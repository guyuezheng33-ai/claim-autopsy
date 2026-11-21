"""Orchestration: seven-step pipeline with a full audit trail.

analyze(text, use_llm) -> result dict
- decompose: LLM first when available, deterministic rule fallback (degraded label)
- negation: detect polarity, build an affirmative retrieval query
- retrieve / adjudicate: local deterministic core; the LLM never owns the verdict
- recall: on rule-zero-recall, AI nominates real same-proposition cards; stance stays on the card
- semantic: optional relevance scoring re-ranks retrieved candidates (see task v4-AI)
- wording: optional LLM phrasing, never a verdict change
- every step is traced; an unavailable LLM never breaks the main flow
"""
import datetime
import hashlib
import json
import uuid

from . import llm, semantic, recall, language, prompt, consistency, plan
from .decompose import rule_split
from .evidence import load_corpus, retrieve
from .negation import detect as detect_negation
from .snapshots import get as snapshot_for
from .adjudicate import adjudicate

VERDICT_LABEL = {
    "supported": "Evidence supports",
    "refuted": "Evidence refutes",
    "undetermined": "Insufficient evidence / cannot decide",
}


def _run_id(text):
    seed = text + datetime.datetime.now(datetime.timezone.utc).isoformat() + uuid.uuid4().hex
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _compose_explanation(v):
    """Template-based wording, so it cannot invent anything."""
    citations = v.get("citations", [])
    src = ", ".join(c["source_id"] for c in citations[:3]) if citations else "none"
    if v["verdict"] == "undetermined":
        # The coverage block on the page already names what is missing, so the
        # one-line explanation does not repeat it; the `missing` field stays in
        # the JSON for anything that wants it programmatically.
        return v["reason"] + " (Sources checked: %s)" % src
    return v["reason"] + " (Based on: %s; open the evidence card to verify the original)" % src


def _gate_result(text, kind, use_llm, corpus, trace=None):
    """Explicit refusal for input the rules cannot read at all.

    Zero claims used to be indistinguishable from "no evidence found". This
    state says why nothing was checked and never looks like a verdict.
    """
    notice = language.notice(kind)
    return {
        "run_id": _run_id(text),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "input": text,
        "mode": llm.mode_label() if use_llm else "offline deterministic core (forced)",
        "degraded": [],
        "unsupported_input": notice,
        "summary": {"claims": 0, "supported": 0, "refuted": 0, "undetermined": 0},
        "verdicts": [],
        "trace": list(trace or []) + [language.trace(kind, text)],
        "disclaimer": corpus["meta"]["notice"],
    }


def analyze(text, use_llm=True):
    corpus = load_corpus()

    # 0. Script gate: the corpus and rules are English. Anything else is
    # refused explicitly instead of silently producing zero claims.
    kind = language.classify(text)
    if kind in ("empty", "cjk", "non_latin"):
        return _gate_result(text, kind, use_llm, corpus)
    if prompt.over_limit(text):
        return _gate_result(text, "too_long", use_llm, corpus)

    trace = []
    degraded = []
    claims = []
    decompose_method = "rule"

    # 1. Decompose
    if use_llm and llm.available():
        llm_claims, err = llm.split_claims(text)
        if err is None and llm_claims:
            claims = llm_claims
            decompose_method = "llm"
        else:
            degraded.append("llm_split_failed:" + str(err))
    if not claims:
        claims = rule_split(text)
    trace.append({
        "step": "decompose",
        "input": text,
        "method": decompose_method,
        "output": claims,
        "detail": ("LLM structured decomposition" if decompose_method == "llm" else
                   "Split on sentence and list punctuation plus connectors; questions and subjective fragments are filtered."),
    })
    if not claims:
        return _gate_result(text, "no_claim", use_llm, corpus, trace)

    # 2-6. Per claim: polarity -> retrieve -> semantic -> adjudicate -> gates
    verdicts = []
    for claim in claims:
        neg = detect_negation(claim)
        trace.append({
            "step": "negation",
            "input": claim,
            "method": "marker-detection",
            "output": {"flip": neg["flip"], "uncertain": neg["uncertain"],
                       "markers": neg["markers"], "normalized": neg["normalized"]},
            "detail": "Negation markers are stripped for retrieval; a single marker inverts evidence stance. Double negation refuses.",
        })

        query = neg["normalized"]
        # With AI active, fetch a wider candidate set so semantic relevance can
        # re-rank it. Without a key, keep the deterministic Top-3 path.
        ai_active = use_llm and llm.available()
        hits, t_retrieve = retrieve(query, corpus=corpus, top_k=(5 if ai_active else 3))

        # AI job 1 (fallback): lexical retrieval found nothing. Let the AI nominate
        # real corpus cards asserting the same proposition. Stance stays on the card.
        t_recall = None
        recalled = False
        if ai_active and not hits:
            hits, t_recall = recall.recall(claim, corpus, enabled=True)
            recalled = bool(hits)

        # On the recall path the semantic judge has nothing to re-rank (the recall
        # already carried relevance); keep a clean, explicit trace instead.
        if recalled:
            sem = None
            t_sem = {
                "step": "semantic", "input": claim, "method": "superseded-by-recall",
                "output": "n/a", "detail": "Semantic relevance was applied during same-proposition recall; no second scoring pass.",
                "reranked": False,
            }
        else:
            sem, t_sem = semantic.judge(claim, hits, enabled=use_llm)

        # The ONE measurable AI job: re-rank candidates by semantic relevance.
        # It cannot add a card, change a stance label or create a verdict.
        rel = semantic.relevance_map(sem)
        if recalled:
            t_sem["reranked"] = False  # recall already ranked; do not rescale
        elif rel:
            for h in hits:
                cid = h["citation"]["card_id"]
                h["score"] = round(h["score"] * (0.5 + rel.get(cid, 0.5)), 4)
            hits.sort(key=lambda x: -x["score"])
            hits = hits[:3]
            t_sem["reranked"] = True
            t_sem["output"] = "reranked by AI relevance"
            t_sem["detail"] += " Candidates re-ranked by semantic relevance; final three-state verdict remains gated by citations."
        else:
            t_sem["reranked"] = False

        v, t_adj = adjudicate(claim, hits, semantic=sem, negation=neg)
        # Attach the archived-paragraph status to every citation. It never changes
        # the verdict: it tells the reader whether the card's source could be
        # re-verified offline, and what the page looks like now if it could not.
        for c in v.get("citations", []):
            c["snapshot"] = snapshot_for(c["card_id"])
        # Why a refusal happened, in falsifiable terms: which card came close and
        # which guard stopped it. Carried on the verdict so the page can explain
        # a refusal instead of shrugging at it.
        near = t_retrieve.get("near_miss", []) if v["verdict"] == "undetermined" else []
        if near and not v["citations"]:
            labels = {"topic_only": "only a topic label, not the assertion",
        "thin_anchor": "one shared word, not the assertion",
              "different_population": "a different population",
                      "different_relation": "a different relation",
                      "no_shared_topic": "no shared subject",
                      "missing_required_topic": "a missing required topic",
                      "different_quantity": "a different quantity",
                      "different_object": "a different condition",
                      "different_outcome": "a different endpoint (risk, cure, prevention)",
                      "different_subject": "a different subject",
                      "different_strength": "a different claim strength",
                      "excluded_by_scope": "an excluded scope"}
            guards = sorted(labels.get(r, r) for r in {r for x in near for r in x["reasons"]})
            v["reason"] = ("A card that shares the claim's words was excluded by a scope guard (%s); "
                           "the claim cannot be decided." % ", ".join(guards))
        # A refusal has to say where the corpus ends and what would end it, or it
        # is indistinguishable from a broken tool. Neither field can touch the
        # verdict: one describes the corpus's subjects, the other the evidence
        # that is missing.
        near = plan.enrich_near(corpus, near)
        v["near_miss"] = near
        v["scope"] = plan.scope_of(claim, corpus)
        v["plan"] = plan.plan_for(claim, near, v["scope"]) if v["verdict"] == "undetermined" else None

        if use_llm and llm.available() and v["verdict"] != "undetermined" and hits:
            snippets = [h["citation"]["snippet"] for h in hits[:3]]
            organized, err = llm.organize(VERDICT_LABEL[v["verdict"]], snippets)
            if err is None and organized:
                v["explanation"] = organized
            else:
                degraded.append("llm_organize_failed:" + str(err))
                v["explanation"] = _compose_explanation(v)
        else:
            v["explanation"] = _compose_explanation(v)

        v["verdict_label"] = VERDICT_LABEL[v["verdict"]]
        if recalled:
            v["origin"] = "semantic_recall"
        trace.append(t_retrieve)
        if t_recall:
            trace.append(t_recall)
        trace.append(t_sem)
        trace.append(t_adj)
        verdicts.append(v)

    # 7. Assemble
    result = {
        "run_id": _run_id(text),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "input": text,
        "mode": llm.mode_label() if use_llm else "offline deterministic core (forced)",
        "degraded": degraded,
        "summary": {
            "claims": len(verdicts),
            "supported": sum(1 for v in verdicts if v["verdict"] == "supported"),
            "refuted": sum(1 for v in verdicts if v["verdict"] == "refuted"),
            "undetermined": sum(1 for v in verdicts if v["verdict"] == "undetermined"),
        },
        "verdicts": verdicts,
        "relations": consistency.relations([v["claim"] for v in verdicts]),
        "chains": consistency.chains([v["claim"] for v in verdicts]),
        "trace": trace,
        "disclaimer": corpus["meta"]["notice"],
    }
    return result


def demo_inputs():
    return load_corpus()["demo_inputs"]


BATCH_LIMIT = 50


def analyze_many(texts, use_llm=False, limit=BATCH_LIMIT):
    """Batch entry: one row per submitted text, verdicts unchanged.

    A batch is a list of independent submissions, not a document: each text is
    run through the same `analyze` call and nothing is shared between them. That
    is why the table can be checked against the single-claim path row by row —
    gate A42 does exactly that, including a tampered batch.
    """
    raw = [t.strip() for t in (texts or []) if isinstance(t, str) and t.strip()]
    kept = raw[:limit]
    items = []
    counts = {"supported": 0, "refuted": 0, "undetermined": 0, "mixed": 0, "not_checkable": 0}
    for text in kept:
        r = analyze(text, use_llm=use_llm)
        overall = plan.overall_verdict(r["summary"])
        counts[overall] = counts.get(overall, 0) + 1
        sources = sorted({c["source_id"] for v in r["verdicts"] for c in (v.get("citations") or [])})
        first = r["verdicts"][0]["reason"] if r["verdicts"] else \
            (r.get("unsupported_input") or {}).get("title", "")
        items.append({
            "input": text,
            "claims": r["summary"]["claims"],
            "supported": r["summary"]["supported"],
            "refuted": r["summary"]["refuted"],
            "undetermined": r["summary"]["undetermined"],
            "verdict": overall,
            "sources": sources,
            "reason": first,
            "run_id": r["run_id"],
        })
    return {
        "n": len(items),
        "dropped": max(0, len(raw) - len(kept)),
        "limit": limit,
        "mode": llm.mode_label() if use_llm else "offline deterministic core (forced)",
        "counts": counts,
        "items": items,
    }


if __name__ == "__main__":
    import sys
    text = " ".join(sys.argv[1:]) or "Getting a flu vaccine gives you the flu, and antibiotics can treat a common cold."
    print(json.dumps(analyze(text, use_llm=False), ensure_ascii=False, indent=2))
