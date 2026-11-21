#!/usr/bin/env python3
"""Retraction / correction sweep for the 41 sources (Tier 0.3).

The corpus is grey literature: no DOI/PMID exists, so Crossref/OpenAlex work-level
retraction lookups are not applicable. This wrapper runs the page-text marker scan
(retracted / withdrawn / correction / erratum / superseded) and writes
evidence/retractions.jsonl with an explicit `not_indexed` status per source.

    DATASUPPLY_ROOT=/path/to/data-agent python tools/check_retractions.py
"""
import os
import subprocess
import sys

DEFAULT_ROOT = os.environ.get("DATASUPPLY_ROOT", "")


def main():
    root = DEFAULT_ROOT
    if not os.path.isdir(root):
        sys.exit(f"data-supply agent not found at {root}; set DATASUPPLY_ROOT")
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "src"), PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, "-m", "datasupply.claim.retractions"], check=True, env=env)


if __name__ == "__main__":
    main()
