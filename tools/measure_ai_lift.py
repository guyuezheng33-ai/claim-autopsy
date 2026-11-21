"""Measure the contribution of AI on two benchmarks (v5).

Shallow set: near-synonym paraphrases; measures verdict consistency.
Deep set: low-lexical-overlap restatements with rule-zero-recall; measures how
often AI recall reaches the expected verdict with a REAL, correctly-stanced card.

Rule-only is always computed live from the deterministic core.
Rule+AI is measured only when LLM_API_KEY is present. Without a key the script
prints SKIPPED and does NOT invent a number.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.pipeline import analyze  # noqa: E402
from core.evidence import load_corpus  # noqa: E402


def shallow_consistency(pairs, use_llm):
    ok = 0
    details = []
    for p in pairs:
        a = analyze(p["a"], use_llm=use_llm)["verdicts"]
        b = analyze(p["b"], use_llm=use_llm)["verdicts"]
        same = len(a) == len(b) == 1 and a[0]["verdict"] == b[0]["verdict"]
        ok += same
        details.append({"id": p["id"], "same": same,
                        "a": a[0]["verdict"] if len(a) == 1 else "?",
                        "b": b[0]["verdict"] if len(b) == 1 else "?"})
    return {"consistent": ok, "total": len(pairs),
            "rate": round(ok / len(pairs), 4) if pairs else 0.0,
            "details": details}


def deep_recall(cases, use_llm):
    """Correct = expected verdict reached, and every citation is a real card
    whose stance equals the corpus's stored stance (no AI-authored stance)."""
    corpus_cards = {c["card_id"]: c for c in load_corpus()["evidence_cards"]}
    ok = 0
    details = []
    for case in cases:
        v = analyze(case["text"], use_llm=use_llm)["verdicts"][0]
        verdict_ok = v["verdict"] == case["expected"]
        cited = [c["card_id"] for c in v["citations"]]
        real = all(cid in corpus_cards for cid in cited)
        stance_ok = all(c["stance"] == corpus_cards[c["card_id"]]["stance"]
                        for c in v["citations"] if c["card_id"] in corpus_cards)
        card_ok = (case["expect_card"] in cited) if case.get("expect_card") else True
        good = verdict_ok and real and stance_ok and card_ok
        ok += good
        details.append({"id": case["id"], "correct": good,
                        "expected": case["expected"], "got": v["verdict"],
                        "origin": v.get("origin", "lexical"), "cited": cited,
                        "real_ids": real, "stance_from_card": stance_ok})
    return {"correct": ok, "total": len(cases),
            "rate": round(ok / len(cases), 4) if cases else 0.0,
            "details": details}


def main():
    with open(os.path.join(ROOT, "data", "golden_set.json"), "r", encoding="utf-8") as f:
        shallow = json.load(f)["paraphrase_pairs"]
    with open(os.path.join(ROOT, "data", "paraphrase_deep.json"), "r", encoding="utf-8") as f:
        deep = json.load(f)["cases"]

    rule = {
        "shallow_consistency": shallow_consistency(shallow, use_llm=False),
        "deep_recall": deep_recall(deep, use_llm=False),
    }
    if not os.environ.get("LLM_API_KEY"):
        payload = {
            "status": "SKIPPED",
            "reason": "LLM_API_KEY is not set. Rule-only is measured live; rule+AI is not measured and no number is pre-filled.",
            "rule_only": rule,
            "rule_plus_ai": {"status": "NOT_MEASURED"},
        }
    else:
        ai = {
            "shallow_consistency": shallow_consistency(shallow, use_llm=True),
            "deep_recall": deep_recall(deep, use_llm=True),
        }
        payload = {
            "status": "MEASURED",
            "rule_only": rule,
            "rule_plus_ai": ai,
            "delta": {
                "shallow_consistency": round(ai["shallow_consistency"]["rate"] - rule["shallow_consistency"]["rate"], 4),
                "deep_recall": round(ai["deep_recall"]["rate"] - rule["deep_recall"]["rate"], 4),
            },
        }

    out_dir = os.path.join(ROOT, "evidence")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "ai_lift.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    summary = {
        "status": payload["status"],
        "rule_shallow": rule["shallow_consistency"]["rate"],
        "rule_deep": rule["deep_recall"]["rate"],
        "delta": payload.get("delta"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("Evidence: %s" % out_path)


if __name__ == "__main__":
    main()
