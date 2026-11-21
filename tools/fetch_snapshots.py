#!/usr/bin/env python3
"""Fetch the 41 paragraph-level evidence snapshots (Tier 0.2).

Wraps the data-supply agent's polite fetcher (2 s delay, robots.txt, UA, Wayback
fallback for 403 pages). Raw HTML lands in the agent tree; this repo keeps the
paragraph rows plus hashes.

    DATASUPPLY_ROOT=/path/to/data-agent python tools/fetch_snapshots.py
"""
import os
import subprocess
import sys

DEFAULT_ROOT = os.environ.get("DATASUPPLY_ROOT", "")


def main():
    root = DEFAULT_ROOT
    script = os.path.join(root, "tools", "run_claim_snapshots.py")
    if not os.path.isdir(root):
        sys.exit(f"data-supply agent not found at {root}; set DATASUPPLY_ROOT")
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "src"), PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, script], check=True, env=env)


if __name__ == "__main__":
    main()
