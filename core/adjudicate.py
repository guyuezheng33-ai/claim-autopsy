"""Three-state adjudicator with gates (Q2, Q8, Q10).

Three states: supported / refuted / undetermined.
Rules:
- Double negation: refuse. We do not guess what the speaker meant.
- Negated claim: evidence stance is inverted before scoring, and each citation
  records both its original and its effective stance.
- Source discrepancy group: refuse and show both sides, no adjudication.
- AI suggestion is advisory only. It can never create a verdict without a
  legal citation (anti-overreach).
"""
from .evidence import validate_citations, primary_relation, sentence_prohibited, same_proposition
from . import negation as negation_mod

MIN_SCORE = 1.2
CONFLICT_RATIO = 0.45


def signed_invert(hit, claim):
    """A harm card decides an affirmative guidance claim by inversion.

    "Taking more than 4,000 IU is recommended" is refuted by a card stating that
    the same dose exceeds the safe upper limit: the card supports "harmful", which
    is the opposite of "recommended". The relation compatibility table already
    allows a harm card to decide a guidance claim; this function supplies the
    direction, so the stance is inverted exactly once and only for that pairing.
    """
    card_rel = primary_relation(hit.get("claim_in_lib", "") or "")
    claim_rel = primary_relation(claim)
    if sentence_prohibited(claim):
        # "is not recommended" already agrees with the harm card: no inversion.
        return False
    return card_rel == "harm" and claim_rel == "guidance"


def _blank(claim, reason, missing, neg, trace_detail):
    v = {
        "claim": claim,
        "verdict": "undetermined",
        "confidence": "none",
        "reason": reason,
        "missing": missing,
        "citations": [],
        "evidence_scores": {"supports": 0.0, "refutes": 0.0, "contextual": 0},
        "conflict_groups": [],
        "semantic_suggestion": None,
        "polarity": neg,
    }
    trace = {
        "step": "adjudicate",
        "input": claim,
        "method": "three-state+gate+conflict-group+anti-overreach+polarity",
        "output": "undetermined",
        "detail": trace_detail,
        "semantic_used": False,
        "polarity_flipped": bool(neg.get("flip")),
    }
    return v, trace


def adjudicate(claim, hits, semantic=None, negation=None):
    neg = negation or {}

    if neg.get("uncertain"):
        return _blank(claim,
            "Ambiguous double negation. The tool refuses rather than guessing which polarity was meant.",
            "An unambiguous claim to check",
            neg, "double negation -> conservative refusal")

    flip = bool(neg.get("flip"))
    pol_note = ("Negation detected (%s); evidence stance was inverted for scoring. "
                % ", ".join(neg.get("markers", []))) if flip else ""

    if not hits:
        ai_says = (semantic or {}).get("suggestion")
        reason = "No matching evidence card in this corpus; the claim cannot be decided."
        if ai_says in ("supported", "refuted"):
            reason = ("AI suggested '%s', but there is no citable evidence; "
                      "the anti-overreach gate forces refusal." % ai_says)
        v = {
            "claim": claim,
            "verdict": "undetermined",
            "confidence": "none",
            "reason": pol_note + reason,
            "missing": "A directly relevant authoritative source",
            "citations": [],
            "evidence_scores": {"supports": 0.0, "refutes": 0.0, "contextual": 0},
            "conflict_groups": [],
            "semantic_suggestion": ai_says,
            "polarity": neg,
        }
        trace = {
            "step": "adjudicate",
            "input": claim,
            "method": "three-state+gate+conflict-group+anti-overreach+polarity",
            "output": "undetermined(no_hits)",
            "detail": "Zero recall forces refusal; an AI suggestion cannot bypass it.",
            "semantic_used": bool(ai_says),
            "polarity_flipped": flip,
        }
        return v, trace

    # 1. Source discrepancy group takes priority over numeric scoring.
    groups = {}
    for h in hits:
        g = h.get("card", {}).get("conflict_group")
        if g:
            groups.setdefault(g, []).append(h)
    conflicting_groups = []
    for g, hs in groups.items():
        stances = set(x["citation"]["stance"] for x in hs)
        if len(stances) > 1:
            conflicting_groups.append({
                "group": g,
                "stances": sorted(stances),
                "cards": [x["citation"]["card_id"] for x in hs],
            })

    def wscore(h):
        return h["score"] * float(h.get("stance_weight", 1.0))

    def stance_of(h):
        """Effective stance after the claim's polarity and any signed pairing.

        A card whose own claim is already negative ("Antibiotics have no side
        effects") should not have its stance flipped again by a negative claim
        about the same thing ("Antibiotics never produce side effects"): the two
        negatives cancel, and the card's refutation stands.
        """
        st = h["citation"]["stance"]
        if st == "contextual":
            return st
        card_flip = negation_mod.detect(h.get("claim_in_lib", "") or "")["flip"]
        same = same_proposition(claim, h.get("claim_in_lib", "") or "")
        if same:
            # The claim and the card assert the same statement, so only their
            # relative polarity matters: "antibiotics cause side effects" against
            # a card reading "antibiotics have no side effects" must flip once.
            adjust = bool(flip) != bool(card_flip)
        else:
            adjust = bool(flip)
        adjust = adjust != signed_invert(h, claim)
        if adjust:
            return "refutes" if st == "supports" else "supports"
        return st

    sup = sum(wscore(h) for h in hits if stance_of(h) == "supports")
    ref = sum(wscore(h) for h in hits if stance_of(h) == "refutes")
    ctx = [h for h in hits if stance_of(h) == "contextual"]
    total = sup + ref
    ratio = min(sup, ref) / max(sup, ref) if sup > 0 and ref > 0 else 0.0

    verdict, confidence, reason, missing = "undetermined", "low", "", ""

    if conflicting_groups:
        reason = ("The retrieved sources differ in wording (%s). This tool shows the "
                  "difference and does not adjudicate." % ", ".join(g["group"] for g in conflicting_groups))
        missing = "Open both sources and judge for yourself; this tool takes no position"
    elif total > 0 and max(sup, ref) < MIN_SCORE:
        reason = "Retrieved evidence is below the decision threshold; no verdict is justified."
        missing = "A more direct and authoritative source"
    elif sup > 0 and ref > 0 and ratio >= CONFLICT_RATIO:
        reason = "Supporting and refuting evidence are close in strength; this is an evidence conflict."
        missing = "A higher-authority source to settle the conflict"
    elif sup >= MIN_SCORE and ref >= MIN_SCORE:
        winner, strength = ("supported", sup) if sup > ref else ("refuted", ref)
        verdict = winner
        confidence = "high" if strength >= MIN_SCORE * 2 else "medium"
        reason = "Sources in one direction are clearly stronger than the other side."
    elif ref >= MIN_SCORE:
        verdict, confidence = "refuted", ("high" if ref >= MIN_SCORE * 2 else "medium")
        reason = "An authoritative source in this corpus refutes the claim."
    elif sup >= MIN_SCORE:
        verdict, confidence = "supported", ("high" if sup >= MIN_SCORE * 2 else "medium")
        reason = "An authoritative source in this corpus supports the claim."
    else:
        reason = "Only background evidence was found; no verdict is justified."
        missing = "A source that directly verifies the claim"

    citations = []
    for h in hits:
        c = dict(h["citation"])
        eff = stance_of(h)
        c["effective_stance"] = eff
        c["polarity_flipped"] = eff != c["stance"]
        citations.append(c)

    if semantic and semantic.get("suggestion") in ("supported", "refuted") and not citations:
        reason = "AI expressed a preference, but no legal citation exists; anti-overreach gate applied."
        missing = "A legal citation (an AI suggestion cannot replace evidence)"

    if verdict in ("supported", "refuted"):
        ok, miss = validate_citations(citations)
        if not ok:
            verdict, confidence = "undetermined", "low"
            reason = "Citation fields are incomplete; gate downgraded the verdict to refusal."
            missing = "Complete citation (" + ",".join(miss) + ")"

    v = {
        "claim": claim,
        "verdict": verdict,
        "confidence": confidence,
        "reason": pol_note + reason,
        "missing": missing,
        "citations": citations,
        "evidence_scores": {"supports": round(sup, 4), "refutes": round(ref, 4), "contextual": len(ctx)},
        "conflict_groups": conflicting_groups,
        "semantic_suggestion": (semantic or {}).get("suggestion"),
        "polarity": neg,
    }
    trace = {
        "step": "adjudicate",
        "input": claim,
        "method": "three-state+gate+conflict-group+anti-overreach+polarity",
        "output": verdict,
        "detail": "supports=%.2f refutes=%.2f threshold=%.2f; ratio=%.2f; groups=%d; flipped=%s" % (
            sup, ref, MIN_SCORE, ratio, len(conflicting_groups), flip),
        "semantic_used": bool(semantic and semantic.get("suggestion")),
        "polarity_flipped": flip,
    }
    return v, trace
