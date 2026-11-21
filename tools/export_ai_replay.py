"""Capture real dual-path runs for the static-page AI contrast panel.

For every case in data/paraphrase_deep.json this script executes TWO real runs:

  * offline deterministic core (no key)
  * AI-assisted path (requires LLM_API_KEY in the environment)

It writes data/ai_recall_replay.json. Nothing here is hand-authored: every
verdict, citation and trace line comes from an executed pipeline call. The
credential is read only from the environment and is never written to disk.

Usage:
    LLM_API_KEY=... python tools/export_ai_replay.py
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import llm  # noqa: E402
from core.evidence import load_corpus  # noqa: E402
from core.pipeline import analyze  # noqa: E402

BENCH = os.path.join(ROOT, "data", "paraphrase_deep.json")
LIFT = os.path.join(ROOT, "evidence", "ai_lift.json")
OUT = os.path.join(ROOT, "data", "ai_recall_replay.json")

CITE_FIELDS = ("card_id", "source_id", "source_name", "url", "snippet",
               "stance", "effective_stance", "polarity_flipped")


def slim(v):
    """Keep only judge-facing fields of a verdict."""
    return {
        "verdict": v["verdict"],
        "confidence": v.get("confidence", ""),
        "reason": v.get("reason", ""),
        "missing": v.get("missing", ""),
        "explain": v.get("explain", ""),
        "citations": [{k: c.get(k) for k in CITE_FIELDS} for c in v.get("citations", [])],
    }


def main():
    if not llm.available():
        raise SystemExit("LLM_API_KEY is not set. Replay must come from real API calls.")
    with open(BENCH, "r", encoding="utf-8") as f:
        bench = json.load(f)
    with open(LIFT, "r", encoding="utf-8") as f:
        lift = json.load(f)

    corpus = load_corpus()
    real_ids = {c["card_id"] for c in corpus["evidence_cards"]}
    cases = []

    for item in bench["cases"]:
        text = item["text"]
        off = analyze(text, use_llm=False)
        ai = analyze(text, use_llm=True)
        ov, av = off["verdicts"][0], ai["verdicts"][0]
        recall = next((t for t in ai["trace"] if t["step"] == "recall"), None)
        retrieve = next((t for t in ai["trace"] if t["step"] == "retrieve"), None)
        adjud = next((t for t in ai["trace"] if t["step"] == "adjudicate"), None)

        # Fail loudly rather than shipping a replay with an invented citation.
        for c in av.get("citations", []):
            if c["card_id"] not in real_ids:
                raise SystemExit("AI produced a card id not in the corpus: %s" % c["card_id"])

        cases.append({
            "id": item["id"],
            "text": text,
            "expected": item["expected"],
            "expect_card": item["expect_card"],
            "kind": "gain" if item["expected"] != "undetermined" else "gated",
            "offline": slim(ov),
            "ai": {
                **slim(av),
                "mode": ai.get("mode", ""),
                "origin": "semantic_recall" if recall else "rule_retrieval",
                "recall_output": recall.get("output") if recall else None,
                "recall_detail": recall.get("detail") if recall else None,
                "retrieve_output": retrieve.get("output") if retrieve else None,
                "adjudicate_detail": adjud.get("detail") if adjud else None,
            },
        })
        print("captured %-5s offline=%-13s ai=%-13s origin=%s" % (
            item["id"], ov["verdict"], av["verdict"], cases[-1]["ai"]["origin"]))

    gains = [c for c in cases if c["kind"] == "gain"]
    gated = [c for c in cases if c["kind"] == "gated"]
    offline_rate = sum(1 for c in cases if c["offline"]["verdict"] == "undetermined") / len(cases)
    ai_rate = sum(1 for c in gains if c["ai"]["verdict"] == c["expected"]) / len(gains)

    payload = {
        "meta": {
            "purpose": "Recorded dual-path evidence for the public static page: the offline core refuses low-overlap restatements, while AI same-proposition recall reaches a gated verdict with a real corpus card.",
            "captured_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "producer": "tools/export_ai_replay.py",
            "source": "Live API calls executed by the producer; no verdict or citation below is hand-written.",
            "provider": "DeepSeek",
            "requested_model": llm.MODEL,
            "offline_engine": "Local deterministic core",
            "honesty": "Recorded, not live. A static page cannot call a model; these are real recorded results, and the live AI path requires running serve.py with a key.",
            "stance_rule": "Every stance is read from the stored evidence card; the AI never supplies or alters a stance or a verdict.",
            "case_count": len(cases),
            "gain_case_count": len(gains),
            "gated_case_count": len(gated),
            "offline_refusal_rate": round(offline_rate, 4),
            "ai_success_rate_on_gain_cases": round(ai_rate, 4),
            "measured_delta": lift.get("delta", {}).get("deep_recall"),
            "benchmark": "data/paraphrase_deep.json",
            "measurement": "evidence/ai_lift.json",
        },
        "cases": cases,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("\nwrote %s | cases=%d gain=%d gated=%d offline_refusal=%.4f ai_success=%.4f" % (
        OUT, len(cases), len(gains), len(gated), offline_rate, ai_rate))


if __name__ == "__main__":
    main()
