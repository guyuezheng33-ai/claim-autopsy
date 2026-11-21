r"""Download an optional local model for the court.

The model is NOT committed to the repository. Three Qwen2.5 Instruct GGUF
profiles are supported; the default is 3B because it is the smallest model
that follows the anchor protocol reliably enough for the demo, while still
running on CPU without a key.

Usage:
    python tools/get_model.py                 # 3B, ~1.9 GB
    python tools/get_model.py --size 1.5b     # smaller, faster, weaker
    python tools/get_model.py --size 7b       # stronger, ~4.4 GB, slow on CPU
    python tools/get_model.py --dest D:\models
"""
import argparse
import os
import sys
import urllib.request

PROFILES = {
    "1.5b": {
        "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "url": ("https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/"
                "qwen2.5-1.5b-instruct-q4_k_m.gguf?download=true"),
        "min_bytes": 100 * 1024 * 1024,
    },
    "3b": {
        "model": "qwen2.5-3b-instruct-q4_k_m.gguf",
        "url": ("https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/"
                "qwen2.5-3b-instruct-q4_k_m.gguf?download=true"),
        "min_bytes": 1000 * 1024 * 1024,
    },
    "7b": {
        "model": "qwen2.5-7b-instruct-q4_k_m.gguf",
        "url": ("https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/"
                "qwen2.5-7b-instruct-q4_k_m.gguf?download=true"),
        "min_bytes": 3000 * 1024 * 1024,
    },
}


def default_dest():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.cache")
    return os.path.join(base, "claim-autopsy", "models")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="3b", choices=sorted(PROFILES))
    ap.add_argument("--dest", default=default_dest())
    args = ap.parse_args()
    profile = PROFILES[args.size]
    os.makedirs(args.dest, exist_ok=True)
    out = os.path.join(args.dest, profile["model"])
    if os.path.isfile(out) and os.path.getsize(out) > profile["min_bytes"]:
        print("already present: %s" % out)
        return 0
    tmp = out + ".part"
    print("downloading %s" % profile["url"])
    print("target: %s" % out)

    def hook(blocks, block_size, total):
        done = blocks * block_size
        if total > 0:
            pct = min(100, int(done * 100 / total))
            sys.stdout.write("\r%3d%%  %.2f / %.2f GB" % (pct, done / 1e9, total / 1e9))
            sys.stdout.flush()

    urllib.request.urlretrieve(profile["url"], tmp, hook)
    print()
    if os.path.getsize(tmp) < profile["min_bytes"]:
        os.remove(tmp)
        print("download too small; refusing to install", file=sys.stderr)
        return 1
    os.replace(tmp, out)
    print("installed: %s" % out)
    print("start the demo with: python serve.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
