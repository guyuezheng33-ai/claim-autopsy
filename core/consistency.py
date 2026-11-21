"""Cross-atom consistency (v14).

A submission can contain two atoms that cannot both be true. Judging each atom
against the corpus is correct, but presenting the two verdicts side by side
without saying they are mutually exclusive invites the reader to average them
("one said yes, one said no, so the answer is maybe"). This module finds such
pairs and labels them, so the report states the conflict instead of hiding it.

Three bases are detected, each requires shared subject matter:

* negation asymmetry - one atom carries a negation marker, the other does not,
  and the rest of their words agree ("Flu vaccines are safe" / "... are not safe").
* antonym predicate - both atoms use opposite predicates of the same pair
  ("The Earth is round" / "The Earth is flat").
* opposite relation - one atom asserts a cause-like relation, the other a
  prevention-like relation, over the same subject ("Coffee causes cancer" /
  "Coffee prevents cancer").

Known synonyms are folded first, so "round" and "spherical" never look like a
conflict. The module is advisory: it never changes a verdict, it only adds a
`relations` list to the report.
"""
import re

from . import negation
from .evidence import STOP_WORDS, relation_classes, RELATION_WORDS, HARM_WORDS, primary_relation

REL_PHRASE_KEYS = dict(RELATION_WORDS)
REL_PHRASE_KEYS["harm"] = HARM_WORDS

# Predicate pairs that cannot both hold of the same subject.
ANTONYM_PAIRS = [
    ("round", "flat"), ("spherical", "flat"),
    ("safe", "unsafe"), ("safe", "dangerous"), ("safe", "harmful"),
    ("effective", "useless"), ("effective", "ineffective"),
    ("true", "false"), ("increase", "decrease"), ("rise", "fall"),
    ("prevent", "cause"),
]

# Words that mean the same thing for conflict detection purposes.
SYNONYMS = {
    "spherical": "round", "globe": "earth", "world": "earth",
    "jab": "vaccine", "shot": "vaccine", "immunisation": "vaccination",
    "immunization": "vaccination", "sanitiser": "sanitizer",
    "handwashing": "hand", "wash": "washing",
}

# Relations that point in opposite directions.
OPPOSED_RELATIONS = [("cause", "prevent"), ("cause", "cure"), ("harm", "prevent")]


def _tokens(text):
    s = (text or "").lower()
    s = re.sub(r"[^a-z0-9\s']", " ", s)
    out = []
    for t in s.split():
        t = t.strip("'")
        if not t or t in STOP_WORDS:
            continue
        out.append(SYNONYMS.get(t, t))
    return out


def _content(text):
    return set(_tokens(text))


def _antonym_hit(a, b):
    """Return the pair that a and b disagree on, if any."""
    for x, y in ANTONYM_PAIRS:
        x, y = SYNONYMS.get(x, x), SYNONYMS.get(y, y)
        if (x in a and y in b) or (y in a and x in b):
            return (x, y)
    return None


def _relation_flip(a_text, b_text):
    ra, rb = relation_classes(a_text), relation_classes(b_text)
    for x, y in OPPOSED_RELATIONS:
        if (x in ra and y in rb) or (y in ra and x in rb):
            return (x, y)
    return None


def compare(a_text, b_text):
    """Compare two atoms. Returns a dict with `conflict` bool and `basis`."""
    a, b = _content(a_text), _content(b_text)
    if not a or not b:
        return {"conflict": False, "basis": None, "shared": []}
    shared = sorted(a & b)
    # Guard against deciding a conflict on a single generic word.
    if len(shared) < 1 or len(shared) < min(len(a), len(b)) * 0.5:
        return {"conflict": False, "basis": None, "shared": shared}

    pair = _antonym_hit(a, b)
    if pair:
        rest_a = a - set(pair)
        rest_b = b - set(pair)
        if rest_a & rest_b:
            return {"conflict": True, "basis": "antonym:%s/%s" % pair, "shared": shared}

    flip = _relation_flip(a_text, b_text)
    if flip:
        return {"conflict": True, "basis": "opposite_relation:%s/%s" % flip, "shared": shared}

    na, nb = negation.detect(a_text)["count"], negation.detect(b_text)["count"]
    if (na % 2) != (nb % 2):
        return {"conflict": True, "basis": "negation", "shared": shared}

    return {"conflict": False, "basis": None, "shared": shared}


CHAIN_RELATIONS = {
    ("cause", "cause"): "cause",
    ("prevent", "cause"): "prevent",
    ("cause", "prevent"): "prevent",
    ("prevent", "prevent"): "cause",
}

REL_PHRASE = {
    "cause": "causes", "prevent": "prevents", "cure": "cures",
    "harm": "harms", "guidance": "is advised for", "efficacy": "works against",
    "course": "changes the course of",
}


def _spans(text):
    """Lower-cased words with their character offsets, punctuation kept aside."""
    return [(m.group(0), m.start(), m.end())
            for m in re.finditer(r"[a-z0-9']+", (text or "").lower())]


def split_atom(text):
    """Split an atom at its first relation word into (subject, relation, object)."""
    spans = _spans(text)
    rel = primary_relation(text)
    if not rel or not spans:
        return None
    pos = None
    for i, (w, s, e) in enumerate(spans):
        if w in REL_PHRASE_KEYS.get(rel, ()):
            pos = i
            break
    if pos is None:
        return None
    subject = " ".join(w for w, _, _ in spans[:pos])
    obj = " ".join(w for w, _, _ in spans[pos + 1:])
    if not subject or not obj:
        return None
    return subject, rel, obj


def chain_derive(a, b, c=None):
    """Derive what two linked atoms force, and check a third atom against it.

    "Coffee causes cancer" + "cancer causes death" force "coffee causes death".
    If a third atom says "coffee prevents death", the submission contradicts
    itself through a two-step path, not through a single pairwise clash. The
    derivation is stated with its basis so a reader can reject it.
    """
    sa = split_atom(a)
    sb = split_atom(b)
    if not sa or not sb:
        return None
    s1, r1, o1 = sa
    s2, r2, o2 = sb
    if not (_content(o1) and _content(o1) & _content(s2)):
        return None
    if (r1, r2) not in CHAIN_RELATIONS:
        return None
    r = CHAIN_RELATIONS[(r1, r2)]
    derived = "%s %s %s" % (s1, REL_PHRASE[r], o2)
    out = {"type": "chain", "atoms": [0, 1], "derived": derived, "relation": r,
           "basis": "chain:%s+%s=>%s" % (r1, r2, r),
           "note": "Two atoms link end to end and force a third statement; the "
                   "derivation is shown so it can be checked, not hidden."}
    if c is None:
        return out
    if _content(s1) & _content(c) and _content(o2) & _content(c) and r in relation_classes(derived):
        rc = relation_classes(c)
        neg = negation.detect(c)["count"]
        opposed = r == "cause" and "prevent" in rc or r == "prevent" and "cause" in rc
        if opposed or neg % 2:
            out["atoms"] = [0, 1, 2]
            out["conflict"] = True
            out["texts"] = [a, b, c]
            out["note"] = ("These three atoms cannot all be true: the first two force "
                           "\"%s\", the third denies it." % derived)
            return out
        out["atoms"] = [0, 1, 2]
        out["texts"] = [a, b, c]
        out["conflict"] = False
    return out


def chains(claims):
    """Find chain derivations inside one submission, one per linked pair."""
    out, seen, flagged = [], set(), set()
    for i in range(len(claims)):
        for j in range(len(claims)):
            if i == j or (min(i, j), max(i, j)) in seen:
                continue
            base = chain_derive(claims[i], claims[j])
            if not base:
                continue
            conflict = None
            agree = None
            for k in range(len(claims)):
                if k in (i, j):
                    continue
                cand = chain_derive(claims[i], claims[j], claims[k])
                if not cand:
                    continue
                if cand.get("conflict") and conflict is None:
                    cand["atoms"] = [i, j, k]
                    conflict = cand
                elif not cand.get("conflict") and agree is None:
                    cand["atoms"] = [i, j, k]
                    agree = cand
            entry = conflict or agree or dict(base, atoms=[i, j])
            key = tuple(sorted(entry["atoms"]))
            if key in flagged:
                seen.add((min(i, j), max(i, j)))
                continue
            flagged.add(key)
            seen.add((min(i, j), max(i, j)))
            out.append(entry)
    return out


def relations(claims):
    """Label mutually exclusive atom pairs in one submission."""
    out = []
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            r = compare(claims[i], claims[j])
            if not r["conflict"]:
                continue
            out.append({
                "type": "contradiction",
                "atoms": [i, j],
                "texts": [claims[i], claims[j]],
                "basis": r["basis"],
                "shared": r["shared"],
                "note": "These two atoms cannot both be true; each is judged on its own evidence and neither is averaged into the other.",
            })
    return out


def explain(rel):
    """One line of plain English for the UI and the audit trail."""
    basis = rel.get("basis") or ""
    if basis.startswith("antonym:"):
        pair = basis.split(":", 1)[1].split("/")
        return "Opposite predicates (%s vs %s) about the same subject." % (pair[0], pair[1])
    if basis.startswith("opposite_relation:"):
        pair = basis.split(":", 1)[1].split("/")
        return "Opposite relations (%s vs %s) over the same subject." % (pair[0], pair[1])
    if basis == "negation":
        return "One atom negates what the other asserts."
    return "The two atoms cannot both be true."
