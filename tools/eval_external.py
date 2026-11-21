#!/usr/bin/env python3
"""External benchmark evaluation (dev slice only).

For each sampled claim: run the offline kernel (no LLM), map its three-state verdict
against the dataset gold label, and report accuracy / macro-F1 / per-label precision-recall
/ refusal rate / selective accuracy at 100-70-50% coverage.

Hold-back slice is deliberately NOT evaluated here: the plan reserves it for a single final
touch. Pass --split holdback explicitly when that moment comes.
"""
import argparse
import json
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.pipeline import analyze  # noqa: E402

DATASETS = ["fever", "scifact", "healthver", "averitec", "pubhealth", "vitaminc"]
LABELS = ["supported", "refuted", "undetermined"]


def _margin(v):
    """Confidence proxy: how far the winning stance is from the runner-up."""
    es = v.get("evidence_scores") or {}
    a, b = float(es.get("supports", 0.0)), float(es.get("refutes", 0.0))
    if v.get("verdict") == "undetermined":
        return 0.0
    return abs(a - b) + (max(a, b) * 0.1)


def run_dataset(name, split, seed, samples_dir=None):
    samples_dir = samples_dir or os.path.join(ROOT, "data", "external", "samples")
    path = os.path.join(samples_dir, f"{name}.jsonl")
    if not os.path.exists(path):
        return None
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    rows = [r for r in rows if r["split"] == split]
    if not rows:
        return None
    preds, wrong_cases, t0 = [], [], time.time()
    for r in rows:
        res = analyze(r["text"], use_llm=False)
        v = res["verdicts"][0] if res.get("verdicts") else {"verdict": "undetermined"}
        pred = v.get("verdict", "undetermined")
        preds.append((r["gold"], pred, _margin(v), res.get("unsupported_input")))
        if pred != "undetermined" and pred != r["gold"]:
            wrong_cases.append({
                "id": r["id"], "text": r["text"], "gold": r["gold"], "pred": pred,
                "cards": [c.get("card_id") for c in (v.get("citations") or [])],
                "sources": [c.get("source_id") for c in (v.get("citations") or [])],
                "atom": v.get("claim"),
            })
    runtime = round(time.time() - t0, 3)

    acc = sum(1 for g, p, _, _ in preds if g == p) / len(preds)
    per = {}
    for lab in LABELS:
        tp = sum(1 for g, p, _, _ in preds if g == lab and p == lab)
        fp = sum(1 for g, p, _, _ in preds if g != lab and p == lab)
        fn = sum(1 for g, p, _, _ in preds if g == lab and p != lab)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        per[lab] = {"precision": round(prec, 4), "recall": round(rec, 4), "support": tp + fn}
    macro_f1 = round(statistics.mean(
        2 * per[l]["precision"] * per[l]["recall"] / (per[l]["precision"] + per[l]["recall"])
        if (per[l]["precision"] + per[l]["recall"]) else 0.0 for l in LABELS), 4)

    refusal = sum(1 for _, p, _, _ in preds if p == "undetermined") / len(preds)
    decided = [(g, p) for g, p, _, _ in preds if p != "undetermined"]
    decided_acc = round(sum(1 for g, p in decided if g == p) / len(decided), 4) if decided else None
    undet_pred = [(g, p) for g, p, _, _ in preds if p == "undetermined"]
    undet_prec = round(sum(1 for g, p in undet_pred if g == "undetermined") / len(undet_pred), 4) if undet_pred else None
    gold_counts = {l: sum(1 for g, _, _, _ in preds if g == l) for l in LABELS}
    baseline = round(max(gold_counts.values()) / len(preds), 4)
    order = sorted(preds, key=lambda x: -x[2])
    selective = {}
    for cov in (100, 70, 50):
        k = max(1, int(len(order) * cov / 100))
        selective[str(cov)] = round(sum(1 for g, p, _, _ in order[:k] if g == p) / k, 4)

    return {
        "dataset": name, "split": split, "n": len(preds), "mapping": None, "accuracy": round(acc, 4),
        "macro_f1": macro_f1, "per_label": per, "refusal_rate": round(refusal, 4),
        "coverage": round(1 - refusal, 4),
        "accuracy_on_decided": decided_acc,
        "answers": len(decided),
        "correct": sum(1 for g, p in decided if g == p),
        "wrong": sum(1 for g, p in decided if g != p),
        "wrong_cases": wrong_cases,
        "undetermined_precision": undet_prec,
        "always_undetermined_baseline": baseline,
        "gold_distribution": gold_counts,
        "selective_accuracy": selective,
        "citation_precision": None,
        "citation_recall": None,
        "citation_metrics_note": "The sampled evidence documents carry no URLs (links were removed at sampling time), so citation_precision/recall cannot be computed on this slice."
                                 "The paragraph-level equivalent is reported in evidence/cards_evidence.jsonl.",
        "runtime_s": runtime, "seed": seed, "commit": "n/a (working tree)",
        "gated_inputs": sum(1 for _, _, _, u in preds if u),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["dev", "holdback", "holdback2"])
    ap.add_argument("--seed", type=int, default=20261120)
    ap.add_argument("--samples-dir", default=os.path.join(ROOT, "data", "external", "samples"))
    ap.add_argument("--out", default=os.path.join(ROOT, "evidence", "external_eval.json"))
    ap.add_argument("--force-rerun", action="store_true",
                    help="hold-back slices are one-shot; this bypass exists for a deliberate re-open "
                         "that must then be explained in the ledger")
    a = ap.parse_args()

    # A hold-back slice stops being a hold-out the second time it is scored. The ledger is
    # the record; the guard is that a second entry requires --force-rerun, so re-opening is
    # always a visible act rather than an accident.
    ledger_path = os.path.join(ROOT, "evidence", "holdback_ledger.json")
    ledger = []
    if os.path.exists(ledger_path):
        with open(ledger_path, "r", encoding="utf-8") as fh:
            ledger = json.load(fh).get("opens", [])
    tag = os.path.basename(os.path.normpath(a.samples_dir))
    if a.split.startswith("holdback"):
        prior = [x for x in ledger if x.get("split") == a.split and x.get("samples") == tag]
        if prior and not a.force_rerun:
            print("refusing to score %s again: it was opened on %s (n=%s, %s). "
                  "A slice scored twice is a tuned set; use --force-rerun only if you will say so."
                  % (a.split, prior[-1].get("evaluated_at"), prior[-1].get("n"), prior[-1].get("out")))
            return 3

    mapping = json.load(open(os.path.join(a.samples_dir, "samples_index.json"),
                             encoding="utf-8"))["datasets"] if os.path.exists(
        os.path.join(a.samples_dir, "samples_index.json")) else {}
    out = {"status": "run", "split": a.split, "seed": a.seed,
           "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "samples_dir": os.path.relpath(a.samples_dir, ROOT).replace("\\", "/"),
           "kernel": "offline deterministic core (use_llm=False)",
           "datasets": {}}
    for name in DATASETS:
        r = run_dataset(name, a.split, a.seed, a.samples_dir)
        if r is None:
            out["datasets"][name] = {"status": "no_samples"}
            continue
        r["mapping"] = (mapping.get(name) or {}).get("mapping")
        out["datasets"][name] = r
        print(f"[{name}] n={r['n']} acc={r['accuracy']} macroF1={r['macro_f1']} "
              f"refusal={r['refusal_rate']} answers={r['answers']} correct={r['correct']} "
              f"wrong={r['wrong']} {r['runtime_s']}s")
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True)
    print("out:", a.out)

    if a.split.startswith("holdback"):
        total_n = sum(v.get("n", 0) for v in out["datasets"].values() if isinstance(v, dict))
        ledger.append({"split": a.split, "samples": tag, "seed": a.seed,
                       "evaluated_at": out["evaluated_at"], "n": total_n,
                       "out": os.path.relpath(a.out, ROOT).replace("\\", "/"),
                       "forced": bool(a.force_rerun),
                       "recorded_retroactively": False})
        with open(ledger_path, "w", encoding="utf-8") as fh:
            json.dump({"opens": ledger}, fh, ensure_ascii=False, indent=2)
        print("ledger: %d open(s) recorded" % len(ledger))
    return 0


if __name__ == "__main__":
    main()
