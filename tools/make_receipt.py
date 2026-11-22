"""Write a machine-readable receipt for an acceptance run it actually performs.

Why this exists: `evidence/acceptance_final.json` proves what the gates returned,
but not that the bytes it describes are the bytes on disk, nor which command,
interpreter and exit code produced it. A receipt binds the run to the artefacts by
SHA-256, records the invocation, and gate A37 recomputes every hash, so a receipt
cannot stay green after the code or the data moved.

The script runs `python -m core.audit <tag>` itself rather than copying an old
result file: a receipt must name a run that happened, not one that was reported.
Because the run it performs includes A37, which needs the receipt to exist, the
first receipt of a given tree is written with `--bootstrap`: it is labelled as
such, keeps the real exit code, and is accepted by A37 only in that labelled
state. The receipt shipped with the project is not a bootstrap one.

Usage: python tools/make_receipt.py [run_tag] [--bootstrap]
"""
import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE = os.path.join(ROOT, "evidence")
OUT = os.path.join(EVIDENCE, "run_receipt.json")

ARTEFACTS = [
    # the engine: the receipt is worthless if it attests data but not the code
    # that read it, so every module the verdicts come out of is hashed here
    "core/evidence.py",
    "core/decompose.py",
    "core/pipeline.py",
    "core/audit.py",
    "core/snapshots.py",
    "core/negation.py",
    "core/plan.py",
    "core/citation.py",
    "core/court.py",
    "core/court_batch.py",
    "core/court_live.py",
    "core/llm.py",
    "serve.py",
    # the data the verdicts are computed from
    "data/claims.json",
    "data/golden_set.json",
    "data/guard_set.json",
    "data/citation_cases.json",
    "data/court_cases.json",
    "data/court_batch_cases.json",
    "data/court_replay.json",
    "data/court_batch_replay.json",
    "data/ai_uplift_cases.json",
    "evidence/cards_evidence.jsonl",
    "evidence/paragraphs.jsonl",
    "evidence/court_live.json",
    "evidence/ai_uplift.json",
    # the second implementation the browser runs
    "web/index.html",
    "web/demo.html",
    "web/app.js",
    "web/court.js",
    "web/court_replay.js",
    "web/court_batch_replay.js",
    "tools/js_ui_verify.js",
    "tools/browser_check.py",
    "tools/browser_check_live.py",
    "tools/make_court_screenshots.py",
    "tools/get_model.py",
    "tools/build_court_replay.py",
    "tools/build_court_batch_replay.py",
    "tools/run_ai_uplift.py",
    # documents and screenshots the reviewer actually reads: a stale number
    # should invalidate the receipt the same way stale code does
    "README.md",
    "SUBMISSION.md",
    "COMPETITION_SCORECARD_CN.md",
    "JUDGE_PATH.md",
    "evidence/screenshots/01-judge-path.png",
    "evidence/screenshots/02-real-model-mistake.png",
    "evidence/screenshots/03-accepted-quote.png",
    "evidence/screenshots/04-four-source-conflict.png",
    "evidence/screenshots/05-receipt.png",
    "evidence/screenshots/06-supported.png",
    "evidence/screenshots/07-not-in-source.png",
    "evidence/demo_60s.mp4",
    "evidence/screenshots/23-court-static-ai.png",
    "evidence/screenshots/24-court-struck.png",
    "evidence/screenshots/25-court-live.png",
    "evidence/screenshots/26-court-batch.png",
]

SELF = "A37"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(payload):
    return json.dumps(payload, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def main():
    argv = sys.argv[1:]
    bootstrap = "--bootstrap" in argv
    rest = [a for a in argv if not a.startswith("--")]
    tag = rest[0] if rest else "final"

    command = [sys.executable, "-m", "core.audit", tag]
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    stdout = proc.stdout or ""
    tail = [line for line in stdout.strip().splitlines() if line.strip()][-3:]

    acc_path = os.path.join(EVIDENCE, "acceptance_%s.json" % tag)
    if not os.path.exists(acc_path):
        print("the audit run wrote no acceptance file for tag %s" % tag)
        return 2
    with open(acc_path, "r", encoding="utf-8") as fh:
        acc = json.load(fh)

    gates = acc.get("results") or {}
    checked = {k: v for k, v in gates.items() if not k.startswith(SELF)}
    green = bool(checked) and all(v.get("pass") for v in checked.values())
    others_red = [k for k, v in checked.items() if not v.get("pass")]

    if not green:
        print("refusing to write a receipt: %d of %d attested gates failed (%s)"
              % (len(others_red), len(checked), ", ".join(sorted(others_red))))
        return 3
    if proc.returncode != 0 and not bootstrap:
        failed = [k for k, v in gates.items() if not v.get("pass")]
        if failed != ["A37_run_receipt"]:
            print("refusing to write a receipt for a red run (%s)" % ", ".join(sorted(failed)))
            return 3
        print("the only red gate is A37 itself; re-run with --bootstrap to mint the first receipt")
        return 4

    try:
        node = subprocess.run(["node", "--version"], capture_output=True,
                              text=True, timeout=20).stdout.strip()
    except Exception:
        node = "unavailable"

    payload = {
        "schema": "claim-autopsy/receipt/1",
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "run_tag": tag,
        "command": " ".join([os.path.basename(sys.executable), "-m", "core.audit", tag]),
        "exit_code": proc.returncode,
        "bootstrap": bootstrap,
        "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
        "stdout_tail": tail,
        "python": platform.python_version(),
        "node": node,
        "gates": {
            "passed": sum(1 for v in checked.values() if v.get("pass")),
            "total": len(checked),
            "all_pass": green,
            "run_passed": sum(1 for v in gates.values() if v.get("pass")),
            "run_total": len(gates),
            "note": "the receipt attests the gates it can attest; A37 is the gate that "
                    "checks this receipt, so it is excluded from its own total "
                    "(otherwise no receipt could ever be written). run_passed/run_total "
                    "repeat the whole gate list from that run, including A37 when it is green.",
        },
        "artefacts": {rel: sha256(os.path.join(ROOT, rel)) for rel in ARTEFACTS},
    }
    payload["receipt_id"] = sha256_bytes(canonical(payload))[:32]
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print("wrote evidence/run_receipt.json  id=%s  exit=%d  bootstrap=%s  gates=%d/%d  artefacts=%d"
          % (payload["receipt_id"], payload["exit_code"], bootstrap,
             payload["gates"]["passed"], payload["gates"]["total"], len(payload["artefacts"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
