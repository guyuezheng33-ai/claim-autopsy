"""Record a real session against the product engine, and make it replayable.

The product's weak claim is its traction story: PRODUCT.md lists who might pay, and there is no
record of anyone actually using the thing. A testimonial would not fix that - it is unverifiable
prose. A session record can: claim in, verdicts and cited sources out, written with the kernel
and corpus fingerprints of the moment, in a file that `tools/verify_sessions.py` can replay.

Replay is the point. The record does not say "the tool told me X"; it says "with these bytes of
kernel and corpus, this input produced these verdicts citing these sources", and anyone can
re-run the input and see whether that is still what happens. Sessions recorded under an older
kernel are kept as history and checked structurally, because a transcript is a fact about the
past, not a claim about today.

What the record still cannot say is what the person did with the output, which is the only part
of a session that bears on whether anyone would pay for it. So an external operator's session
carries a reviewer block: what they did with the verdicts (used them, threw them out, had to
rephrase, or had no opinion), one sentence of why, and whether they would pay. That block is
the operator's statement, not ours - it is written by the person running the session, and the
audit refuses a customer/reviewer session that lacks it instead of inferring one from silence.

Usage:
  python tools/session_log.py --operator self --channel cli --claim "..." [--claim "..."] [--note "..."]
  python tools/session_log.py --operator customer --claim "..." \
      --reviewer-outcome used --reviewer-note "..." --would-pay unsure
"""
import argparse
import datetime
import hashlib
import json
import os
import platform
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.pipeline import analyze  # noqa: E402

SESS_DIR = os.path.join(ROOT, "evidence", "sessions")
KERNEL_FILES = ("core/evidence.py", "core/decompose.py", "core/pipeline.py",
                "core/adjudicate.py", "core/negation.py", "core/semantic.py",
                "core/snapshots.py")
CORPUS_FILE = "data/claims.json"

OPERATORS = ("self", "customer", "external-reviewer")
REVIEWER_OUTCOMES = ("used", "discarded", "re_prompted", "no_opinion")
WOULD_PAY = ("no", "unsure", "yes")


def sha256_file(rel):
    h = hashlib.sha256()
    with open(os.path.join(ROOT, rel), "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint():
    return {"kernel": {rel: sha256_file(rel) for rel in KERNEL_FILES},
            "corpus_sha256": sha256_file(CORPUS_FILE),
            "python": platform.python_version()}


def canonical(payload):
    return json.dumps(payload, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def turn(text):
    t0 = time.time()
    res = analyze(text, use_llm=False)
    verdicts = []
    for v in res.get("verdicts") or []:
        verdicts.append({
            "claim": v.get("claim"),
            "verdict": v.get("verdict"),
            "sources": sorted(str(c.get("source_id", c.get("card_id")))
                              for c in (v.get("citations") or [])),
            "reason": v.get("reason"),
        })
    out = {"input": text,
           "verdicts": verdicts,
           "claims_detected": len(res.get("claims") or []),
           "unsupported_input": (res.get("unsupported_input") or {}).get("kind"),
           "runtime_ms": int(round((time.time() - t0) * 1000))}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--operator", default="self", choices=OPERATORS)
    ap.add_argument("--channel", default="cli")
    ap.add_argument("--claim", action="append", required=True, dest="claims")
    ap.add_argument("--note", default="")
    ap.add_argument("--reviewer-outcome", default="", choices=("",) + REVIEWER_OUTCOMES)
    ap.add_argument("--reviewer-note", default="",
                    help="one sentence: why the reviewer kept, dropped or rephrased the output")
    ap.add_argument("--would-pay", default="", choices=("",) + WOULD_PAY)
    a = ap.parse_args()

    reviewer = None
    if a.reviewer_outcome:
        if a.operator == "self":
            print("refused: the reviewer block is the external operator's statement, not ours; "
                  "record it with --operator customer or external-reviewer", file=sys.stderr)
            return 2
        if len(a.reviewer_note.strip()) < 10:
            print("refused: --reviewer-note needs one real sentence (>=10 chars) saying what "
                  "the reviewer did with the verdicts", file=sys.stderr)
            return 2
        reviewer = {"outcome": a.reviewer_outcome,
                    "note": a.reviewer_note.strip(),
                    "would_pay": a.would_pay or "unsure"}
    elif a.operator != "self":
        print("refused: a %s session must state what they did with the output; pass "
              "--reviewer-outcome and --reviewer-note" % a.operator, file=sys.stderr)
        return 2

    started = datetime.datetime.now(datetime.timezone.utc)
    body = {
        "schema": "claim-autopsy/session/1",
        "operator": a.operator,
        "channel": a.channel,
        "note": a.note,
        "reviewer": reviewer,
        "started_at": started.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "environment": fingerprint(),
        "turns": [turn(c) for c in a.claims],
    }
    answered = sum(1 for t in body["turns"] for v in t["verdicts"] if v["verdict"] != "undetermined")
    body["summary"] = {
        "inputs": len(body["turns"]),
        "atoms": sum(len(t["verdicts"]) for t in body["turns"]),
        "answered_atoms": answered,
        "undetermined_atoms": sum(1 for t in body["turns"] for v in t["verdicts"]
                                  if v["verdict"] == "undetermined"),
        "no_claim_inputs": sum(1 for t in body["turns"] if t["claims_detected"] == 0),
    }
    body["session_id"] = hashlib.sha256(canonical(body)).hexdigest()[:32]

    os.makedirs(SESS_DIR, exist_ok=True)
    stamp = body["started_at"].replace(":", "-")
    path = os.path.join(SESS_DIR, "%s_%s.json" % (stamp, a.operator))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(body, fh, ensure_ascii=False, indent=2)
    print("wrote %s  id=%s  inputs=%d answered=%d undetermined=%d"
          % (os.path.relpath(path, ROOT), body["session_id"], body["summary"]["inputs"],
             body["summary"]["answered_atoms"], body["summary"]["undetermined_atoms"]))
    if reviewer:
        print("  reviewer: %s / would_pay=%s" % (reviewer["outcome"], reviewer["would_pay"]))
    for t in body["turns"]:
        print("  in : %s" % t["input"])
        for v in t["verdicts"]:
            print("  out: %-12s %s  [%s]" % (v["verdict"], (v["claim"] or "")[:70],
                                             ", ".join(v["sources"]) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
