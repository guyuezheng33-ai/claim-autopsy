"""Build a second, never-scored hold-out slice from the full benchmark dumps.

Why this exists: `data/external/samples/` holds 1,200 claims, all of which have now been
looked at - 840 on dev and 360 on the first hold-back. A slice that has been seen is not a
hold-out, and there is no honest way to un-see it. But the full dumps are on disk (FEVER
shared-task dev, AVeriTeC dev, HealthVer dev, PUBHEALTH dev, VitaminC dev/test), so a second
slice can be drawn that shares no claim text with anything already used.

What it does:
  - reads the full dumps from BENCH_RAW (default: the data-agent tree on this machine);
  - drops every row whose normalised text appears in samples 1, the corpus, the golden set or
    the guard set, and every label that maps to `__excluded__`;
  - picks rows deterministically by sha256(dataset|id|text), so the same dumps always produce
    the same slice;
  - writes `data/external/samples2/*.jsonl` in the same row schema as samples 1, with
    `split = "holdback2"`, plus a freeze file recording every file hash.

It does not evaluate anything. Opening this slice is a separate, one-shot act recorded in
`evidence/holdback_ledger.json`.

Usage: python tools/make_holdout2.py [--raw DIR]
"""
import argparse
import csv
import datetime
import hashlib
import io
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The raw benchmark downloads are not part of the repo (they are large and licensed per source),
# so the location is supplied at run time: --raw, or BENCH_RAW in the environment.
DEFAULT_RAW = os.environ.get("BENCH_RAW") or ""
OUT_DIR = os.path.join(ROOT, "data", "external", "samples2")
SEED_TAG = "20261121"

QUOTA = {"fever": 120, "healthver": 120, "averitec": 80, "pubhealth": 80, "vitaminc": 80}

MAPS = {
    "fever": {"SUPPORTS": "supported", "REFUTES": "refuted", "NOT ENOUGH INFO": "undetermined"},
    "healthver": {"Supports": "supported", "Refutes": "refuted", "Neutral": "undetermined"},
    "averitec": {"Supported": "supported", "Refuted": "refuted",
                 "Not Enough Evidence": "undetermined", "Conflicting": "__excluded__"},
    "pubhealth": {"true": "supported", "false": "refuted", "unproven": "undetermined",
                  "mixture": "__excluded__"},
    "vitaminc": {"SUPPORTS": "supported", "REFUTES": "refuted", "NOT ENOUGH INFO": "undetermined"},
}


def norm(s):
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip().lower()


def sha_file(path):
    d = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            d.update(chunk)
    return d.hexdigest()


def used_texts():
    used = set()
    for name in MAPS:
        p = os.path.join(ROOT, "data", "external", "samples", "%s.jsonl" % name)
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                used.add(norm(json.loads(line)["text"]))
    data = json.load(open(os.path.join(ROOT, "data", "claims.json"), encoding="utf-8"))
    for c in data["evidence_cards"]:
        used.add(norm(c["claim"]))
    for rel in ("data/golden_set.json", "data/guard_set.json"):
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        data = json.load(open(p, encoding="utf-8"))
        for c in data.get("cases") or data.get("probes") or []:
            if isinstance(c, dict) and c.get("text"):
                used.add(norm(c["text"]))
    return used


def template_row(name):
    src = os.path.join(ROOT, "data", "external", "samples", "%s.jsonl" % name)
    return json.loads(open(src, encoding="utf-8").readline())


def base_row(name, tpl, raw_id, text, label):
    return {
        "dataset": name,
        "domain": tpl.get("domain"),
        "evidence_docs": [],
        "gold": MAPS[name][label],
        "id": "%s-%s" % (name, raw_id),
        "licence": tpl.get("licence"),
        "mapped_from": label,
        "source_label": label,
        "split": "holdback2",
        "text": re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip(),
    }


def raw_rows(name, raw):
    if name == "fever":
        with open(os.path.join(raw, "fever_shared_task_dev.jsonl"), encoding="utf-8") as fh:
            for line in fh:
                d = json.loads(line)
                yield str(d["id"]), d.get("claim"), d.get("label")
    elif name == "healthver":
        with open(os.path.join(raw, "healthver_dev.csv"), encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                yield str(r["id"]), r.get("claim"), r.get("label")
    elif name == "averitec":
        for i, d in enumerate(json.load(open(os.path.join(raw, "averitec_dev.json"), encoding="utf-8"))):
            yield "%04d" % (i + 1), d.get("claim"), d.get("label")
    elif name == "pubhealth":
        with zipfile.ZipFile(os.path.join(raw, "pubhealth.zip")) as zp:
            for member in ("PUBHEALTH/dev.tsv", "PUBHEALTH/train.tsv"):
                with zp.open(member) as fh:
                    for r in csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8"), delimiter="\t"):
                        yield str(r["claim_id"]), r.get("claim"), r.get("label")
    elif name == "vitaminc":
        with zipfile.ZipFile(os.path.join(raw, "vitaminc.zip")) as zp:
            for member in ("vitaminc/test.jsonl", "vitaminc/dev.jsonl"):
                with zp.open(member) as fh:
                    for line in io.TextIOWrapper(fh, encoding="utf-8"):
                        d = json.loads(line)
                        yield "%s|%s" % (d.get("unique_id") or d.get("case_id"),
                                         (d.get("page") or "")[:40]), d.get("claim"), d.get("label")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=os.environ.get("BENCH_RAW", DEFAULT_RAW))
    a = ap.parse_args()
    if not os.path.isdir(a.raw):
        print("no benchmark dumps at %s; set BENCH_RAW. The 1,200 samples in the repo are "
              "sampled output, not the dumps, so a second slice cannot be drawn from them." % a.raw)
        return 2

    used = used_texts()
    os.makedirs(OUT_DIR, exist_ok=True)
    summary = {}
    for name, quota in QUOTA.items():
        tpl = template_row(name)
        cand, seen = [], set()
        dropped_used = dropped_label = 0
        for rid, text, raw_label in raw_rows(name, a.raw):
            if raw_label not in MAPS[name] or MAPS[name][raw_label] == "__excluded__":
                dropped_label += 1
                continue
            t = norm(text)
            if not t or t in used:
                dropped_used += 1
                continue
            if t in seen:
                continue
            seen.add(t)
            key = hashlib.sha256(("%s|%s|%s" % (name, rid, t)).encode("utf-8")).hexdigest()
            cand.append((key, rid, t, raw_label))
        cand.sort()
        rows = [base_row(name, tpl, rid, text, label)
                for _, rid, text, label in cand[:quota]]
        out = os.path.join(OUT_DIR, "%s.jsonl" % name)
        with open(out, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
        summary[name] = {"rows": len(rows), "candidates": len(cand),
                         "dropped_used_text": dropped_used, "dropped_label": dropped_label}
        print("[%s] rows=%d candidates=%d dropped_used=%d dropped_label=%d"
              % (name, len(rows), len(cand), dropped_used, dropped_label))

    now = datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat().replace("+00:00", "Z")
    index = {
        "created_at": now,
        "seed_tag": SEED_TAG,
        "raw_dir": a.raw,
        "dataset": "holdout2 (never evaluated)",
        "datasets": {n: {"file": "data/external/samples2/%s.jsonl" % n, "rows": s["rows"],
                         "mapping": MAPS[n]} for n, s in summary.items()},
        "excluded_by_text": "samples 1, data/claims.json, golden set, guard set",
    }
    with open(os.path.join(OUT_DIR, "samples_index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=2, sort_keys=True)

    freeze = {
        "created_at": now,
        "seed_tag": SEED_TAG,
        "rows": {n: s["rows"] for n, s in summary.items()},
        "files": {os.path.relpath(os.path.join(OUT_DIR, f), ROOT).replace("\\", "/"):
                  sha_file(os.path.join(OUT_DIR, f))
                  for f in sorted(os.listdir(OUT_DIR)) if f.endswith(".jsonl")},
        "statement": "this slice has not been evaluated; scoring it once is recorded in "
                     "evidence/holdback_ledger.json and burns it",
        "dedup": {n: {"candidates": s["candidates"],
                      "dropped_used_text": s["dropped_used_text"],
                      "dropped_label": s["dropped_label"]} for n, s in summary.items()},
    }
    with open(os.path.join(OUT_DIR, "freeze.json"), "w", encoding="utf-8") as fh:
        json.dump(freeze, fh, ensure_ascii=False, indent=2, sort_keys=True)
    print("freeze: data/external/samples2/freeze.json  total=%d" % sum(freeze["rows"].values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
