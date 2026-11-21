"""Negation / polarity detection (Q10, A16).

A claim whose polarity is inverted must never inherit the stance of its
affirmative form. "The Earth is not round" is the opposite of "The Earth is
round", so a supporting card must become a refuting signal. This module:

1. detects English negation markers,
2. strips them to build an affirmative query for retrieval,
3. tells the adjudicator to invert evidence stance before scoring.

Double negation is deliberately conservative: it returns `undetermined`
rather than guessing what the speaker meant.
"""
import re

EN_NEG = [
    r"\bcannot\b", r"\bcan not\b", r"\bcan't\b",
    r"\bwill not\b", r"\bwon't\b",
    r"\bdoes not\b", r"\bdoesn't\b",
    r"\bdo not\b", r"\bdon't\b",
    r"\bdid not\b", r"\bdidn't\b",
    r"\bis not\b", r"\bisn't\b",
    r"\bare not\b", r"\baren't\b",
    r"\bwas not\b", r"\bwasn't\b",
    r"\bwere not\b", r"\bweren't\b",
    r"\bnever\b", r"\bnot\b", r"\bno\b",
]


def detect(text):
    """Return polarity metadata for one atomic claim.

    Keys: original, normalized, markers, count, flip, uncertain.
    `normalized` drops the negation marker so retrieval sees the affirmative
    proposition, which is the form stored in the evidence cards.

    A prohibition ("not recommended", "not allowed") is masked first: it is a
    single lexicalised predicate, not the logical negation of its positive form.
    Treating it as a negation inverted the evidence, so a card stating that a
    dose exceeds the safe upper limit was scored as evidence *against* the claim
    that the dose is not recommended.
    """
    s = text or ""
    masked = re.sub(r"\bnot[ \t]+(?=(recommended|advised|allowed|permitted|approved)\b)",
                    "\u0001", s, flags=re.IGNORECASE)
    out = masked
    markers = []
    # Longest first: consume "is not" before the standalone "not".
    for pat in sorted(EN_NEG, key=len, reverse=True):
        def repl(m):
            markers.append(m.group(0))
            return " "
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    normalized = re.sub(r"\s+", " ", out.replace("\u0001", " ")).strip()
    count = len(markers)
    return {
        "original": s,
        "normalized": normalized or s,
        "markers": markers,
        "count": count,
        "flip": count == 1,
        "uncertain": count >= 2,
    }
