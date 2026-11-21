"""Walk one external reviewer through three claims and record what they did.

The audit can prove a session replayed; it cannot prove anyone used the output.
That is the reviewer block's job, and it has to be the reviewer's words, typed
while they are in front of the screen. This tool is the shortest path to that:
three fixed claims for one named scenario (a paper abstract, a news brief or a
customer-service reply), one refuted, one supported, one refused, with their real
verdicts and citations, then four questions.

Usage:
  python tools/run_external_session.py                        # interactive, writes a session
  python tools/run_external_session.py --scenario news        # same protocol, different claims
  python tools/run_external_session.py --rehearse             # canned answers, writes nothing
  python tools/run_external_session.py --out-dir DIR          # write somewhere other than evidence/sessions

The claims are fixed per scenario so that sessions are comparable, and so that
the refusal case is included on purpose: a reviewer who only sees agreements
never tests the part this product is built around.
"""
import argparse
import datetime
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import session_log  # noqa: E402

SCENARIOS = {
    "paper": (
        "checking a science-paper abstract",
        [
            ("Getting a flu vaccine gives you the flu.", "refuted",
             "The vaccine cannot give you the flu; the citation is a CDC page on vaccine safety."),
            ("A common cold can resolve on its own.", "supported",
             "A common cold usually clears without treatment; the citation is a public health page."),
            ("Coffee causes cancer in children.", "undetermined",
             "The corpus has a coffee-and-cancer card, but it is about adults; the guard refuses "
             "rather than narrowing an adult card onto children."),
        ],
    ),
    "news": (
        "checking a news brief",
        [
            ("Cold weather kills the coronavirus.", "refuted",
             "A WHO myth-buster refutes it directly; the citation carries an archived paragraph."),
            ("The Earth is round.", "supported",
             "A NASA explainer supports it; the citation is not a topic label."),
            ("Vitamin C cures the flu.", "undetermined",
             "The corpus has vitamin C and flu cards, but none asserts a cure; the refusal names "
             "the endpoint mismatch."),
        ],
    ),
    "script": (
        "checking a customer-service reply",
        [
            ("Antibiotics can treat a common cold.", "refuted",
             "A CDC antibiotics page refutes it: colds are viral and antibiotics do not work on viruses."),
            ("Antibiotics cause side effects.", "supported",
             "A CDC page states the side effects; the stance is read from the card."),
            ("Coffee stunts growth in teenagers.", "undetermined",
             "The closest card is about coffee and cancer in adults; the guard refuses on population "
             "and topic grounds instead of borrowing it."),
        ],
    ),
}
OUTCOMES = {
    "1": "used",
    "2": "discarded",
    "3": "re_prompted",
    "4": "no_opinion",
}
PAY = {"1": "no", "2": "unsure", "3": "yes"}


def show(text, want):
    res = session_log.turn(text)
    print("\n%s" % ("-" * 72))
    print("CLAIM : %s" % text)
    if not res["verdicts"]:
        print("RESULT: not checkable (%s)" % (res.get("unsupported_input") or "no claim"))
        return res
    for v in res["verdicts"]:
        print("VERDICT: %s" % v["verdict"].upper())
        print("ATOM   : %s" % v["claim"])
        print("SOURCES: %s" % (", ".join(v["sources"]) or "none cited"))
        print("WHY    : %s" % (v.get("reason") or ""))
    print("(expected on this kernel: %s)" % want)
    return res


def ask(prompt, options, allow_blank=False):
    while True:
        print(prompt)
        for key, val in options.items():
            print("  [%s] %s" % (key, val))
        raw = input("> ").strip()
        if not raw and allow_blank:
            return ""
        if raw in options:
            return options[raw]
        print("Please answer with one of: %s" % ", ".join(options.keys()))


def build(operator, channel, turns, reviewer, note):
    started = datetime.datetime.now(datetime.timezone.utc)
    body = {
        "schema": "claim-autopsy/session/1",
        "operator": operator,
        "channel": channel,
        "note": note,
        "reviewer": reviewer,
        "started_at": started.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "environment": session_log.fingerprint(),
        "turns": turns,
    }
    answered = sum(1 for t in body["turns"] for v in t["verdicts"]
                   if v["verdict"] != "undetermined")
    body["summary"] = {
        "inputs": len(body["turns"]),
        "atoms": sum(len(t["verdicts"]) for t in body["turns"]),
        "answered_atoms": answered,
        "undetermined_atoms": sum(1 for t in body["turns"] for v in t["verdicts"]
                                  if v["verdict"] == "undetermined"),
        "no_claim_inputs": sum(1 for t in body["turns"] if t["claims_detected"] == 0),
    }
    body["session_id"] = hashlib.sha256(session_log.canonical(body)).hexdigest()[:32]
    return body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--operator", default="external-reviewer",
                    choices=("external-reviewer", "customer"))
    ap.add_argument("--channel", default="in-person")
    ap.add_argument("--out-dir", default=session_log.SESS_DIR)
    ap.add_argument("--scenario", default="paper", choices=tuple(SCENARIOS),
                    help="which three-claim pack to walk: paper, news or customer-service script")
    ap.add_argument("--rehearse", action="store_true",
                    help="canned answers, print only, never writes a session file")
    a = ap.parse_args()

    label, claims = SCENARIOS[a.scenario]
    note = "guided three-claim session (%s): one refuted, one supported, one refused" % label
    turns = [show(text, want) for text, want, _why in claims]

    if a.rehearse:
        reviewer = {"outcome": "used", "note": "Rehearsal only: the tool walked the three cases "
                    "and the recording path is exercised without writing a file.",
                    "would_pay": "unsure"}
        body = build(a.operator, a.channel + "-rehearsal", turns, reviewer, note)
        print("\n" + json.dumps(body, ensure_ascii=False, indent=2)[:1200] + "\n...")
        print("rehearsal: no file written; session_id=%s" % body["session_id"])
        return 0

    print("\n" + "=" * 72)
    print("Now the part the audit cannot infer: what did you do with these verdicts?")
    outcome = ask("Did you keep, drop or rephrase anything the tool said?",
                  OUTCOMES)
    note = ""
    while len(note) < 10:
        note = input("One sentence: why? (>=10 characters)\n> ").strip()
        if len(note) < 10:
            print("A sentence is required; silence is not a data point.")
    pay = ask("Would you pay for this as it stands?", PAY)

    reviewer = {"outcome": outcome, "note": note, "would_pay": pay}
    body = build(a.operator, a.channel, turns, reviewer, note)
    os.makedirs(a.out_dir, exist_ok=True)
    stamp = body["started_at"].replace(":", "-")
    path = os.path.join(a.out_dir, "%s_%s.json" % (stamp, a.operator))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(body, fh, ensure_ascii=False, indent=2)
    print("\nwrote %s" % os.path.relpath(path, ROOT))
    print("session_id=%s  reviewer=%s  would_pay=%s"
          % (body["session_id"], outcome, pay))
    print("Next: python tools/verify_sessions.py --json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
