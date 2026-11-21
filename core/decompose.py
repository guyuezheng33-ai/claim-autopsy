"""Atomic claim decomposition using deterministic English rules.

Sentence and list punctuation split the input; connectors split further, but
connectors after a comma are protected when they continue the same claim
("..., otherwise ..."). Questions, subjective fragments and fragments with
fewer than three words are filtered. When nothing survives, return nothing.
"""
import re

CONNECTORS = ["and", "also", "but", "plus", "however", "moreover", "in addition"]
NO_SPLIT_LEADS = ["and", "but", "because", "so", "otherwise", "which", "that", "besides"]
SPLIT_PUNCT = r"[。！？；;、\n]+"

# Two sentences must be able to become two atoms, otherwise "X is true. X is
# false." collapses into one string and the contradiction never surfaces. A full
# stop only breaks a sentence when whitespace and a capital (or digit / quote)
# follow, and never after a known abbreviation or a decimal point.
_SENT_BREAK = re.compile(r"(?<=[.!?])[ \t]+(?=[\"'(\[A-Z0-9])")
_ABBREV = {"e.g", "i.e", "dr", "mr", "mrs", "ms", "no", "vs", "u.s", "st",
           "approx", "fig", "ref", "cf", "al", "etc", "inc", "ltd"}


def _break_sentences(text):
    """Insert a newline at real sentence boundaries, leaving abbreviations alone."""
    out, last = [], 0
    for m in _SENT_BREAK.finditer(text):
        head = text[last:m.start()]
        word = re.split(r"[^A-Za-z.\u2019']", head.rstrip())[-1].lower()
        if word in _ABBREV:
            continue
        out.append(head)
        out.append("\n")
        last = m.end()
    out.append(text[last:])
    return "".join(out)

# A bare predicate after a connector has lost its subject: "The Earth is round
# and flat" must yield a second atom, otherwise the contradiction disappears
# inside one apparently supported claim.
VERB_HINTS = (
    "is", "are", "was", "were", "can", "cannot", "could", "will", "would",
    # Modals and appearance verbs: "mask wearing and social distancing for
    # COVID-19 may be slowing influenza spread" is one claim with a compound
    # subject, and without these the first noun phrase was silently dropped.
    "may", "might", "must", "should", "shall", "appears", "appear",
    "seems", "seem", "remains", "remain", "includes", "include",
    "does", "do", "did", "has", "have", "had", "causes", "cause", "cures",
    "cure", "treats", "treat", "prevents", "prevent", "makes", "make",
    "gives", "give", "supports", "support", "improves", "improve", "contains",
    "contain", "leads", "lead", "triggers", "trigger", "builds", "build",
    "stays", "stay", "reduces", "reduce", "raises", "raise", "protects",
    "protect", "weakens", "weaken", "removes", "remove",
)


# Only predicate adjectives are repaired. "cold and flu" coordinates two
# objects and must stay one atom, while "round and flat" coordinates two
# predicates and must become two — otherwise the contradiction hides inside
# a single supported verdict.
PREDICATE_ADJ = {
    "round", "flat", "true", "false", "real", "fake", "safe", "unsafe",
    "harmful", "harmless", "healthy", "unhealthy", "dangerous", "effective",
    "ineffective", "useless", "useful", "toxic", "natural", "artificial",
    "alive", "dead", "legal", "illegal", "possible", "impossible", "normal",
    "common", "rare", "necessary", "optional", "contagious", "infectious",
    "curable", "incurable", "renewable", "finite", "infinite", "solid",
    "liquid", "hot", "cold",
}


def _is_bare_predicate(atom):
    words = [w.lower().strip(",.!?;:") for w in atom.split()]
    return 0 < len(words) <= 2 and bool(set(words) & PREDICATE_ADJ)


def _is_object_continuation(frag):
    """A short verbless fragment after a connector continues the object list."""
    words = [w for w in frag.split() if w.strip()]
    if not words or len(words) > 3:
        return False
    return not _subject_verb(frag)[1] and not _is_bare_predicate(frag)


def _subject_verb(atom):
    words = atom.split()
    for i, w in enumerate(words):
        if w.lower().strip(",.!?;:") in VERB_HINTS:
            return " ".join(words[:i]).strip(), w.strip(",.")
    return "", ""


def _clean(s):
    s = s.strip(" ，,、:：\"'“”‘’ ")
    # "e.g." / "i.e." open an example, not a claim; drop the marker so that what
    # follows is judged on its own (and usually filtered as too short).
    s = re.sub(r"^(e\.g\.|i\.e\.)\s*", "", s, flags=re.IGNORECASE)
    for c in CONNECTORS:
        if s.lower().startswith(c.lower()):
            s = s[len(c):].strip(" ，,、:：")
    return s.strip()


def _cap(s):
    """Capitalise an atom whose first letter was lost to a stripped connector."""
    if s and s[0].islower():
        return s[0].upper() + s[1:]
    return s


def _is_checkable(s):
    if len(s) < 4:
        return False
    if len(re.findall(r"[A-Za-z0-9%]+", s)) < 3:
        return False
    if s.endswith(("？", "?")):
        return False
    # "Several recent studies have looked at the impact of vitamin D" reports
    # that research exists; it does not assert a finding. Judging it against a
    # card about curing COVID-19 answers a question nobody asked.
    low = s.lower()
    words = set(re.findall(r"[a-z']+", low))
    if (words & {"studies", "study", "researchers", "scientists", "authors",
                 "investigators"}
            and (words & {"examined", "examining", "investigated",
                          "investigating", "studied", "studying", "reviewed",
                          "explored"})
            and not (words & {"found", "finds", "show", "shows", "shown",
                              "suggest", "suggests", "suggested", "report",
                              "reports", "reported", "conclude", "concludes",
                              "linked", "associated", "evidence", "cause",
                              "causes", "increase", "increases", "reduce",
                              "reduces", "effective", "risk"})):
        return False
    if (words & {"studies", "study", "researchers", "scientists", "authors",
                 "investigators"}
            and re.search(r"\b(looked at|looked into|focused on)\b", low)
            and not (words & {"found", "finds", "show", "shows", "shown",
                              "suggest", "suggests", "suggested", "report",
                              "reports", "reported", "conclude", "concludes",
                              "linked", "associated", "evidence", "cause",
                              "causes", "increase", "increases", "reduce",
                              "reduces", "effective", "risk"})):
        return False
    return True


def _split_on_comma(seg):
    out, buf = [], ""
    i = 0
    while i < len(seg):
        ch = seg[i]
        if ch in "，,":
            # A thousands separator is part of the number, not a clause break:
            # "4,000 IU" must not become "4" and "000 IU". The same rule covers
            # "1,000-4,000" ranges because only digit-digit commas are skipped.
            prev_digit = buf[-1:].isdigit()
            next_digit = seg[i + 1:i + 2].isdigit()
            if prev_digit and next_digit:
                buf += ch
                i += 1
                continue
            nxt = seg[i + 1:].lstrip(" ，,")
            if any(nxt.lower().startswith(x.lower()) for x in NO_SPLIT_LEADS):
                buf += ch
            else:
                out.append(buf)
                buf = ""
        else:
            buf += ch
        i += 1
    out.append(buf)
    return out


def rule_split(text):
    """Return a list of atomic, independently checkable claims."""
    if not text or not text.strip():
        return []
    atoms = []
    for seg in re.split(SPLIT_PUNCT, _break_sentences(text)):
        seg = seg.strip()
        if not seg:
            continue
        for piece in _split_on_comma(seg):
            # Word boundaries matter: "and" must not split "hand-sanitizer".
            pattern = "(" + "|".join(r"\b" + re.escape(c) + r"\b" for c in CONNECTORS) + ")"
            parts = re.split(pattern, piece, flags=re.IGNORECASE)
            buf = []
            i = 0
            while i < len(parts):
                p = parts[i]
                if i % 2 == 1 and p.strip().lower() in {c.lower() for c in CONNECTORS}:
                    nxt = parts[i + 1] if i + 1 < len(parts) else ""
                    if nxt.strip() and _is_object_continuation(nxt):
                        # "a common cold and flu": keep the object list together.
                        buf.append(p + nxt)
                        i += 2
                        continue
                    if buf and not _subject_verb("".join(buf))[1] and _subject_verb(nxt)[1]:
                        # "Soap and water handwashing prevents ...": the left side
                        # is a noun phrase, not a claim, so the connector joins a
                        # compound subject instead of starting a new atom.
                        buf.append(p + nxt)
                        i += 2
                        continue
                    if buf:
                        atoms.append(_clean("".join(buf)))
                        buf = []
                elif p.strip():
                    buf.append(p)
                i += 1
            if buf:
                atoms.append(_clean("".join(buf)))
    out = []
    repaired = []
    for a in atoms:
        a = _clean(a)
        if not a:
            continue
        subj, verb = _subject_verb(a)
        if not verb and _is_bare_predicate(a) and repaired:
            prev_subj, prev_verb = _subject_verb(repaired[-1])
            if prev_subj and prev_verb:
                a = "%s %s %s" % (prev_subj, prev_verb, a)
        repaired.append(a)
    for a in repaired:
        a = _cap(_clean(a))
        if _is_checkable(a) and a not in out:
            out.append(a)
    return out


def decompose(text, llm_mode=False):
    claims = rule_split(text)
    trace = {
        "step": "decompose",
        "input": text,
        "method": "rule",
        "output": claims,
        "detail": "Split on sentence and list punctuation plus connectors; questions and subjective fragments are filtered.",
    }
    return claims, trace
