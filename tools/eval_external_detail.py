#!/usr/bin/env python3
"""Per-claim external diagnosis (dev slice only).

The aggregate eval reports accuracy, which hides the thing this project cares
about most: which claims the kernel was willing to answer, and what it said.
This script writes one row per dev claim — gold label, verdict, cited card,
matched words and the near-miss reasons — so every wrong verdict in the
published numbers can be read by a stranger, and so the guards can be tuned
against evidence instead of intuition.

Rows where the verdict is `None` are inputs the product deliberately refuses to
parse (a question, not a claim); they are counted separately from refusals.
"""
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.pipeline import analyze  # noqa: E402

DATASETS = ["fever", "healthver", "averitec", "pubhealth", "vitaminc"]
OUT = os.path.join(ROOT, "evidence", "external_dev_detail.json")


def main():
    rows = []
    for name in DATASETS:
        path = os.path.join(ROOT, "data", "external", "samples", "%s.jsonl" % name)
        if not os.path.exists(path):
            continue
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            if r["split"] != "dev":
                continue
            res = analyze(r["text"], use_llm=False)
            v = (res.get("verdicts") or [{}])[0]
            rows.append({
                "dataset": name,
                "text": r["text"],
                "gold": r["gold"],
                "pred": v.get("verdict"),
                "reason": v.get("reason"),
                "cites": [(c.get("card_id"), c.get("stance")) for c in (v.get("citations") or [])],
                "matched": [c.get("matched") for c in (v.get("citations") or [])],
                "near": [(n.get("card_id"), n.get("reasons")) for n in (v.get("near_miss") or [])],
            })

    answered = [r for r in rows if r["pred"] in ("supported", "refuted")]
    wrong = [r for r in answered if r["pred"] != r["gold"]]
    gated = [r for r in rows if r["pred"] is None]

    print("dev claims: %d | answered: %d | correct: %d | refused: %d | gated as not-a-claim: %d"
          % (len(rows), len(answered), len(answered) - len(wrong),
             len(rows) - len(answered) - len(gated), len(gated)))
    for name in DATASETS:
        sub = [r for r in rows if r["dataset"] == name]
        ans = [r for r in sub if r["pred"] in ("supported", "refuted")]
        bad = [r for r in ans if r["pred"] != r["gold"]]
        print("%-10s n=%3d answered=%2d wrong=%2d" % (name, len(sub), len(ans), len(bad)))
        for r in bad:
            print("   - [%s -> %s] %s | cites=%s | matched=%s"
                  % (r["gold"], r["pred"], r["text"][:100], r["cites"][:2], (r["matched"] or [])[:1]))
        if bad:
            print("   wrong pairs:", dict(collections.Counter((r["gold"], r["pred"]) for r in bad)))

    payload = {
        "split": "dev",
        "totals": {"claims": len(rows), "answered": len(answered),
                   "correct": len(answered) - len(wrong), "wrong": len(wrong), "gated": len(gated)},
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("written evidence/external_dev_detail.json")


if __name__ == "__main__":
    main()
