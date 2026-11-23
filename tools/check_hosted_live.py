#!/usr/bin/env python3
"""Verify the public hosted endpoint from outside the browser.

Usage:
    python tools/check_hosted_live.py
    python tools/check_hosted_live.py --base https://your-space.hf.space --write

The check is deliberately black-box: HTTP status, CORS preflight, an actual
Qwen2.5-3B trial, and the receipt model name. It never reads local model files
and never trusts the page's own badge.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BASE = "https://bali-drive-install-hiking.trycloudflare.com"
PAGE = "https://guyuezheng33-ai.github.io/claim-autopsy/web/index.html"
CLAIM = "Venus is the hottest planet in the Solar System."
SOURCE = ("Venus has the highest mean surface temperature of any planet in the "
          "Solar System.")
ORIGIN = "https://guyuezheng33-ai.github.io"


def request(url, method="GET", body=None, headers=None, timeout=120):
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Origin", ORIGIN)
    req.add_header("User-Agent", "claim-autopsy-hosted-check/1.0")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            return response.status, dict(response.headers), raw, time.time() - started
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, dict(exc.headers), raw, time.time() - started


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=os.environ.get("CLAIM_HOSTED_API", DEFAULT_BASE))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    base = args.base.rstrip("/")

    failures = []
    status_code, status_headers, raw, status_seconds = request(
        base + "/api/status", timeout=20)
    status = json.loads(raw) if raw else {}
    if status_code != 200:
        failures.append("status_http_%s" % status_code)
    if not status.get("model_live"):
        failures.append("model_not_live")
    if not status.get("hosted"):
        failures.append("not_hosted_mode")
    model = status.get("model") or ""
    if "qwen2.5-3b" not in model:
        failures.append("model_not_qwen_3b:%s" % model)

    options_code, options_headers, _, _ = request(
        base + "/api/trial_stream",
        method="OPTIONS",
        headers={
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
        timeout=20,
    )
    allow_origin = (options_headers.get("Access-Control-Allow-Origin") or
                    options_headers.get("access-control-allow-origin") or "")
    allow_methods = (options_headers.get("Access-Control-Allow-Methods") or
                     options_headers.get("access-control-allow-methods") or "")
    if options_code != 204:
        failures.append("preflight_http_%s" % options_code)
    if allow_origin != "*":
        failures.append("preflight_origin:%s" % allow_origin)
    if "POST" not in allow_methods.upper():
        failures.append("preflight_methods:%s" % allow_methods)

    trial_code, _, raw_trial, trial_seconds = request(
        base + "/api/trial_stream",
        method="POST",
        body={"claim": CLAIM, "source": SOURCE, "live": True},
        timeout=args.timeout,
    )
    payload = None
    if trial_code == 200:
        for line in raw_trial.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "result":
                payload = event.get("payload")
                break
    if trial_code != 200:
        failures.append("trial_http_%s" % trial_code)
    if not payload:
        failures.append("trial_no_result_event")
        payload = {}
    if payload.get("error"):
        failures.append("trial_error:%s" % payload["error"])
    receipt = payload.get("receipt") or {}
    trial_model = receipt.get("model") or ""
    if "qwen2.5-3b" not in trial_model:
        failures.append("trial_model:%s" % trial_model)
    summary = payload.get("summary") or {}
    if not summary.get("claims"):
        failures.append("trial_no_claims")

    artifact = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "public_page": PAGE,
        "endpoint": base,
        "origin_header": ORIGIN,
        "status": {
            "http": status_code,
            "seconds": round(status_seconds, 3),
            "hosted": status.get("hosted"),
            "model_live": status.get("model_live"),
            "mode": status.get("mode"),
            "model": model,
        },
        "cors_preflight": {
            "http": options_code,
            "allow_origin": allow_origin,
            "allow_methods": allow_methods,
        },
        "trial": {
            "http": trial_code,
            "seconds": round(trial_seconds, 3),
            "claim": CLAIM,
            "source_sha256": hashlib.sha256(SOURCE.encode("utf-8")).hexdigest(),
            "run_id": receipt.get("run_id"),
            "model": trial_model,
            "engine": receipt.get("engine"),
            "verdict": ((payload.get("atoms") or [{}])[0] or {}).get("verdict"),
            "summary": summary,
            "ai_available": payload.get("ai_available"),
            "ai_meta": payload.get("ai_meta"),
        },
        "failures": failures,
        "pass": not failures,
    }

    print(json.dumps(artifact, ensure_ascii=False, indent=2))
    if args.write:
        target = os.path.join(ROOT, "evidence", "hosted_live.json")
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(artifact, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print("wrote %s" % target, file=sys.stderr)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
