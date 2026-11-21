#!/usr/bin/env python3
"""Oracle-evidence evaluation: separate retrieval coverage from semantic rules.

The external benchmark run (`eval_external.py`) refuses most claims because the
100-card corpus does not cover them, so its accuracy mostly measures coverage.
This script answers a different question: **if the gold evidence passage is handed
to the kernel as a single card, can the semantic layer (polarity, relation,
strength, quantity, object and subject guards) produce the right verdict?**

Input cards are built from the benchmark's own evidence sentences. They are
evaluation-only: they never enter the corpus, and the URL field is a `urn:` marker
because the released samples deliberately omit links. Nothing here is presented
as a product citation; the only output is a diagnostic table plus a failure dump.

Usage:
    python tools/eval_oracle.py                 # dev slice, all datasets with evidence
    python tools/eval_oracle.py --split holdback
    python tools/eval_oracle.py --dataset healthver --limit 50
"""
import argparse
import json
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.adjudicate import adjudicate  # noqa: E402
from core.evidence import matched_anchors  # noqa: E402
from core.negation import detect  # noqa: E402

DATASETS = ["healthver", "averitec", "pubhealth", "vitaminc", "fever"]
LABELS = ["supported", "refuted", "undetermined"]


def load_rows(name, split):
    path = os.path.join(ROOT, "data", "external", "samples", f"{name}.jsonl")
    if not os.path.exists(path):
        return None
    rows = [json.loads(line) for line in open(path, encoding="utf-8")]
    return [r for r in rows if r.get("split") == split]


def evidence_text(row, max_chars=900):
    parts = []
    for doc in row.get("evidence_docs", []):
        for sentence in doc.get("sentences", [])[:4]:
            if sentence and sentence not in parts:
                parts.append(sentence.strip())
    text = " ".join(parts)
    return text[:max_chars]


def one_hit(row, text):
    """Build the single card the oracle hands to the adjudicator."""
    cid = "B1"
    citation = {
        "card_id": cid,
        "source_id": row["dataset"].upper() + "-GOLD",
        "source_name": row["dataset"] + " gold evidence (evaluation only)",
        "url": "urn:benchmark:%s:%s" % (row["dataset"], row["id"]),
        "snippet": text,
        "stance": "supports",
        "matched": matched_anchors(row["text"], text),
    }
    card = {
        "card_id": cid,
        "claim": text,
        "source_id": citation["source_id"],
        "source_name": citation["source_name"],
        "url": citation["url"],
        "snippet": text,
        "stance": "supports",
        "tags": [],
    }
    return {"score": 99.0, "anchor_coverage": 1.0, "stance_weight": 1.0,
            "card": card, "citation": citation, "claim_in_lib": text}


def run_dataset(name, split, limit, dump_failures=12):
    rows = load_rows(name, split)
    if rows is None:
        return None
    rows = [r for r in rows if evidence_text(r)]
    if limit:
        rows = rows[:limit]
    if not rows:
        return {"dataset": name, "status": "no_rows_with_evidence"}

    preds, failures, t0 = [], [], time.time()
    for row in rows:
        text = evidence_text(row)
        neg = detect(row["text"])
        verdict, _ = adjudicate(row["text"], [one_hit(row, text)], negation=neg)
        pred = verdict["verdict"]
        preds.append((row["gold"], pred, row["text"], text, verdict.get("evidence_scores")))
        if pred != row["gold"] and len(failures) < dump_failures:
            failures.append({
                "id": row["id"], "gold": row["gold"], "pred": pred,
                "claim": row["text"], "evidence": text,
                "scores": verdict.get("evidence_scores"),
                "reason": verdict.get("reason", "")[:180],
                "polarity_flipped": bool(neg.get("flip")),
            })

    n = len(preds)
    acc = sum(1 for g, p, *_ in preds if g == p) / n
    per = {}
    for lab in LABELS:
        tp = sum(1 for g, p, *_ in preds if g == lab and p == lab)
        fp = sum(1 for g, p, *_ in preds if g != lab and p == lab)
        fn = sum(1 for g, p, *_ in preds if g == lab and p != lab)
        per[lab] = {
            "precision": round(tp / (tp + fp), 4) if tp + fp else 0.0,
            "recall": round(tp / (tp + fn), 4) if tp + fn else 0.0,
            "support": tp + fn,
        }
    macro = round(statistics.mean(
        2 * per[l]["precision"] * per[l]["recall"] / (per[l]["precision"] + per[l]["recall"])
        if per[l]["precision"] + per[l]["recall"] else 0.0 for l in LABELS), 4)
    decided = [p for g, p, *_ in preds if p != "undetermined"]
    decided_acc = round(sum(1 for g, p, *_ in preds if p != "undetermined" and g == p) / len(decided), 4) if decided else None
    gold_counts = {l: sum(1 for g, _, *_ in preds if g == l) for l in LABELS}
    baseline = round(max(gold_counts.values()) / n, 4)
    confusion = {g: {p: sum(1 for gg, pp, *_ in preds if gg == g and pp == p) for p in LABELS}
                 for g in LABELS}
    return {
        "dataset": name, "split": split, "n": n,
        "accuracy": round(acc, 4), "macro_f1": macro, "per_label": per,
        "coverage": round(len(decided) / n, 4),
        "accuracy_on_decided": decided_acc,
        "always_undetermined_baseline": baseline,
        "gold_distribution": gold_counts, "confusion": confusion,
        "runtime_s": round(time.time() - t0, 3),
        "failures": failures,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["dev", "holdback"])
    ap.add_argument("--dataset", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=os.path.join(ROOT, "evidence", "oracle_eval.json"))
    args = ap.parse_args()

    names = [args.dataset] if args.dataset else DATASETS
    out = {"status": "run", "split": args.split,
           "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "question": "Can the semantic layer decide when the gold evidence passage is supplied?",
           "protocol": ("Each claim is paired with one card built from the benchmark's own evidence "
                        "sentences; the card asserts the evidence, so a correct verdict means the "
                        "rule layer recognised agreement, contradiction, or a scope mismatch. "
                        "URLs are urn: markers because released samples omit links."),
           "datasets": {}}
    for name in names:
        r = run_dataset(name, args.split, args.limit)
        if r is None:
            continue
        out["datasets"][name] = r
        if r.get("status"):
            print(f"[{name}] {r['status']}")
            continue
        print(f"[{name}] n={r['n']} acc={r['accuracy']} macroF1={r['macro_f1']} "
              f"coverage={r['coverage']} decided_acc={r['accuracy_on_decided']} baseline={r['always_undetermined_baseline']}")
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True)
    print("out:", args.out)


if __name__ == "__main__":
    main()
