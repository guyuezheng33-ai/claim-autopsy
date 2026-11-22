"""Claim court: AI advocates argue, a deterministic judge verifies.

The product question is narrow and checkable: does the source the user supplied
actually state this claim? The court does not decide truth. It decides whether a
quoted sentence, taken in context, supports or contradicts an atomic claim.

Why a court rather than a classifier
------------------------------------
A model is good at proposing paraphrases and counter-arguments, and bad at being
trusted with the verdict. So the model is cast as prosecution and defence: it
may only submit an argument together with an exact quotation from the evidence
packet. The judge then checks six things a fabricated or overstated argument
cannot fake: the quote exists, the relation is the same, the subject and
population are the same, the quantity is the same, the strength is the same, and
the polarity points the way the advocate says it does. Any failure is `struck`,
with a reason code, and the argument cannot enter the verdict.

Without a model the court still runs. The rules-only docket proposes the same
kind of argument from lexical coverage and the same judge accepts or strikes it.
That keeps output coverage at 100% by construction: every atom gets a finding
about the supplied source, including `not_in_source`.
"""
import datetime
import hashlib
import json
import os
import re

from . import citation, language
from .decompose import rule_split
from .evidence import (
    NEG_WORDS, object_compatible, population_compatible, predicate_classes, predicate_compatible,
    quantity_compatible, relation_classes, strength_compatible, subject_compatible,
)
from .negation import detect as detect_negation

MAX_ATOMS = 8
MAX_ARGS_PER_SIDE = 3
MIN_QUOTE_CHARS = 12
MIN_QUOTE_WORDS = 3
MAX_SOURCE_CHARS = 20000
MAX_CLAIM_CHARS = 2000
MAX_ANCHORS = 5
MIN_ANCHOR_CHARS = 2

SIDE_PROSECUTION = "prosecution"
SIDE_DEFENSE = "defense"
VALID_SIDES = (SIDE_PROSECUTION, SIDE_DEFENSE)

STRIKE_LABELS = {
    "unknown_evidence": "evidence id is not in the packet",
    "quote_not_found": "quotation does not appear in the cited evidence",
    "quote_too_short": "quotation is too short to establish a proposition",
    "low_coverage": "quotation shares too little of the claim's content",
    "relation_mismatch": "quotation asserts a different relation",
    "subject_mismatch": "quotation is about a different subject",
    "population_mismatch": "quotation is about a different population",
    "object_mismatch": "quotation is about a different condition",
    "endpoint_mismatch": "quotation answers a different endpoint",
    "quantity_mismatch": "quotation states a different quantity",
    "number_missing": "quotation does not state the claim's number",
    "strength_mismatch": "quotation states a different strength",
    "polarity_ambiguous": "quotation or claim has ambiguous double negation",
    "side_mismatch": "quotation points the other way",
    "empty_argument": "argument has no usable quotation",
    "anchor_not_grounded": "an anchor term does not appear in the claim or the quotation",
    "anchor_forbidden": "an anchor tries to replace negation, a relation verb or a number",
    "anchor_no_effect": "the bridge does not make the quotation state the claim",
}

_WHITESPACE = re.compile(r"\s+")
_QUOTE_MAP = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u00a0": " ",
})


def _canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(obj):
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def _sha_text(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _norm_quote(text):
    s = (text or "").translate(_QUOTE_MAP)
    s = _WHITESPACE.sub(" ", s).strip()
    return s


def _quote_in(quote, evidence_text):
    """Exact or whitespace-normalised containment; never fuzzy."""
    if not quote or not evidence_text:
        return False, None
    if quote in evidence_text:
        return True, quote
    nq, ne = _norm_quote(quote), _norm_quote(evidence_text)
    if nq and nq in ne:
        # Recover the original span so the receipt can quote the source, not the
        # model's re-spacing of it.
        idx = ne.find(nq)
        return True, ne[idx:idx + len(nq)]
    return False, None


def _word_count(text):
    return len(re.findall(r"[A-Za-z0-9%]+", text or ""))


def _term_in(term, text):
    """Whole-token containment, case and spacing normalised."""
    term = _norm_quote(term).lower()
    text = _norm_quote(text).lower()
    if not term:
        return False
    return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) is not None


def _anchor_forbidden(term):
    tokens = set(re.findall(r"[a-z0-9]+", _norm_quote(term).lower()))
    return (bool(tokens & NEG_WORDS)
            or bool(relation_classes(term))
            or bool(re.search(r"\d", term or ""))
            or len(_norm_quote(term)) < MIN_ANCHOR_CHARS)


def _bridge_claim(atom, quote, anchors):
    """Apply a model-supplied, auditable term bridge to the claim.

    The model may map a claim term to the source's term ("aspirin" ->
    "acetylsalicylic acid"). The judge checks that both terms are actually
    present, forbids anchors that touch negation/relations/numbers, then reruns
    every structural check on the bridged claim. A bridge cannot lower the
    lexical bar; it changes the vocabulary the judge reads.
    """
    if not isinstance(anchors, list) or not anchors:
        return atom, [], "anchor_not_grounded"
    if len(anchors) > MAX_ANCHORS:
        return atom, [], "anchor_forbidden"
    bridged = atom
    used = []
    for pair in anchors:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            return atom, [], "anchor_not_grounded"
        claim_term = _norm_quote(str(pair[0]))
        source_term = _norm_quote(str(pair[1]))
        if not _term_in(claim_term, atom) or not _term_in(source_term, quote):
            return atom, [], "anchor_not_grounded"
        if _anchor_forbidden(claim_term) or _anchor_forbidden(source_term):
            return atom, [], "anchor_forbidden"
        pattern = r"(?<![a-z0-9])" + re.escape(claim_term) + r"(?![a-z0-9])"
        bridged = re.sub(pattern, source_term, bridged, count=1, flags=re.IGNORECASE)
        used.append([claim_term, source_term])
    if not used or _norm_quote(bridged).lower() == _norm_quote(atom).lower():
        return atom, [], "anchor_no_effect"
    return bridged, used, None


def build_evidence(source_text, source_name="provided source"):
    """Split the source into sentence-level evidence with offsets and hashes."""
    text = citation.prompt_safe_source(source_text) if hasattr(citation, "prompt_safe_source") else (source_text or "")
    sentences = citation._split_sentences(text)
    doc_hash = _sha_text(text)
    items = []
    for i, s in enumerate(sentences):
        quote = s["text"]
        items.append({
            "evidence_id": "S1-P%d" % (i + 1),
            "source_id": "S1",
            "source_name": source_name,
            "paragraph": i + 1,
            "char_start": s["start"],
            "char_end": s["end"],
            "quote": quote,
            "quote_sha256": _sha_text(quote),
            "doc_sha256": doc_hash,
        })
    return {
        "source": {
            "source_id": "S1",
            "name": source_name,
            "sha256": doc_hash,
            "chars": len(text),
            "sentences": len(items),
        },
        "sentences": items,
        "text": text,
        "idf": citation._index([{**s, "tokens": citation._tokens(s["text"])} for s in sentences]),
    }


def _claim_text(text):
    """Normalise contractions that otherwise become phantom content words."""
    s = (text or "").lower()
    s = s.replace("cannot", "can not").replace("can't", "can not")
    s = re.sub(r"\bgetting\b", "get", s)
    s = re.sub(r"\bgives\b", "give", s)
    return s


def _claim_content(text):
    return list(dict.fromkeys(citation._content(_claim_text(text))))


def _coverage(atom, quote, idf):
    return citation._weighted_coverage(
        _claim_content(atom), citation._tokens(quote), idf)


def judge_quote(atom, quote, idf):
    """Run the six checks. Return a receipt, never a verdict by itself."""
    checks = {
        "quote_exact": True,
        "relation": True,
        "subject": True,
        "population": True,
        "object": True,
        "endpoint": True,
        "quantity": True,
        "strength": True,
        "polarity": True,
    }
    codes = []
    cov, _ = _coverage(atom, quote, idf)

    rel_ok, _ = citation._relation_ok(atom, quote)
    if not rel_ok:
        checks["relation"] = False
        codes.append("relation_mismatch")
    if not subject_compatible(atom, quote):
        checks["subject"] = False
        codes.append("subject_mismatch")
    if not population_compatible(atom, quote):
        checks["population"] = False
        codes.append("population_mismatch")
    if not object_compatible(atom, quote):
        checks["object"] = False
        codes.append("object_mismatch")
    if not predicate_compatible(atom, quote):
        checks["endpoint"] = False
        codes.append("endpoint_mismatch")
    if not quantity_compatible(atom, quote):
        checks["quantity"] = False
        codes.append("quantity_mismatch")
    missing = citation._numbers(atom) - citation._numbers(quote)
    if missing:
        checks["quantity"] = False
        codes.append("number_missing")
    if not strength_compatible(atom, quote):
        checks["strength"] = False
        codes.append("strength_mismatch")
    claim_neg = detect_negation(atom)
    if claim_neg.get("uncertain"):
        checks["polarity"] = False
        codes.append("polarity_ambiguous")
    quote_neg = citation._is_negated(quote)
    direction = None
    if checks["polarity"] and not claim_neg.get("uncertain"):
        direction = "contradicts" if claim_neg["flip"] != quote_neg else "supports"

    structural_ok = all(checks[k] for k in (
        "relation", "subject", "population", "object", "endpoint",
        "quantity", "strength", "polarity"))
    same_predicate = bool(predicate_classes(atom) & predicate_classes(quote))
    # A predicate synonym (cure/treat) can push lexical coverage just below the
    # strict threshold while every structural check agrees and both sentences
    # sit in the same predicate class. Only that narrow case gets the partial
    # floor; an unrelated colour or object ("green" vs "blue") still strikes.
    if cov < citation.FULL_MATCH:
        if not (structural_ok and same_predicate and cov >= citation.PARTIAL_MATCH):
            codes.append("low_coverage")

    return {
        "ok": not codes,
        "coverage": round(cov, 4),
        "checks": checks,
        "strike_codes": sorted(set(codes)),
        "direction": direction,
        "reason": STRIKE_LABELS.get(codes[0], "quotation does not establish the claim") if codes else (
            "The quotation states the same proposition with %s polarity." %
            ("the same" if direction == "supports" else "the opposite")),
    }


def _argument(side, atom_id, evidence, quote, rationale, judge, requested_side=None,
              origin="rule"):
    status = "accepted" if judge["ok"] and (requested_side is None or
                                            (side == SIDE_PROSECUTION and judge["direction"] == "contradicts") or
                                            (side == SIDE_DEFENSE and judge["direction"] == "supports")) else "struck"
    codes = list(judge["strike_codes"])
    if judge["ok"] and status == "struck":
        codes.append("side_mismatch")
    return {
        "argument_id": "%s-%s-%s-%s" % (
            side[:1].upper(), atom_id, evidence["evidence_id"], _sha_text(quote)[:6]),
        "side": side,
        "origin": origin,
        "atom_id": atom_id,
        "relation": "contradicts" if judge["direction"] == "contradicts" else "supports",
        "evidence_id": evidence["evidence_id"],
        "source_name": evidence["source_name"],
        "quote": quote,
        "quote_sha256": _sha_text(quote),
        "char_start": evidence["char_start"],
        "char_end": evidence["char_end"],
        "rationale": rationale[:240],
        "status": status,
        "strike_codes": codes,
        "strike_reason": STRIKE_LABELS.get(codes[0], "") if codes else None,
        "checks": judge["checks"],
        "coverage": judge["coverage"],
        "bridge": judge.get("bridge"),
    }


def verify_ai_argument(atom, atom_id, arg, packet, expected_side):
    """Validate one model argument. Any doubt is a strike, never a verdict."""
    if not isinstance(arg, dict):
        return None
    evidence_id = str(arg.get("evidence_id", "")).strip()
    quote = str(arg.get("quote", "")).strip()
    rationale = str(arg.get("rationale", "")).strip()
    by_id = {e["evidence_id"]: e for e in packet["sentences"]}
    evidence = by_id.get(evidence_id)
    if not evidence:
        return {
            "argument_id": "%s-%s-unknown" % (expected_side[:1].upper(), atom_id),
            "side": expected_side, "origin": "ai", "atom_id": atom_id, "relation": "unknown",
            "evidence_id": evidence_id, "quote": quote,
            "char_start": 0, "char_end": 0,
            "status": "struck", "strike_codes": ["unknown_evidence"],
            "strike_reason": STRIKE_LABELS["unknown_evidence"], "checks": {},
            "coverage": 0.0, "rationale": rationale[:240],
        }
    exact, recovered = _quote_in(quote, evidence["quote"])
    if not exact:
        return {
            "argument_id": "%s-%s-%s" % (expected_side[:1].upper(), atom_id, evidence_id),
            "side": expected_side, "origin": "ai", "atom_id": atom_id, "relation": "unknown",
            "evidence_id": evidence_id, "quote": quote,
            "char_start": evidence["char_start"], "char_end": evidence["char_end"],
            "status": "struck", "strike_codes": ["quote_not_found"],
            "strike_reason": STRIKE_LABELS["quote_not_found"], "checks": {"quote_exact": False},
            "coverage": 0.0, "rationale": rationale[:240],
        }
    if len(recovered) < MIN_QUOTE_CHARS or _word_count(recovered) < MIN_QUOTE_WORDS:
        return {
            "argument_id": "%s-%s-%s" % (expected_side[:1].upper(), atom_id, evidence_id),
            "side": expected_side, "origin": "ai", "atom_id": atom_id, "relation": "unknown",
            "evidence_id": evidence_id, "quote": recovered,
            "char_start": evidence["char_start"], "char_end": evidence["char_end"],
            "status": "struck", "strike_codes": ["quote_too_short"],
            "strike_reason": STRIKE_LABELS["quote_too_short"],
            "checks": {"quote_exact": True}, "coverage": 0.0, "rationale": rationale[:240],
        }
    judge = judge_quote(atom, recovered, packet["idf"])
    if not judge["ok"] and arg.get("anchors"):
        bridged, used, bridge_err = _bridge_claim(atom, recovered, arg.get("anchors"))
        if bridge_err:
            judge = {
                "ok": False, "coverage": 0.0, "checks": {}, "direction": None,
                "strike_codes": [bridge_err],
                "reason": STRIKE_LABELS[bridge_err],
            }
        else:
            bridged_judge = judge_quote(bridged, recovered, packet["idf"])
            if bridged_judge["ok"]:
                bridged_judge["bridge"] = {
                    "original_claim": atom,
                    "bridged_claim": bridged,
                    "anchors": used,
                }
                judge = bridged_judge
            else:
                bridged_judge["strike_codes"] = ["anchor_no_effect"] + bridged_judge["strike_codes"]
                bridged_judge["reason"] = STRIKE_LABELS["anchor_no_effect"]
                judge = bridged_judge
    out = _argument(expected_side, atom_id, evidence, recovered, rationale, judge,
                    requested_side=expected_side, origin="ai")
    out["anchors_requested"] = arg.get("anchors") if isinstance(arg.get("anchors"), list) else []
    return out


def _rule_arguments(atom, atom_id, packet):
    """Rules-only docket: propose from coverage, let the same judge decide."""
    args = []
    scored = []
    for e in packet["sentences"]:
        cov, _ = _coverage(atom, e["quote"], packet["idf"])
        scored.append((cov, e))
    scored.sort(key=lambda x: -x[0])
    for cov, e in scored[:4]:
        if cov < citation.PARTIAL_MATCH:
            continue
        judge = judge_quote(atom, e["quote"], packet["idf"])
        if judge["ok"]:
            side = SIDE_DEFENSE if judge["direction"] == "supports" else SIDE_PROSECUTION
            args.append(_argument(side, atom_id, e, e["quote"], judge["reason"], judge,
                                  requested_side=side))
    return args, scored[0] if scored else (0.0, None)


def _verdict(atom, atom_id, args, nearest):
    accepted = [a for a in args if a["status"] == "accepted"]
    sup = [a for a in accepted if a["relation"] == "supports"]
    ref = [a for a in accepted if a["relation"] == "contradicts"]
    struck = [a for a in args if a["status"] == "struck"]
    if sup and ref:
        verdict = "conflict"
        reason = "Verified arguments point both ways; the court does not pick one."
    elif sup:
        verdict = "supported"
        reason = "A verified quotation states the same proposition with the same polarity."
        if any(a.get("bridge") for a in sup):
            reason += " The AI supplied a grounded term bridge; the judge rechecked the bridged claim."
    elif ref:
        verdict = "refuted"
        reason = "A verified quotation states the same proposition with the opposite polarity."
        if any(a.get("bridge") for a in ref):
            reason += " The AI supplied a grounded term bridge; the judge rechecked the bridged claim."
    else:
        verdict = "not_in_source"
        reason = "No verified quotation states this proposition in the supplied source."
    return {
        "atom_id": atom_id,
        "claim": atom,
        "verdict": verdict,
        "reason": reason,
        "accepted_argument_ids": [a["argument_id"] for a in accepted],
        "struck_argument_ids": [a["argument_id"] for a in struck],
        "bridge_argument_ids": [a["argument_id"] for a in accepted if a.get("bridge")],
        "evidence_ids": sorted({a["evidence_id"] for a in accepted}),
        "nearest": ({
            "quote": nearest[1]["quote"],
            "coverage": round(nearest[0], 4),
            "evidence_id": nearest[1]["evidence_id"],
            "char_start": nearest[1]["char_start"],
            "char_end": nearest[1]["char_end"],
        } if nearest and nearest[1] else None),
        "what_would_change_it": (
            "A source sentence asserting the same proposition with the opposite "
            "polarity would change this verdict."
            if verdict == "supported" else
            "A source sentence asserting the same proposition would change this verdict."
            if verdict == "refuted" else
            "A sentence, in this source, that states the same subject, quantity and "
            "strength as the claim would change this result."
        ),
    }


def _input_error(kind, extra=None):
    out = {"error": kind}
    if extra:
        out.update(extra)
    return out


def make_dossier(claim_text, source_text, source_name="provided source",
                 ai_arguments=None, mode="rules", model=None, trace=None):
    """Build the full court record. Never raises on ordinary input."""
    claim_text = (claim_text or "").strip()
    source_text = (source_text or "").strip()
    source_name = (source_name or "provided source").strip() or "provided source"

    if not claim_text:
        return _input_error("empty_claim")
    if not source_text:
        return _input_error("empty_source")
    if len(claim_text) > MAX_CLAIM_CHARS:
        return _input_error("claim_too_long", {"limit": MAX_CLAIM_CHARS})
    if len(source_text) > MAX_SOURCE_CHARS:
        return _input_error("source_too_long", {"limit": MAX_SOURCE_CHARS})
    kind = language.classify(claim_text)
    if kind != "english":
        return _input_error("unsupported_language", {"kind": kind, "notice": language.notice(kind)})
    kind_src = language.classify(source_text)
    if kind_src != "english":
        return _input_error("unsupported_language", {"kind": kind_src, "notice": language.notice(kind_src)})

    atoms = rule_split(claim_text) or [claim_text]
    atoms = atoms[:MAX_ATOMS]
    packet = build_evidence(source_text, source_name)

    arguments = []
    verdicts = []
    for i, atom in enumerate(atoms, 1):
        atom_id = "A%d" % i
        if ai_arguments:
            for side in VALID_SIDES:
                supplied = [a for a in (ai_arguments.get(side) or [])
                            if str(a.get("atom_id", "")) == atom_id][:MAX_ARGS_PER_SIDE]
                for a in supplied:
                    checked = verify_ai_argument(atom, atom_id, a, packet, side)
                    if checked:
                        arguments.append(checked)
        rule_args, nearest = _rule_arguments(atom, atom_id, packet)
        # The rules-only docket is a floor, not a competitor: AI may add
        # arguments, but it cannot erase a lexical argument that the same judge
        # would accept. Duplicates on (side, evidence, quote) are skipped.
        seen = {(a["side"], a["evidence_id"], a["quote"]) for a in arguments
                if a["atom_id"] == atom_id}
        for ra in rule_args:
            key = (ra["side"], ra["evidence_id"], ra["quote"])
            if key not in seen:
                seen.add(key)
                arguments.append(ra)
        atom_args = [a for a in arguments if a["atom_id"] == atom_id]
        verdicts.append(_verdict(atom, atom_id, atom_args, nearest))

    summary = {
        "claims": len(verdicts),
        "supported": sum(1 for v in verdicts if v["verdict"] == "supported"),
        "refuted": sum(1 for v in verdicts if v["verdict"] == "refuted"),
        "not_in_source": sum(1 for v in verdicts if v["verdict"] == "not_in_source"),
        "conflict": sum(1 for v in verdicts if v["verdict"] == "conflict"),
        "accepted_arguments": sum(1 for a in arguments if a["status"] == "accepted"),
        "struck_arguments": sum(1 for a in arguments if a["status"] == "struck"),
        "ai_arguments": sum(1 for a in arguments if a.get("origin") == "ai"),
        "ai_accepted": sum(1 for a in arguments if a.get("origin") == "ai" and a["status"] == "accepted"),
        "ai_struck": sum(1 for a in arguments if a.get("origin") == "ai" and a["status"] == "struck"),
        "ai_bridges": sum(1 for a in arguments if a.get("origin") == "ai"
                          and a["status"] == "accepted" and a.get("bridge")),
        "rule_arguments": sum(1 for a in arguments if a.get("origin") == "rule"),
    }
    generated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    run_id = _hash({
        "claim": claim_text,
        "source_sha256": packet["source"]["sha256"],
        "atoms": atoms,
        "arguments": [
            {k: a.get(k) for k in ("side", "atom_id", "evidence_id", "quote", "status", "strike_codes", "bridge")}
            for a in arguments
        ],
        "mode": mode,
    })[:16]
    return {
        "mode": "court",
        "ai_mode": mode,
        "input": {
            "claim": claim_text,
            "source_name": source_name,
            "source_sha256": packet["source"]["sha256"],
        },
        "source": packet["source"],
        "atoms": verdicts,
        "arguments": arguments,
        "summary": summary,
        "receipt": {
            "run_id": run_id,
            "generated_at": generated_at,
            "model": model or None,
            "engine": "deterministic judge + rules-only docket" if mode == "rules" else "deterministic judge + AI advocates",
        },
        "trace": trace or [],
        "disclaimer": (
            "The court decides whether the supplied source states the claim. "
            "It is not an authoritative fact-check, and `not_in_source` is a "
            "finding about this source, not a claim that the statement is false."
        ),
    }


def fixtures(path=None):
    path = path or os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                "data", "court_cases.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_fixtures(path=None):
    data = fixtures(path)
    results = []
    for case in data["cases"]:
        d = make_dossier(case["claim"], case["source"], case.get("source_name", "fixture source"))
        got = [a["verdict"] for a in d["atoms"]]
        expected = case["expected"] if isinstance(case["expected"], list) else [case["expected"]]
        ok = got == expected
        if case.get("must_cite"):
            ok = ok and any(case["must_cite"] in (arg.get("quote") or "")
                            for arg in d["arguments"] if arg["status"] == "accepted")
        results.append({"id": case["id"], "pass": ok, "expected": expected,
                        "got": got, "run_id": d.get("receipt", {}).get("run_id")})
    arg_results = []
    for case in data.get("argument_cases", []):
        packet = build_evidence(case["source"], "argument fixture")
        atom = case["claim"]
        arg = {"evidence_id": case["evidence_id"], "quote": case["quote"],
               "anchors": case.get("anchors", []),
               "rationale": case.get("rationale", "")}
        checked = verify_ai_argument(atom, "A1", arg, packet, case["side"])
        got = checked["status"] if checked else "missing"
        codes = checked.get("strike_codes") if checked else []
        ok = got == case["expected"]
        if case.get("expected_code"):
            ok = ok and case["expected_code"] in codes
        arg_results.append({"id": case["id"], "pass": ok,
                            "expected": case["expected"], "got": got,
                            "codes": codes})
    input_results = []
    for case in data.get("input_cases", []):
        d = make_dossier(case["claim"], case["source"])
        got = d.get("error") if isinstance(d, dict) else "not_an_error"
        input_results.append({"id": case["id"], "pass": got == case["expected_error"],
                              "expected": case["expected_error"], "got": got})
    anchor_results = []
    for case in data.get("anchor_cases", []):
        bridged, used, err = _bridge_claim(case["claim"], case["quote"], case["anchors"])
        ok = err == case.get("expected_error")
        if ok and case.get("must_contain"):
            ok = case["must_contain"] in bridged
        anchor_results.append({"id": case["id"], "pass": ok,
                               "expected_error": case.get("expected_error"),
                               "got_error": err, "bridged": bridged, "anchors": used})
    passed = (sum(1 for r in results if r["pass"])
              + sum(1 for r in arg_results if r["pass"])
              + sum(1 for r in input_results if r["pass"])
              + sum(1 for r in anchor_results if r["pass"]))
    total = (len(results) + len(arg_results) + len(input_results)
             + len(anchor_results))
    return {"passed": passed, "total": total, "all_pass": passed == total,
            "cases": results, "argument_cases": arg_results,
            "anchor_cases": anchor_results, "input_cases": input_results}


def main(argv=None):
    import argparse
    import sys
    argv = argv or sys.argv[1:]
    ap = argparse.ArgumentParser(
        prog="python -m core.court",
        description="Deterministic citation court: replay fixtures or run the live docket.",
    )
    sub = ap.add_subparsers(dest="command")
    sub.add_parser("fixtures", help="run the frozen fixture docket")
    sub.add_parser("live", help="run the live docket against the local model")
    ap.add_argument("--fixtures", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--live", action="store_true", help=argparse.SUPPRESS)
    ns = ap.parse_args(argv)
    command = ns.command or ("fixtures" if ns.fixtures else "live" if ns.live else "")
    if command == "fixtures":
        out = run_fixtures()
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if out["all_pass"] else 1
    if command == "live":
        from . import court_live
        out = court_live.run()
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if out.get("ok") else 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
