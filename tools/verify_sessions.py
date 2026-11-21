"""Replay every recorded session and say whether it still holds.

A session file is evidence only if it can be checked. This tool re-runs each recorded input
through the current engine and compares the verdicts, the atom boundaries and the cited source
ids against what the file claims. Sessions recorded under the current kernel and corpus must
match exactly; sessions recorded under an older kernel are history, and are checked structurally
with the difference stated rather than silently accepted.

`core/audit.py` gate A40 calls `verify_all()` and lists its findings, so a session that cannot
be replayed fails the build instead of sitting in the repo as a nice story.

Usage: python tools/verify_sessions.py [--json]
"""
import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools.session_log import fingerprint, KERNEL_FILES  # noqa: E402
from core.pipeline import analyze  # noqa: E402

SESS_DIR = os.path.join(ROOT, "evidence", "sessions")
REQUIRED = ("schema", "operator", "channel", "started_at", "environment", "turns", "summary")
REVIEWER_OUTCOMES = ("used", "discarded", "re_prompted", "no_opinion")
WOULD_PAY = ("no", "unsure", "yes")
EXTERNAL_OPERATORS = ("customer", "external-reviewer")


def check_reviewer(s):
    """The reviewer block is what the operator did with the output. Ours cannot stand in."""
    bad = []
    operator = s.get("operator")
    rev = s.get("reviewer")
    if operator in EXTERNAL_OPERATORS:
        if not isinstance(rev, dict):
            bad.append("external_session_missing_reviewer")
            return bad
        if rev.get("outcome") not in REVIEWER_OUTCOMES:
            bad.append("reviewer_outcome:%s" % rev.get("outcome"))
        if len(str(rev.get("note") or "").strip()) < 10:
            bad.append("reviewer_note_too_short")
        if rev.get("would_pay") not in WOULD_PAY:
            bad.append("reviewer_would_pay:%s" % rev.get("would_pay"))
    elif rev is not None:
        bad.append("self_session_has_reviewer")
    return bad


def canonical(payload):
    return json.dumps(payload, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def replay_turn(text):
    res = analyze(text, use_llm=False)
    verdicts = []
    for v in res.get("verdicts") or []:
        verdicts.append({
            "claim": v.get("claim"),
            "verdict": v.get("verdict"),
            "sources": sorted(str(c.get("source_id", c.get("card_id")))
                              for c in (v.get("citations") or [])),
        })
    return verdicts


def verify_one(path):
    with open(path, "r", encoding="utf-8") as fh:
        s = json.load(fh)
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    bad = []
    for k in REQUIRED:
        if k not in s:
            bad.append("missing_field:%s" % k)
    body = {k: v for k, v in s.items() if k != "session_id"}
    want = hashlib.sha256(canonical(body)).hexdigest()[:32]
    if want != s.get("session_id"):
        bad.append("session_id_mismatch")

    env = s.get("environment") or {}
    now = fingerprint()
    same_kernel = (env.get("kernel") == now["kernel"]
                   and env.get("corpus_sha256") == now["corpus_sha256"])
    status = "replay_match" if same_kernel else "historical"

    for i, t in enumerate(s.get("turns") or []):
        if not t.get("input"):
            bad.append("turn_%d_no_input" % i)
            continue
        got = replay_turn(t["input"])
        rec = [{"claim": v.get("claim"), "verdict": v.get("verdict"),
                "sources": list(v.get("sources") or [])} for v in (t.get("verdicts") or [])]
        if same_kernel:
            if len(got) != len(rec):
                bad.append("turn_%d_atom_count:%d!=%d" % (i, len(got), len(rec)))
                continue
            for a, b in zip(got, rec):
                if a["claim"] != b["claim"]:
                    bad.append("turn_%d_claim_differs" % i)
                if a["verdict"] != b["verdict"]:
                    bad.append("turn_%d_verdict:%s!=%s" % (i, b["verdict"], a["verdict"]))
                if a["sources"] != b["sources"]:
                    bad.append("turn_%d_sources:%s!=%s" % (i, b["sources"], a["sources"]))
        else:
            # History: the words still have to be a well-formed record, but the verdicts belong
            # to the kernel named inside the file, not to today's. Say which one.
            for v in rec:
                if v["verdict"] not in ("supported", "refuted", "undetermined"):
                    bad.append("turn_%d_bad_verdict:%s" % (i, v["verdict"]))

    if not same_kernel and status == "historical":
        if env.get("kernel") != now["kernel"]:
            status = "historical:kernel_changed"
        else:
            status = "historical:corpus_changed"

    if (s.get("summary") or {}).get("inputs") != len(s.get("turns") or []):
        bad.append("summary_inputs_mismatch")

    bad.extend(check_reviewer(s))

    rev = s.get("reviewer") if isinstance(s.get("reviewer"), dict) else {}
    return {"file": rel, "session_id": s.get("session_id"), "operator": s.get("operator"),
            "channel": s.get("channel"), "status": status, "bad": bad[:6],
            "reviewer_outcome": rev.get("outcome"), "would_pay": rev.get("would_pay"),
            "bad_count": len(bad)}


def verify_all():
    files = []
    if os.path.isdir(SESS_DIR):
        files = sorted(os.path.join(SESS_DIR, f) for f in os.listdir(SESS_DIR)
                       if f.endswith(".json") and not f.startswith("_"))
    out = [verify_one(p) for p in files]
    external = [x for x in out if x.get("operator") in EXTERNAL_OPERATORS]
    bad = [x for x in out if x["bad"]]
    outcomes = {}
    for x in out:
        if x.get("reviewer_outcome"):
            outcomes[x["reviewer_outcome"]] = outcomes.get(x["reviewer_outcome"], 0) + 1
    return {"files": len(out), "sessions": out,
            "external_operators": len(external),
            "reviewer_outcomes": outcomes,
            "paid_yes": sum(1 for x in out if x.get("would_pay") == "yes"),
            "bad": bad,
            "note": "a session recorded under an older kernel is history; it is checked "
                    "structurally and labelled, not replayed against today's verdicts"}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--json", action="store_true")
    args = a.parse_args()
    res = verify_all()
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0 if not res["bad"] else 1
    print("%d session(s), %d by an external operator; reviewer outcomes: %s"
          % (res["files"], res["external_operators"],
             res["reviewer_outcomes"] or "none recorded"))
    for s in res["sessions"]:
        print("  %-38s %-10s %-22s %s" % (s["file"], s["operator"], s["status"],
                                          ", ".join(s["bad"]) or "ok"))
    return 0 if not res["bad"] else 1


if __name__ == "__main__":
    sys.exit(main())
