"""Semantic layer: the one job AI owns.

The LLM scores how directly each candidate card addresses the claim. That score
is consumed by the pipeline to re-rank retrieval candidates. It never creates a
citation, never changes a stance label and never produces a verdict on its own.

Every unavailable path is explicit (`skipped`, `degraded`) so a demo without a
key cannot be mistaken for an AI-powered run.
"""
from . import llm


def judge(claim, hits, enabled=True):
    """Return (judgement, trace). Judgement carries per-card relevance."""
    if not enabled:
        return None, _trace(claim, "skipped", [], "LLM disabled by caller (forced offline mode).")
    if not llm.available():
        return None, _trace(claim, "degraded", [], "LLM_API_KEY not set; semantic scoring skipped, deterministic core running.")
    if not hits:
        return None, _trace(claim, "skipped", [], "Zero recall: AI may not judge beyond the evidence.")

    cards = [{"card_id": h["citation"]["card_id"],
              "claim": h.get("claim_in_lib", ""),
              "snippet": h["citation"]["snippet"]} for h in hits]
    out, err = llm.semantic_judge(claim, cards)
    if err:
        return None, _trace(claim, "degraded", cards, "Semantic scoring failed: %s; deterministic core retained." % err)

    return out, _trace(claim, "llm", cards,
        "AI relevance scored %d candidate cards; ranking may change, verdict still owned by the citation gate." % len(out["relevant"]),
        out)


def relevance_map(judgement):
    if not judgement:
        return {}
    return {r["card_id"]: r["relevance"] for r in judgement.get("relevant", [])}


def _trace(claim, method, cards, detail, judgement=None):
    return {
        "step": "semantic",
        "input": claim,
        "method": method,
        "output": (judgement or {}).get("suggestion", method),
        "detail": detail,
        "cards": [c["card_id"] for c in cards],
        "relevance": relevance_map(judgement),
    }
