"""Same-proposition recall for rule-zero-recall inputs (Q15, A18).

When the deterministic lexical index finds nothing, the LLM may nominate real
corpus cards that assert the SAME proposition in different words. This module
turns those nominations into evidence hits — but with hard gates:

1. Every nominated card_id must exist in the corpus (no invented citations).
2. The stance is read from the STORED card, never from the AI. The AI only says
   which cards are about the same proposition and how relevant they are.
3. The three-state adjudicator still owns the verdict. A recalled card is just
   a normal evidence hit; it goes through the same citation gate and polarity
   handling as a lexically retrieved card.

So removing the AI removes this recall path, but the AI can never author a
stance, a citation or a verdict on its own.
"""
from . import llm
from .evidence import build_index  # ensures corpus shape is the canonical one

MIN_RELEVANCE = 0.85
MAX_RECALL = 5
RECALL_SCORE = 2.0  # a same-proposition card is direct evidence, above MIN_SCORE


def recall(claim, corpus, enabled=True):
    """Return (hits, trace). Hits are [] whenever recall must not fire.

    Recall fires only when enabled, a key is present, and the caller has already
    established that deterministic retrieval returned zero hits.
    """
    if not enabled:
        return [], _trace(claim, "skipped", [], "AI recall disabled by caller.")
    if not llm.available():
        return [], _trace(claim, "degraded", [], "No LLM key; same-proposition recall unavailable.")

    cards = [{"card_id": c["card_id"], "claim": c.get("claim", "")}
             for c in corpus["evidence_cards"]]
    noms, err = llm.semantic_recall(claim, cards, min_relevance=MIN_RELEVANCE)
    if err:
        return [], _trace(claim, "degraded", [], "Semantic recall failed: %s; refusal retained." % err)
    if not noms:
        return [], _trace(claim, "no_match", [],
                          "AI found no card asserting the same proposition; the tool refuses.")

    hits, admitted = _build_from_nominations(noms, corpus)

    detail = ("AI recalled %d real card(s) asserting the same proposition; "
              "stance read from each stored card, verdict still owned by the deterministic gate." % len(admitted))
    return hits, _trace(claim, "llm", admitted, detail, reranked=True)


def _build_from_nominations(noms, corpus):
    """Pure gate: AI nominations -> real evidence hits. Single source of truth
    shared by the production recall path and gate A18, so the audit exercises
    exactly the code that runs in production.

    Ignores any `stance` key the AI may have supplied: stance is ALWAYS read
    from the stored card. Drops ids not in the corpus and low relevance.
    """
    by_id = {c["card_id"]: c for c in corpus["evidence_cards"]}
    hits, admitted = [], []
    for n in noms[:MAX_RECALL]:
        cid = str(n.get("card_id", ""))
        card = by_id.get(cid)
        if not card:  # invented id -> never a citation
            continue
        try:
            rel = float(n.get("relevance", 0.0))
        except (TypeError, ValueError):
            continue
        if rel < MIN_RELEVANCE:
            continue
        hits.append(_hit(card, rel))
        admitted.append({"card_id": card["card_id"], "stance": card["stance"],
                         "relevance": rel})
    return hits, admitted


def _hit(card, relevance):
    """Build a normal evidence hit; stance comes only from the stored card."""
    citation = {
        "card_id": card["card_id"],
        "source_id": card["source_id"],
        "source_name": card["source_name"],
        "url": card["url"],
        "snippet": card["snippet"],
        "stance": card["stance"],  # THE card's own stance; AI never supplies one
    }
    return {
        "score": RECALL_SCORE,
        "anchor_coverage": 1.0,
        "stance_weight": card.get("stance_weight", 1.0),
        "card": card,
        "citation": citation,
        "claim_in_lib": card.get("claim", ""),
        "relevance": relevance,
        "origin": "semantic_recall",
    }


def _trace(claim, method, admitted, detail, reranked=False):
    return {
        "step": "recall",
        "input": claim,
        "method": "ai-same-proposition+" + method,
        "output": method if not admitted else ",".join(a["card_id"] for a in admitted),
        "detail": detail,
        "admitted": admitted,
        "reranked": reranked,
    }
