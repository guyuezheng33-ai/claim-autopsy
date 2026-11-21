#!/usr/bin/env python3
"""Fetch the public claim-verification benchmarks (Tier 0.1).

Thin wrapper: the download logic lives in the data-supply agent so the same code
paths are versioned there. Set DATASUPPLY_ROOT if the agent tree is elsewhere.

    DATASUPPLY_ROOT=/path/to/data-agent python tools/fetch_benchmarks.py
"""
import os
import subprocess
import sys

DEFAULT_ROOT = os.environ.get("DATASUPPLY_ROOT", "")


def main():
    root = DEFAULT_ROOT
    script = os.path.join(root, "tools", "download_benchmarks.py")
    if not os.path.isdir(root):
        sys.exit(f"data-supply agent not found at {root}; set DATASUPPLY_ROOT")
    if not os.path.isfile(script):
        sys.exit(f"missing {script}")
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "src"), PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, script], check=True, env=env)


if __name__ == "__main__":
    main()
