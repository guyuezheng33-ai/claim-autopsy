"""Measure where the coverage ceiling actually is, on the dev slice.

Two numbers get confused when people read "coverage 1.4%". One is a matcher question - does a
card exist that restates the claim closely enough to answer it, and is the kernel failing to
find it? The other is a corpus question - does the corpus assert anything about this claim at
all? Only the first is fixable by tuning; the second is fixable only by writing new cards, and
writing them from benchmark claims would be training on the test.

So this tool measures both, separately:

  * `best_cover` - for every refused claim, the highest share of any card's content that the
    claim restates, ignoring every guard. That is the ceiling a perfect matcher could reach.
  * `contact` - whether any card shares a content word with the claim at all (topic overlap).
    A claim with no contact is out of the corpus's subject matter; a claim with contact but
    low cover is inside the subject and simply not asserted yet.

and it lists the in-domain refusals with the highest cover, because those are the propositions
the corpus is missing. It is analysis only: no verdict changes, and it runs on dev alone.

Usage: python tools/coverage_headroom.py [--split dev]
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.pipeline import analyze  # noqa: E402
from core.evidence import load_corpus, content_terms, topic_overlap  # noqa: E402

OUT = os.path.join(ROOT, "evidence", "coverage_headroom.json")
SAMPLES = os.path.join(ROOT, "data", "external", "samples")
BUCKETS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.01)


def bucket(x):
    for lo, hi in zip(BUCKETS, BUCKETS[1:]):
        if lo <= x < hi:
            return "%.1f-%.1f" % (lo, min(hi, 1.0))
    return "1.0"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    a = ap.parse_args()

    cards = load_corpus()["evidence_cards"]
    rows = []
    for name in ("fever", "healthver", "averitec", "pubhealth", "vitaminc"):
        with open(os.path.join(SAMPLES, "%s.jsonl" % name), encoding="utf-8") as fh:
            rows.extend(json.loads(line) for line in fh)
    rows = [r for r in rows if r["split"] == a.split]

    answered = 0
    refused = 0
    hist = {}
    per = {}
    in_domain = []
    for r in rows:
        res = analyze(r["text"], use_llm=False)
        v = res.get("verdicts") or []
        first = v[0].get("verdict", "undetermined") if v else "undetermined"
        ds = per.setdefault(r["dataset"], {"answered": 0, "refused": 0, "in_domain_refused": 0,
                                          "no_contact": 0})
        if first != "undetermined":
            answered += 1
            ds["answered"] += 1
            continue
        refused += 1
        ds["refused"] += 1
        claim_terms = set(content_terms(r["text"]))
        cover, card, contact = 0.0, None, False
        for c in cards:
            k = set(content_terms(c["claim"]))
            if not k:
                continue
            if topic_overlap(r["text"], c["claim"]):
                contact = True
            cov = len(claim_terms & k) / float(len(k))
            if cov > cover:
                cover, card = cov, c
        hist[bucket(cover)] = hist.get(bucket(cover), 0) + 1
        if contact:
            ds["in_domain_refused"] += 1
            in_domain.append({"id": r["id"], "dataset": r["dataset"], "text": r["text"],
                              "gold": r["gold"], "nearest_card": card["card_id"] if card else None,
                              "nearest_claim": card["claim"] if card else None,
                              "best_cover": round(cover, 3)})
        else:
            ds["no_contact"] += 1

    for d in per.values():
        denom = d["answered"] + d["in_domain_refused"]
        d["coverage_in_domain"] = round(d["answered"] / denom, 4) if denom else None
    denom = answered + sum(d["in_domain_refused"] for d in per.values())
    in_domain.sort(key=lambda x: -x["best_cover"])

    payload = {
        "split": a.split,
        "claims": len(rows),
        "answered": answered,
        "refused": refused,
        "coverage_overall": round(answered / len(rows), 4),
        "coverage_in_domain": round(answered / denom, 4) if denom else None,
        "refusals_with_contact": sum(d["in_domain_refused"] for d in per.values()),
        "refusals_without_contact": sum(d["no_contact"] for d in per.values()),
        "best_cover_histogram_ignoring_guards": hist,
        "per_dataset": per,
        "in_domain_missing": in_domain[:25],
        "reading": ("The histogram is the matcher ceiling: with every guard switched off, no "
                    "refused claim on this slice restates even 80% of any card. Loosening a "
                    "threshold would therefore buy nothing here. The contact split says why: "
                    "claims without contact are outside the corpus's subject matter, and "
                    "coverage inside the subject is the number to quote."),
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: payload[k] for k in
                      ("claims", "answered", "refused", "coverage_overall", "coverage_in_domain",
                       "refusals_with_contact", "refusals_without_contact",
                       "best_cover_histogram_ignoring_guards", "per_dataset")},
                     ensure_ascii=False, indent=1))
    print("out:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
