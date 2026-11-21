"""Write a receipt for the external evaluation, produced by an evaluation it runs itself.

Why this exists: A35 recomputes the five dev slices, which proves the published numbers are
reproducible *now*. It does not say when the numbers were first produced, by which command, or
whether the sample files on disk are the ones that produced them. The same failure that A37
closed for the acceptance run existed one layer out for the benchmark: a table of numbers with
no record of the run behind it.

This script runs `tools/eval_external.py` and `tools/eval_external_detail.py` itself, then writes
`evidence/eval_receipt.json`: exit codes, the commands, UTC times, the per-dataset numbers read
back from the file it just wrote, the SHA-256 of 15 artefacts (the five sample files, the samples
index, both result files, the corpus and the six kernel modules that decide verdicts), and the
hold-back block — read from the frozen file, with its ledger entry, because that slice is not
re-scored here.

Usage: python tools/make_eval_receipt.py [--split dev]
"""
import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "evidence")
OUT = os.path.join(EV, "eval_receipt.json")

SAMPLES = ["fever", "healthver", "averitec", "pubhealth", "vitaminc"]

ARTEFACTS = (
    ["data/external/samples/%s.jsonl" % n for n in SAMPLES]
    + ["data/external/samples/samples_index.json",
       "evidence/external_eval_v4.json",
       "evidence/external_dev_detail.json",
       "evidence/external_eval_holdback.json",
       "evidence/holdback_ledger.json",
       "data/claims.json",
       "core/evidence.py",
       "core/pipeline.py",
       "core/decompose.py",
       "core/adjudicate.py",
       "core/negation.py",
       "core/semantic.py"]
)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(payload):
    return json.dumps(payload, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def run(cmd):
    got = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "command": " ".join(cmd),
        "exit_code": got.returncode,
        "stdout_sha256": hashlib.sha256((got.stdout or "").encode("utf-8")).hexdigest(),
        "stdout_tail": [ln for ln in (got.stdout or "").strip().splitlines() if ln.strip()][-3:],
    }


def main():
    split = "dev"
    if "--split" in sys.argv:
        split = sys.argv[sys.argv.index("--split") + 1]
    if split.startswith("holdback"):
        print("this receipt covers the dev slice only; hold-back opens are recorded in "
              "evidence/holdback_ledger.json, and are not re-scored by a receipt run")
        return 2

    eval_run = run([sys.executable, "tools/eval_external.py", "--split", split,
                    "--out", os.path.join("evidence", "external_eval_v4.json")])
    if eval_run["exit_code"] != 0:
        print("the evaluation did not finish; no receipt. %s" % eval_run["stdout_tail"])
        return 3
    detail_run = run([sys.executable, "tools/eval_external_detail.py"])
    if detail_run["exit_code"] != 0:
        print("the detail pass did not finish; no receipt (a receipt must describe a complete run)")
        return 3

    with open(os.path.join(EV, "external_eval_v4.json"), "r", encoding="utf-8") as fh:
        ev = json.load(fh)

    per = {}
    for name in SAMPLES:
        d = ev.get("datasets", {}).get(name) or {}
        if d.get("status") == "no_samples":
            continue
        per[name] = {"n": d.get("n"), "accuracy": d.get("accuracy"),
                     "refusal": d.get("refusal_rate"), "accuracy_on_decided": d.get("accuracy_on_decided"),
                     "answers": d.get("answers"), "correct": d.get("correct"), "wrong": d.get("wrong"),
                     "baseline": d.get("always_undetermined_baseline")}
    totals = {k: sum((v.get(k) or 0) for v in per.values()) for k in ("n", "answers", "correct", "wrong")}

    hold = {"status": "not_opened"}
    hb_path = os.path.join(EV, "external_eval_holdback.json")
    if os.path.exists(hb_path):
        with open(hb_path, "r", encoding="utf-8") as fh:
            hb = json.load(fh)
        ledger_path = os.path.join(EV, "holdback_ledger.json")
        opens = []
        if os.path.exists(ledger_path):
            with open(ledger_path, "r", encoding="utf-8") as fh:
                opens = json.load(fh).get("opens", [])
        hb_open = [x for x in opens if x.get("split") == "holdback"]
        hold = {
            "status": "opened",
            "evidence_kind": "frozen result of the single open; this script does not re-score it",
            "file_sha256": sha256(hb_path),
            "evaluated_at": hb.get("evaluated_at"),
            "split": hb.get("split"),
            "seed": hb.get("seed"),
            "opens": len(hb_open),
            "ledger_entry": hb_open[-1] if hb_open else None,
            "per_dataset": {n: {"n": (hb.get("datasets", {}).get(n) or {}).get("n"),
                                "accuracy": (hb.get("datasets", {}).get(n) or {}).get("accuracy"),
                                "refusal": (hb.get("datasets", {}).get(n) or {}).get("refusal_rate"),
                                "answers": (hb.get("datasets", {}).get(n) or {}).get("answers"),
                                "correct": (hb.get("datasets", {}).get(n) or {}).get("correct"),
                                "wrong": (hb.get("datasets", {}).get(n) or {}).get("wrong")}
                            for n in SAMPLES
                            if (hb.get("datasets", {}).get(n) or {}).get("status") != "no_samples"},
        }
        hold["totals"] = {k: sum((v.get(k) or 0) for v in hold["per_dataset"].values())
                          for k in ("n", "answers", "correct", "wrong")}

    payload = {
        "schema": "claim-autopsy/eval-receipt/1",
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "split": split,
        "seed": ev.get("seed"),
        "evaluated_at": ev.get("evaluated_at"),
        "kernel": ev.get("kernel"),
        "python": platform.python_version(),
        "runs": [eval_run, detail_run],
        "datasets": per,
        "totals": totals,
        "holdback": hold,
        "artefacts": {rel: sha256(os.path.join(ROOT, rel)) for rel in ARTEFACTS},
    }
    payload["receipt_id"] = hashlib.sha256(canonical(payload)).hexdigest()[:32]
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print("wrote evidence/eval_receipt.json  id=%s  n=%d  answers=%d  correct=%d  wrong=%d  "
          "artefacts=%d  holdback=%s"
          % (payload["receipt_id"], totals["n"], totals["answers"], totals["correct"],
             totals["wrong"], len(payload["artefacts"]), hold["status"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
