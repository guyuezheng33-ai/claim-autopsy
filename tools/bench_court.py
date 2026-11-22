"""Reproducible latency benchmark for the deterministic court.

Run from the product root:

    python tools/bench_court.py

It measures `make_dossier` on two fixed cases, writes `data/bench_court.csv`,
and never touches the verdict fixtures.
"""

import csv
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.court import make_dossier  # noqa: E402

CASES = [
    (
        "supported_short",
        "The vaccine does not contain live virus.",
        "The vaccine does not contain live virus.",
    ),
    (
        "refuted_short",
        "Getting a flu vaccine gives you the flu.",
        "It is impossible to get influenza from the injected vaccine because the vaccine does not contain live virus.",
    ),
]
RUNS = 40
OUT = ROOT / "eval" / "bench_court.csv"


def measure(claim, source, runs=RUNS):
    samples = []
    for _ in range(runs):
        started = time.perf_counter()
        make_dossier(claim, source, "benchmark source")
        samples.append((time.perf_counter() - started) * 1000)
    samples.sort()
    p95 = samples[min(len(samples) - 1, int(len(samples) * 0.95))]
    return round(statistics.median(samples), 2), round(p95, 2)


def main():
    rows = []
    for name, claim, source in CASES:
        median, p95 = measure(claim, source)
        rows.append({"case": name, "runs": RUNS, "median_ms": median, "p95_ms": p95})
        print("%s: median %.2f ms, p95 %.2f ms (%d runs)" % (name, median, p95, RUNS))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["case", "runs", "median_ms", "p95_ms"])
        writer.writeheader()
        writer.writerows(rows)
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
