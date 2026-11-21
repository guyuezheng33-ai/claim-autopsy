"""Citation audit: check a claim against the source the user provides.

Why this exists
---------------
The corpus mode answers "does our 112-card corpus decide this claim?", and on
open-domain claims the honest answer is usually no. That is a coverage limit the
product cannot hide. Citation audit changes the question to the one a reader
actually asks: "does the document I am citing actually say this?"

Every atom gets a finding. `not_in_source` is a finding, not a refusal: it
means the provided text does not state the claim, and the closest sentence is
shown so the reader can see why. That makes output coverage 100% by
construction, because the evidence is supplied with the input.

Verdicts are still deterministic and still gated: a verdict requires a
near-verbatim sentence from the same source, the same relation, a compatible
subject, quantity and strength. A paraphrased source that shares the topic but
not the proposition is reported as `not_in_source`, never guessed.
"""
import datetime
import hashlib
import math
import re

from .decompose import rule_split
from .evidence import (
    STOP_WORDS, _normalize, _tokens, primary_relation, quantity_compatible,
    strength_compatible, subject_compatible,
)
from .negation import detect as detect_negation

# A verdict needs most of the claim's content words in one sentence. Partial
# matches are reported as `not_in_source` with the closest sentence attached.
FULL_MATCH = 0.70
PARTIAL_MATCH = 0.35

MAX_SOURCE_CHARS = 20000
MAX_CLAIM_CHARS = 2000

ABBREV = {"dr", "mr", "mrs", "ms", "prof", "st", "vs", "e.g", "i.e", "etc",
          "fig", "no", "approx", "cf", "al", "inc", "ltd", "u.s", "u.k"}

_SENT_END = re.compile(r"[.!?]")


def _split_sentences(text):
    """Sentence spans with character offsets, without breaking decimals or Dr.

    Offsets matter: the page quotes the exact span, so a reader can find it in
    their own document. A missing sentence is worse than a coarse one.
    """
    out = []
    start = 0
    n = len(text)
    for m in _SENT_END.finditer(text):
        i = m.end()
        # A decimal point or an abbreviation is not a sentence end.
        if text[m.start()] == ".":
            prev = text[max(0, m.start() - 12):m.start()].split()
            if prev and prev[-1].lower().strip("(") in ABBREV:
                continue
            if i < n and text[i].isdigit():
                continue
        # Consume closing quotes/brackets and trailing spaces.
        while i < n and text[i] in "\"')]”’":
            i += 1
        if i < n and not text[i].isspace():
            continue
        seg = text[start:i].strip()
        if seg:
            lead = len(text[start:i]) - len(text[start:i].lstrip())
            out.append({"text": seg, "start": start + lead, "end": start + lead + len(seg)})
        start = i
    tail = text[start:].strip()
    if tail:
        lead = len(text[start:]) - len(text[start:].lstrip())
        out.append({"text": tail, "start": start + lead,
                    "end": start + lead + len(tail)})
    return out


def _content(text):
    return [w for w in _tokens(text) if w not in STOP_WORDS and len(w) > 1]


def _weighted_coverage(claim_tokens, sent_tokens, idf):
    """IDF-weighted share of the claim's content words present in a sentence.

    Rare words dominate on purpose: a sentence that shares "study" and "people"
    but not the intervention has not restated the claim. The denominator is the
    claim, not the sentence, so a long paragraph can still match a short claim.
    """
    if not claim_tokens:
        return 0.0, []
    have = set(sent_tokens)
    total = sum(max(idf.get(w, 1.0), 0.5) for w in claim_tokens)
    if total <= 0:
        return 0.0, []
    hit = [w for w in claim_tokens if w in have]
    got = sum(max(idf.get(w, 1.0), 0.5) for w in set(hit))
    return got / total, sorted(set(hit))


def _index(sentences):
    df = {}
    for s in sentences:
        for w in set(s["tokens"]):
            df[w] = df.get(w, 0) + 1
    n = max(1, len(sentences))
    idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}
    return idf


def _relation_ok(claim, sentence):
    a, b = primary_relation(claim), primary_relation(sentence)
    if a and b and a != b:
        # "prevents" and "cures" are not the same assertion even when every
        # other word matches. The source may still be relevant, but it does not
        # state this claim.
        return False, "the source asserts a different relation (%s, not %s)" % (b, a)
    return True, ""


def _is_negated(text):
    return bool(detect_negation(text)["flip"])


def _numbers(text):
    return {m.group(0).replace(",", "") for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", text or "")}


def _finding(claim, verdict, reason, sentence=None, cov=0.0, near=None):
    rec = {
        "claim": claim,
        "verdict": verdict,
        "confidence": "high" if verdict != "not_in_source" and cov >= 0.85 else
                      ("medium" if verdict != "not_in_source" else "none"),
        "coverage": round(cov, 4),
        "reason": reason,
        "source_sentence": sentence["text"] if sentence else None,
        "char_offset": [sentence["start"], sentence["end"]] if sentence else None,
        "near": near or [],
    }
    return rec


def audit(claim_text, source_text, source_name="provided source"):
    """Return a citation audit for every atom of `claim_text`.

    Never raises on ordinary input: an empty source or a source with no
    sentences is an explicit error result, not a crash.
    """
    claim_text = (claim_text or "").strip()
    source_text = (source_text or "").strip()
    source_name = (source_name or "provided source").strip() or "provided source"

    if not claim_text:
        return {"error": "empty_claim"}
    if not source_text:
        return {"error": "empty_source"}
    if len(claim_text) > MAX_CLAIM_CHARS:
        return {"error": "claim_too_long", "limit": MAX_CLAIM_CHARS}
    if len(source_text) > MAX_SOURCE_CHARS:
        return {"error": "source_too_long", "limit": MAX_SOURCE_CHARS}

    atoms = rule_split(claim_text) or [claim_text]
    sentences = _split_sentences(source_text)
    for s in sentences:
        s["tokens"] = _tokens(s["text"])
    idf = _index(sentences)

    findings = []
    for atom in atoms:
        ctoks = _content(atom)
        scored = []
        for s in sentences:
            cov, hit = _weighted_coverage(ctoks, s["tokens"], idf)
            scored.append((cov, hit, s))
        scored.sort(key=lambda x: -x[0])
        top_cov, top_hit, top = scored[0]
        near = [{"text": s["text"], "coverage": round(c, 3), "hit": h}
                for c, h, s in scored[1:4] if c > 0]

        if top_cov < PARTIAL_MATCH:
            findings.append(_finding(
                atom, "not_in_source",
                "The provided source does not mention this claim. Only %.0f%% of its "
                "content words appear in the closest sentence." % (top_cov * 100),
                None, top_cov, near))
            continue

        rel_ok, rel_reason = _relation_ok(atom, top["text"])
        if not rel_ok:
            findings.append(_finding(
                atom, "not_in_source", "The closest sentence shares the topic but %s." % rel_reason,
                top, top_cov, near))
            continue
        if not subject_compatible(atom, top["text"]):
            findings.append(_finding(
                atom, "not_in_source", "The closest sentence is about a different subject.",
                top, top_cov, near))
            continue
        if not quantity_compatible(atom, top["text"]):
            findings.append(_finding(
                atom, "not_in_source", "The source states a different quantity.",
                top, top_cov, near))
            continue
        missing_numbers = _numbers(atom) - _numbers(top["text"])
        if missing_numbers:
            findings.append(_finding(
                atom, "not_in_source", "The source does not state the number(s) in the claim (%s)."
                % ", ".join(sorted(missing_numbers)), top, top_cov, near))
            continue
        if not strength_compatible(atom, top["text"]):
            findings.append(_finding(
                atom, "not_in_source", "The source states a different strength (hedged vs absolute).",
                top, top_cov, near))
            continue

        if top_cov < FULL_MATCH:
            findings.append(_finding(
                atom, "not_in_source",
                "The source comes close (%.0f%% of the claim's content words) but does not "
                "state it as written; no verdict is transferred from a partial match."
                % (top_cov * 100), top, top_cov, near))
            continue

        # Polarity decides the direction once the proposition is matched. A
        # source sentence that negates the same proposition refutes the claim;
        # the same polarity supports it. Double negation is left to the reader.
        claim_neg = detect_negation(atom)
        sent_neg = _is_negated(top["text"])
        if claim_neg.get("uncertain"):
            findings.append(_finding(
                atom, "not_in_source",
                "The claim contains ambiguous double negation; the source is quoted but "
                "no direction is assigned.", top, top_cov, near))
            continue
        if claim_neg["flip"] != sent_neg:
            findings.append(_finding(
                atom, "refuted",
                "The source states the same proposition with the opposite polarity.",
                top, top_cov, near))
        else:
            findings.append(_finding(
                atom, "supported",
                "The source states this proposition directly.",
                top, top_cov, near))

    src_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    summary = {
        "claims": len(findings),
        "supported": sum(1 for f in findings if f["verdict"] == "supported"),
        "refuted": sum(1 for f in findings if f["verdict"] == "refuted"),
        "not_in_source": sum(1 for f in findings if f["verdict"] == "not_in_source"),
        "adjudicated": len(findings),
    }
    return {
        "mode": "citation",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "input": claim_text,
        "source": {
            "name": source_name,
            "sha256": src_hash,
            "chars": len(source_text),
            "sentences": len(sentences),
        },
        "summary": summary,
        "verdicts": findings,
        "disclaimer": ("Every atom gets a finding. not_in_source means the provided text "
                       "does not state the claim; it is a result, not a refusal."),
    }
