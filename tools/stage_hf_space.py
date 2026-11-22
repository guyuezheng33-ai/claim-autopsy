"""Stage the runtime-only payload for a Hugging Face Docker Space.

The competition repo is not the Space repo. This copies exactly what serve.py
needs at runtime, swaps in the HF Dockerfile, and leaves the local model files
and screenshots out of the upload.

Usage:
    python tools/stage_hf_space.py
    python tools/stage_hf_space.py --out C:\\path\\to\\stage
"""
import argparse
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HF = os.path.join(ROOT, "deploy", "hf-space")
DEFAULT_OUT = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                           "claim-autopsy", "hf-space-stage")
SKIP_DIRS = {"__pycache__", ".pytest_cache", "models", ".git"}
SKIP_EVIDENCE = {"screenshots", "demo_60s.mp4", "local_llm.log", "ai_uplift_live_run.log"}


def _ignore(dirname, names):
    out = []
    for name in names:
        if name in SKIP_DIRS:
            out.append(name)
            continue
        if os.path.basename(dirname) == "evidence" and name in SKIP_EVIDENCE:
            out.append(name)
    return out


def _copy_tree(src, dst):
    if not os.path.exists(src):
        raise SystemExit("missing source: %s" % src)
    shutil.copytree(src, dst, ignore=_ignore)


def stage(out):
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)

    shutil.copy2(os.path.join(ROOT, "serve.py"), os.path.join(out, "serve.py"))
    for name in ("core", "web", "data", "evidence"):
        _copy_tree(os.path.join(ROOT, name), os.path.join(out, name))

    shutil.copy2(os.path.join(HF, "Dockerfile"), os.path.join(out, "Dockerfile"))
    shutil.copy2(os.path.join(HF, "start.sh"), os.path.join(out, "start.sh"))
    shutil.copy2(os.path.join(HF, "README.md"), os.path.join(out, "README.md"))

    with open(os.path.join(out, ".dockerignore"), "w", encoding="utf-8") as f:
        f.write("models/\n__pycache__/\n*.pyc\n.git/\n.pytest_cache/\n")

    # A Space must never accidentally upload a local 2 GB model.
    for dirpath, _dirnames, filenames in os.walk(out):
        for filename in filenames:
            if filename.endswith(".gguf"):
                raise SystemExit("refusing to stage model file: %s" % os.path.join(dirpath, filename))

    total = sum(os.path.getsize(os.path.join(dp, f))
                for dp, _dn, fs in os.walk(out) for f in fs)
    print("staged %s | %.1f MB" % (out, total / (1024 * 1024)))
    print("files=%d" % sum(len(fs) for _dp, _dn, fs in os.walk(out)))
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()
    stage(os.path.abspath(args.out))
