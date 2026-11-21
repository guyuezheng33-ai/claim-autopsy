"""Input script gate.

The corpus, the anchor rules and every snippet are English. Feeding Chinese
(or any other non-Latin script) into those rules silently produced zero
claims, and a zero-claim result looks exactly like "nothing to check" instead
of "this input cannot be checked". This module makes that state explicit and
explainable, without ever pretending to have produced a verdict.

classify(text) -> one of "english", "cjk", "non_latin", "empty"
"""

import re

CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
LATIN = re.compile(r"[A-Za-z]")

NOTICE = {
    "cjk": (
        "English only — this demo cannot read this input",
        "The text contains CJK (Chinese/Japanese/Korean) characters. The evidence "
        "corpus, the anchor rules and every citation are English, so no claim was "
        "extracted and nothing was verified. Claims: 0 here is not a verdict.",
        "Paste the claim in English, or translate it first. Try one of the English examples.",
    ),
    "non_latin": (
        "English only — this demo cannot read this input",
        "The text has no Latin letters. The corpus and the anchor rules are English, "
        "so nothing could be checked. Claims: 0 here is not a verdict.",
        "Paste the claim in English, or translate it first. Try one of the English examples.",
    ),
    "empty": (
        "Nothing to check",
        "The input is empty, so no claim was extracted.",
        "Paste a declarative claim, e.g. \"Antibiotics cure viral infections.\"",
    ),
    "too_long": (
        "Input too long to check as one claim",
        "The input is longer than the 6000-character budget, so it was not read at "
        "all. A long passage would be split into many claims and would also "
        "multiply the cost of the optional model call. Claims: 0 here is not a verdict.",
        "Paste the single claim you want checked, or one short paragraph at a time.",
    ),
    "no_claim": (
        "No checkable claim found",
        "The text was read, but every fragment was filtered out: questions, "
        "subjective statements and fragments shorter than three words are not "
        "checkable, and the input produced no atomic claim. Claims: 0 here is not a verdict.",
        "Write a full declarative sentence, e.g. \"Antibiotics cure viral infections.\"",
    ),
}


def classify(text):
    """Return the input kind. Conservative: mixed text is English when Latin wins."""
    s = text or ""
    if not s.strip():
        return "empty"
    cjk = len(CJK.findall(s))
    latin = len(LATIN.findall(s))
    if cjk and cjk >= latin:
        return "cjk"
    if latin == 0:
        return "non_latin"
    return "english"


def notice(kind):
    title, body, action = NOTICE.get(kind, NOTICE["no_claim"])
    return {"kind": kind, "title": title, "body": body, "action": action}


def trace(kind, text):
    return {
        "step": "language_gate",
        "input": text,
        "method": "script-detection",
        "output": kind,
        "detail": notice(kind)["body"],
    }
