"""Census of benchmark labels that contradict themselves.

HealthVer labels a claim against the evidence sentence that came with it, not against the
claim alone, so the same sentence can arrive labelled Supports and Refutes in the same split.
That matters here for one reason: a claim-level accuracy number computed on such a file is
partly a number about the file, not about the tool, and a "wrong" verdict may be a verdict
against a label that half the file contradicts.

This tool counts it, twice: on the 1,200 committed samples (every split), which is always
available, and on the raw HealthVer dev file when the downloads directory is supplied via
--raw or BENCH_RAW, which is what turns a sampled duplicate into a census.

Usage: python tools/check_label_noise.py [--raw DIR]
"""
import argparse
import collections
import datetime
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(ROOT, "data", "external", "samples")
OUT = os.path.join(ROOT, "evidence", "label_conflicts.json")
DATASETS = ("fever", "healthver", "averitec", "pubhealth", "vitaminc")


def norm(text):
    return " ".join((text or "").replace("\xa0", " ").split()).strip().lower()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def census(pairs):
    """pairs: list of (normalized_text, label, id, slice). Returns the conflict census."""
    groups = collections.defaultdict(list)
    for text, label, rid, slice_name in pairs:
        if text:
            groups[text].append((label, rid, slice_name))
    conflicting = {}
    for text, rows in groups.items():
        labels = collections.Counter(lab for lab, _, _ in rows)
        if len(labels) > 1:
            conflicting[text] = {
                "labels": dict(sorted(labels.items())),
                "ids": [rid for _, rid, _ in rows],
                "slices": sorted({s for _, _, s in rows}),
            }
    return {
        "rows": len(pairs),
        "distinct": len(groups),
        "conflicting_groups": len(conflicting),
        "rows_in_conflicting_groups": sum(len(groups[t]) for t in conflicting),
        "conflicts": dict(sorted(conflicting.items())),
    }


def samples_census():
    pairs = []
    for name in DATASETS:
        path = os.path.join(SAMPLES, "%s.jsonl" % name)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                pairs.append((norm(r["text"]), r["gold"], r["id"], r["split"]))
    return census(pairs)


def raw_healthver(raw_dir):
    path = os.path.join(raw_dir, "healthver_dev.csv")
    if not os.path.exists(path):
        return None
    import csv
    pairs = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            pairs.append((norm(r.get("claim")), (r.get("label") or "").strip(), r.get("id"), "dev"))
    body = census(pairs)
    body["file"] = "healthver_dev.csv"
    body["sha256"] = sha256_file(path)
    body["note"] = ("label counts per claim text, computed over the raw dev split; this is the "
                    "census the sample was drawn from, not a re-scoring of it")
    return body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=os.environ.get("BENCH_RAW") or "")
    a = ap.parse_args()

    payload = {
        "schema": "claim-autopsy/label-conflicts/1",
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "samples": samples_census(),
        "raw_healthver": raw_healthver(a.raw) if a.raw else None,
        "reading": ("A group is a normalized claim text that arrives with more than one gold "
                    "label. On such a text, a claim-level accuracy number cannot be right for "
                    "every row, and a single wrong verdict may be a verdict against a label the "
                    "file contradicts elsewhere."),
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    s = payload["samples"]
    print("samples: %d rows / %d distinct / %d conflicting / %d rows in conflicts"
          % (s["rows"], s["distinct"], s["conflicting_groups"], s["rows_in_conflicting_groups"]))
    r = payload["raw_healthver"]
    if r:
        print("raw healthver dev: %d rows / %d distinct / %d conflicting / %d rows in conflicts"
              % (r["rows"], r["distinct"], r["conflicting_groups"], r["rows_in_conflicting_groups"]))
    else:
        print("raw healthver: not available (pass --raw DIR or set BENCH_RAW)")
    print("out:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
