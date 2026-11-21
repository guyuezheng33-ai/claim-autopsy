"""Retrieval and citation validation (Q1, Q7).

An English word-level BM25-lite index with IDF-weighted anchor coverage.
Card text is normalized through a one-way synonym table, then scored. Coverage
requires the card's content words to appear in the input so common words cannot
fake relevance. Scope guards (`exclude_if`, `requires_all`) let a specific card
yield to, or be held back from, a vaguer claim.
"""
import json
import math
import os
import re

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "claims.json")

# One-way convergence only. Never merge a general term with a specific one:
# doing that once made "perfect sphere" retrieve the generic "round Earth" card.
CANON = {
    "influenza": "flu", "vaccines": "vaccine",
    "antibiotics": "antibiotic", "causes": "cause", "caused": "cause",
    "gives": "give", "gave": "give", "people": "humans",
    "ten percent": "10%", "10 percent": "10%",
    # Third-person verb forms must fold to the base form. A mechanically negated
    # claim ("does not prevent") otherwise stops matching the card ("prevents").
    "prevents": "prevent", "preventing": "prevent",
    "protects": "protect", "reduces": "reduce", "raises": "raise",
    "cures": "cure", "treats": "treat", "causing": "cause",
    # Shape adjectives are the predicate of a geometry claim, not decoration.
    "spherical": "round",
}
_CANON_ORDER = sorted(CANON.items(), key=lambda kv: -len(kv[0]))

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "to", "of",
    "and", "or", "in", "on", "for", "with", "that", "this", "it", "its",
    "can", "could", "do", "does", "did", "have", "has", "had", "you", "your",
    "we", "our", "only", "not", "no", "from", "by", "as", "at", "will",
    "would", "may", "might", "more", "than", "other", "their", "there",
    "get", "gets", "make", "makes", "give", "take", "takes", "use", "uses",
}


def _normalize(s):
    s = (s or "").lower()
    for k, v in _CANON_ORDER:
        s = s.replace(k, v)
    return s


def load_corpus(path=DATA_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _tokens(s):
    return re.findall(r"[a-z0-9%]+", _normalize(s))


def _score(query_tokens, doc_tokens, idf):
    tf = {}
    for t in doc_tokens:
        tf[t] = tf.get(t, 0) + 1
    score = 0.0
    seen = set()
    for t in query_tokens:
        if t in seen:
            continue
        seen.add(t)
        if t in tf:
            score += (1 + math.log(tf[t])) * idf.get(t, 1.0)
    return score


def build_index(corpus):
    docs = []
    for card in corpus["evidence_cards"]:
        text = " ".join([
            card.get("claim", ""),
            " ".join(card.get("tags", [])),
            card.get("source_name", ""),
            card.get("snippet", ""),
        ])
        docs.append({"card": card, "tokens": _tokens(text)})
    df = {}
    for d in docs:
        for t in set(d["tokens"]):
            df[t] = df.get(t, 0) + 1
    n = len(docs)
    idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
    return idf, docs


def anchor_coverage(claim, card_claim, idf=None):
    """IDF-weighted share of a card's content words found in the input."""
    words = _tokens(card_claim)
    content = [w for w in words if w not in STOP_WORDS and len(w) > 1]
    if not content:
        return 0.0
    in_words = set(_tokens(claim))
    weight = (lambda w: max(idf.get(w, 1.0), 0.5)) if idf else (lambda w: 1.0)
    total = sum(weight(w) for w in content)
    if total <= 0:
        return 0.0
    return sum(weight(w) for w in content if w in in_words) / total


ANCHOR_MIN = 0.42

# Relation classes. A card that says "causes cancer" may decide whether coffee
# causes cancer; it may not decide whether coffee prevents it. Without this
# guard a refutation of one causal direction silently decided the opposite
# direction as well.
RELATION_WORDS = {
    "prevent": ("prevent", "prevents", "preventing", "prevention", "protect",
                "protects", "protection", "reduce", "reduces", "lower", "lowers",
                "avoid", "avoids", "stop", "stops"),
    "cause": ("cause", "causes", "caused", "causing", "trigger", "triggers",
              "lead", "leads", "produce", "produces", "increase", "increases",
              "raise", "raises", "give", "spread", "spreads", "transmit"),
    "cure": ("cure", "cures", "cured", "treat", "treats", "treated", "heal",
             "heals", "reverse", "reverses", "fix", "fixes"),
    "guidance": ("receive", "receives", "eligible", "eligibility",
                 "recommend", "recommends", "recommended", "should", "must",
                 "allowed", "approved", "ineligible"),
    "course": ("resolve", "resolves", "resolved", "recover", "recovers", "recovery",
               "clear", "clears", "last", "lasts", "duration", "self", "own",
               "symptom", "symptoms", "mild", "severe"),
    "efficacy": ("work", "works", "worked", "effective", "effectiveness", "efficacy",
                 "kill", "kills", "killed", "eliminate", "eliminates", "useless",
                 "ineffective"),
}
HARM_WORDS = ("exceed", "exceeds", "exceeding", "overdose",
              "harmful", "harm", "dangerous", "damage", "damages", "toxic", "unsafe")

# Relation verbs and harm adjectives express structure, not content: every
# sentence needs a predicate, so agreeing on "cause" says nothing about what is
# caused. They are excluded when deciding whether a citation rests on anything
# more than topic labels (see `topic_only` in `retrieve`).
REL_TOKENS = {w for words in RELATION_WORDS.values() for w in words}

# Which relation classes may decide each other. Same class always may. The
# asymmetric pairs are the ones with a defensible reading: a harm statement is
# decided by a causation card and by an eligibility/guidance card (both discuss
# the risk of the same intervention), but a harm statement says nothing about
# whether the intervention prevents something. Everything else refuses, which is
# what stops "coffee prevents cancer" from borrowing a "coffee causes cancer"
# card and "vitamin C cures flu" from borrowing a vaccine-eligibility card.
RELATION_COMPAT = {
    ("harm", "cause"), ("harm", "cure"), ("harm", "guidance"),
    # A guidance claim ("use sunscreen with SPF 15") is decided by a card stating
    # what the product does ("sunscreen filters UV and protects the skin").
    ("guidance", "prevent"),
}

# Population scope. A claim narrowed to children, infants or pregnancy cannot be
# decided by a card that only ever examined adults, and a card about infants
# cannot decide a claim about everyone. The two are different propositions with
# different evidence, so the pair refuses instead of borrowing a neighbour's
# verdict. Cards with no population word are treated as unmarked (general), which
# keeps ordinary claims untouched.
POP_GROUPS = {
    "child": ("child", "children", "kid", "kids", "infant", "infants", "infant's",
              "toddler", "toddlers", "baby", "babies", "pediatric", "adolescent",
              "adolescents", "teen", "teens", "teenager", "teenagers", "newborn",
              "newborns"),
    "pregnancy": ("pregnant", "pregnancy", "breastfeeding", "lactating"),
    "adult": ("adult", "adults", "elderly", "senior", "seniors", "geriatric",
              "menopausal"),
    "male": ("men", "male", "males", "boy", "boys"),
    "female": ("women", "woman", "female", "females", "girl", "girls"),
}


_QTY_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(mcg|µg|ug|mg|g|iu|ml|%|percent)", re.IGNORECASE)
_QTY_UNIT = {"mcg": "mcg", "µg": "mcg", "ug": "mcg", "mg": "mg", "g": "g",
             "iu": "iu", "ml": "ml", "%": "%", "percent": "%"}
DOSE_UNITS = {"mcg", "mg", "g", "iu", "ml", "%"}


def quantities(text):
    """Map unit -> set of numeric values stated in the text.

    Only dose-shaped quantities (mass, IU, volume, percentage) are read. Durations
    and counts are deliberately excluded: "20 seconds" is a recommendation, not
    an amount, and a card about timing should not be able to settle a dose.
    """
    out = {}
    for value, unit in _QTY_RE.findall(text or ""):
        u = _QTY_UNIT.get(unit.lower())
        if not u:
            continue
        try:
            v = float(value.replace(",", ""))
        except ValueError:
            continue
        out.setdefault(u, set()).add(v)
        # "1,000 IU" and "1000 IU" must be the same number.
    return out


# Hedged frequency is not an absolute. "Antibiotic side effects are rare" cannot
# refute "antibiotics never have side effects", because rare is not never: the
# card admits the event and only bounds its rate. Only a claim that states an
# absolute quantifier is checked, so ordinary claims are unaffected.
ABSOLUTE_WORDS = {"never", "always", "none", "every", "all", "no"}
HEDGE_WORDS = {"rare", "rarely", "uncommon", "uncommonly", "sometimes", "occasionally",
               "may", "might", "can", "could", "often", "usually", "frequently"}


def strength_compatible(claim, card_claim):
    """Reject an absolute claim settled only by a hedged card (or the reverse)."""
    a, b = set(_tokens(claim)), set(_tokens(card_claim))
    if a & ABSOLUTE_WORDS and b & HEDGE_WORDS:
        return False
    if a & HEDGE_WORDS and b & ABSOLUTE_WORDS:
        return False
    return True


def quantity_compatible(claim, card_claim):
    """Reject a card when both sides state a dose in the same unit and disagree.

    A card about 400 mcg cannot settle a claim about 40 mcg, and a card about 60%
    alcohol cannot refute a claim about 40%. When only one side states a number,
    the pair stays compatible: a general card may still speak to a specific
    request, which keeps "vitamin C 500 mg prevents a cold" decidable.
    """
    a, b = quantities(claim), quantities(card_claim)
    for unit in DOSE_UNITS & set(a) & set(b):
        if not (a[unit] & b[unit]):
            return False
    return True


# Attribute words: a claim about safety or effectiveness is not the same
# proposition as a claim about what something causes. A card that only says
# "getting a flu shot gives you the flu" cannot settle "flu vaccines are safe",
# even though the two share every subject word. Matching on subjects alone
# transferred that stance and produced a confident, wrong verdict.
ATTRIBUTE_WORDS = {
    "safe": ["safe", "safely", "safety"],
    "unsafe": ["unsafe", "dangerous", "harmful", "risky", "hazardous"],
    "effective": ["effective", "efficacy", "beneficial", "works", "work", "clean",
                  "cleans", "cleanse", "cleansing", "disinfects", "disinfect"],
    "useless": ["useless", "ineffective", "uselessly"],
}
# Attributes that address the same question from opposite sides.
ATTR_COMPAT = [("safe", "unsafe"), ("effective", "useless")]


def attribute_classes(text):
    tokens = set(_tokens(text))
    return {cls for cls, words in ATTRIBUTE_WORDS.items() if tokens & set(words)}


def attribute_compatible(claim, card_claim):
    """Reject a card that does not speak to the claim's attribute at all.

    A claim that asserts safety or effectiveness is a statement about the whole
    intervention. A card about one specific harm or one specific cause covers a
    narrower proposition: "getting a flu shot gives you the flu" being refuted
    says nothing about whether flu shots are safe, so that stance must not be
    transferred. Practice and eligibility cards may still decide the question
    ("pregnant women can receive the flu vaccine" is a recommendation, and a
    refusal of that recommendation is evidence against "unsafe for pregnancy").
    """
    a, b = attribute_classes(claim), attribute_classes(card_claim)
    if not a:
        return True
    if b:
        if a & b:
            return True
        for x, y in ATTR_COMPAT:
            if (x in a and y in b) or (y in a and x in b):
                return True
        return False
    # The card names no attribute: only a causal or harm statement is too narrow.
    return not (relation_classes(card_claim) & {"cause", "harm"})


# Outcomes and conditions. Two claims can share every subject word and still be
# about different diseases: "antibiotics cure a common cold or flu" was being
# decided by a card about antibiotics and COVID-19, because the only shared
# content word was "antibiotics". When both sides name a condition, the
# conditions must be the same.
OUTCOME_WORDS = [
    "cold", "colds", "flu", "influenza", "covid", "covid-19", "coronavirus",
    "cancer", "diabetes", "malaria", "measles", "polio", "pneumonia", "asthma",
    "autism", "poisoning", "headache", "headaches", "migraine", "infection",
    "infections", "diarrhea", "diarrheal", "diarrhoea", "respiratory", "stroke",
    "obesity", "depression", "anxiety", "allergy", "allergies", "blindness",
    "night", "vision", "pregnancy", "birth", "neural", "tube", "defects",
    "toxicity", "dementia", "arthritis", "tuberculosis",
    "tumour", "tumours", "tumor", "tumors", "neoplasm", "carcinoma", "sars-cov-2",
]

# Two words for the same condition are one class, or the guard refuses a card
# that names it differently. Found on the dev slice: "dry indoor air may
# encourage coronavirus spread" was refuted by E122, "exposure to air makes a
# tumour spread" — the only shared words were air and spread, and tumour was not
# an outcome word at all, so the comparison saw no condition on the card's side
# and let it through. "coronavirus" and "covid" were also separate classes,
# which would have blocked the weather cards from deciding weather claims.
OUTCOME_SYNONYMS = {
    "covid-19": "covid", "coronavirus": "covid", "sars-cov-2": "covid",
    "tumour": "cancer", "tumours": "cancer", "tumor": "cancer", "tumors": "cancer",
    "neoplasm": "cancer", "carcinoma": "cancer",
}


def outcome_classes(text):
    tokens = set(_tokens(text))
    out = set()
    for w in OUTCOME_WORDS:
        if w in tokens or w.replace("-", " ") in text.lower():
            out.add(OUTCOME_SYNONYMS.get(w, w))
    out.discard("night")
    return out


GENERIC_OUTCOMES = {"infection", "infections", "respiratory", "vision", "birth",
                    "pregnancy", "toxicity"}


def object_compatible(claim, card_claim):
    """Reject a card about a different condition than the claim names.

    Generic categories ("viral infections", "respiratory illness") are not
    conditions: a card about colds may still decide a claim about infections.
    Only two disjoint *specific* conditions are a mismatch.
    """
    a, b = outcome_classes(claim), outcome_classes(card_claim)
    a, b = a - GENERIC_OUTCOMES, b - GENERIC_OUTCOMES
    if not a or not b:
        return True
    return bool(a & b)


# What the claim says happens to the condition, not which condition it is.
# `object_compatible` compares the nouns (cold vs cancer); this compares the
# predicate's endpoint. Without it, a card that says "vitamin supplements can
# cure COVID-19" decides "vitamin D makes you more susceptible to COVID-19":
# same object, same direction of interest, different endpoint. Found on
# HealthVer, where the claim asked about susceptibility and the card answered
# about cure — the engine called it refuted.
PREDICATE_OUTCOMES = {
    "risk": ["susceptible", "susceptibility", "vulnerable", "vulnerability",
             "risk", "risks", "likely", "probability", "prone", "catch",
             "catches", "contract", "contracts"],
    "cure": ["cure", "cures", "cured", "treat", "treats", "treated",
             "treatment", "therapy", "remedy", "heal", "heals", "reverse"],
    "prevent": ["prevent", "prevents", "prevention", "protect", "protects",
                "protection", "avoid", "avoids", "stop", "stops", "block",
                "blocks"],
    "transmit": ["transmit", "transmits", "transmission", "spread", "spreads",
                 "spreading", "infect", "infects", "infected"],
    "harm": ["cause", "causes", "caused", "harm", "harms", "damage", "damages",
             "toxic", "poison", "poisoning", "side", "effects", "worsen",
             "worsens"],
    "severity": ["severe", "severely", "severity", "hospitalised",
                 "hospitalized", "hospitalisation", "hospitalization", "death",
                 "die", "dies", "mortality", "fatal"],
}

# Endpoints that address the same question from different sides.
PREDICATE_COMPAT = {("risk", "prevent"), ("risk", "transmit"),
                    ("prevent", "transmit"), ("risk", "severity")}


def predicate_classes(text):
    tokens = set(_tokens(text))
    out = set()
    for name, words in PREDICATE_OUTCOMES.items():
        if any(w in tokens for w in words):
            out.add(name)
    return out


def predicate_compatible(claim, card_claim):
    a, b = predicate_classes(claim), predicate_classes(card_claim)
    if not a or not b:
        return True
    if a & b:
        return True
    return any((x, y) in PREDICATE_COMPAT or (y, x) in PREDICATE_COMPAT
               for x in a for y in b)


def sentence_prohibited(text):
    """True when a guidance verb carries its own `not` ("is not recommended")."""
    return re.search(
        r"\bnot[ \t]+(?=(recommended|advised|allowed|permitted|approved)\b)",
        text.lower()) is not None


def _head_subject(text):
    """Words before the first relation word, i.e. what the sentence is about."""
    rel = primary_relation(text)
    if not rel:
        return None
    tokens = _tokens(text)
    keys = REL_PHRASE_KEYS_FOR_SUBJECT.get(rel, ())
    for i, tok in enumerate(tokens):
        if tok in keys:
            head = [t for t in tokens[:i] if t not in STOP_WORDS]
            return set(head) or None
    return None


REL_PHRASE_KEYS_FOR_SUBJECT = dict(RELATION_WORDS)
REL_PHRASE_KEYS_FOR_SUBJECT["harm"] = HARM_WORDS


SUBJECT_SYNONYMS = {
    "monosodium": "msg", "glutamate": "msg",
    "ascorbic": "vitamin c", "jab": "vaccine", "shot": "vaccine",
}


NEG_WORDS = {"not", "no", "never", "cannot", "cant", "without", "none", "nothing",
             "do", "does", "did", "have", "has", "had", "is", "are", "was", "were", "be"}


def same_proposition(a, b, threshold=0.6):
    """True when two sentences are the same statement apart from negation.

    Used to cancel a double negative: "Antibiotics never produce side effects"
    and a card reading "Antibiotics have no side effects" are the same claim,
    so the card's refutation must not be flipped back into support. A merely
    related sentence ("Flu vaccination is not unsafe ...") scores far below the
    threshold and is not treated as the same proposition.
    """
    A = set(_tokens(a)) - NEG_WORDS
    B = set(_tokens(b)) - NEG_WORDS
    if not A or not B:
        return False
    return len(A & B) / float(len(A | B)) >= threshold


def _expand_subject(words):
    out = set(words)
    for w in list(out):
        if w in SUBJECT_SYNONYMS:
            out.add(SUBJECT_SYNONYMS[w])
    return out


def subject_compatible(claim, card_claim):
    """Reject a card about a different actor when nothing else connects them.

    "Smoking causes lung cancer" was being refuted by a card about coffee and
    cancer: they share the outcome and the relation, so every content-word
    guard passed. The head noun before the relation is what the sentence is
    about; when the two heads are disjoint *and* neither head appears anywhere
    in the other sentence, the card is about someone else.
    """
    a, b = _head_subject(claim), _head_subject(card_claim)
    if not a:
        # A claim with no relation verb ("antibiotics never have side effects")
        # still has a subject: its leading content words.
        a = set(list(_tokens(claim))[:2]) - NEG_WORDS
    if not b:
        return True
    a, b = _expand_subject(a), _expand_subject(b)
    if a & b:
        return True
    # The card's own subject may appear anywhere in the claim ("pregnant women
    # cannot receive the vaccine" decides "the vaccine is unsafe for pregnant
    # women"). The reverse is not allowed: "Cancer causes death" must not be
    # decided by a card whose *object* is cancer ("coffee causes cancer").
    if b & set(_tokens(claim)):
        return True
    return False


def population_classes(text):
    tokens = set(_tokens(text))
    return {cls for cls, words in POP_GROUPS.items() if tokens & set(words)}

def population_compatible(claim, card_claim):
    """Reject a card whose population scope is not the claim's population scope.

    Unmarked on both sides is compatible. Marked on one side only is a scope
    mismatch in either direction: narrowing a general card to a subgroup, or
    widening a subgroup card to everyone.
    """
    a, b = population_classes(claim), population_classes(card_claim)
    if not a and not b:
        return True
    if not a or not b:
        return False
    return bool(a & b)


def relation_classes(text):
    tokens = set(_tokens(text))
    out = {cls for cls, words in RELATION_WORDS.items() if tokens & set(words)}
    if tokens & set(HARM_WORDS):
        out.add("harm")
    return out


def primary_relation(text):
    """The relation the sentence actually asserts, by first mention.

    A sentence can carry more than one relation word. "Alcohol gel prevents the
    spread of flu" contains `prevent` and `spread` (a cause word), so a set
    intersection said it agrees with "the vaccine gives you the flu" — a cause
    card — and refuted a prevention claim. The first relation word in the
    sentence is the one being asserted; the others are objects or modifiers.
    """
    pos = None
    tokens = _tokens(text)
    for i, tok in enumerate(tokens):
        for cls, words in RELATION_WORDS.items():
            if tok in words:
                if pos is None or i < pos[0]:
                    pos = (i, cls)
        if tok in HARM_WORDS and (pos is None or i < pos[0]):
            pos = (i, "harm")
    return pos[1] if pos else None


def relation_compatible(claim, card_claim):
    a, b = relation_classes(claim), relation_classes(card_claim)
    if not a or not b:
        return True
    pa, pb = primary_relation(claim), primary_relation(card_claim)
    if pa and pb:
        if pa == pb or (pa, pb) in RELATION_COMPAT or (pb, pa) in RELATION_COMPAT:
            return True
        return False
    for x in a:
        for y in b:
            if x == y or (x, y) in RELATION_COMPAT or (y, x) in RELATION_COMPAT:
                return True
    return False


def topic_overlap(claim, card_claim):
    """True when the two share at least one content word that is neither a
    population label nor a relation verb.

    Coverage can otherwise be satisfied by rare, high-IDF population words alone:
    a card about "pregnant women" scored 0.42+ against "MSG causes headaches in
    pregnant women" and was about to decide it. Population words say who, relation
    words say how; neither says what. The proposition needs a shared subject.
    """
    pop = {w for words in POP_GROUPS.values() for w in words}
    rel = {w for words in RELATION_WORDS.values() for w in words} | set(HARM_WORDS)
    a = {w for w in _tokens(claim) if w not in STOP_WORDS and w not in pop and w not in rel}
    b = {w for w in _tokens(card_claim) if w not in STOP_WORDS and w not in pop and w not in rel}
    return bool(a & b)


LONG_CLAIM_TERMS = 6      # a claim this long has plenty of content to answer to
THIN_ANCHORS = 1          # ... so one shared word cannot carry a verdict


def content_terms(text):
    """Words a claim asserts with: stop words and bare numbers removed."""
    return [w for w in _tokens(text) if w not in STOP_WORDS and not w.isdigit()]


def tag_tokens(card):
    """Topic labels carried as metadata, not as asserted content."""
    return set(_tokens(" ".join(card.get("tags") or [])))


def matched_anchors(claim, card_claim):
    """The card's content words that literally occur in the claim.

    This is the receipt behind a citation: not a score, but the words that made
    the card reachable. If this list is empty, the citation was bought with
    scoring arithmetic rather than shared vocabulary, and the UI has nothing
    honest to show.
    """
    content = [w for w in _tokens(card_claim) if w not in STOP_WORDS and len(w) > 1]
    have = set(_tokens(claim))
    return sorted({w for w in content if w in have})


def retrieve(claim, corpus=None, top_k=3):
    """Return (hits, trace). A hit carries the card, its citation and scores.

    The trace also carries `near_miss`: cards that scored and anchored well
    enough to be considered, but were rejected by a guard, with the reason. A
    refusal that says *which* card came close and *why* it was not used is
    falsifiable in a way that "no evidence found" is not.
    """
    corpus = corpus or load_corpus()
    idf, docs = build_index(corpus)
    qt = _tokens(claim)
    nclaim = _normalize(claim)
    scored = []
    near = []
    for d in docs:
        card = d["card"]
        s = _score(qt, d["tokens"], idf)
        cov = anchor_coverage(claim, card.get("claim", ""), idf)
        if s <= 0 or cov < ANCHOR_MIN:
            continue
        reasons = []
        excludes = card.get("exclude_if", [])
        if excludes and any(x in nclaim for x in excludes):
            reasons.append("excluded_by_scope")
        requires = card.get("requires_all", [])
        if requires and not all(x in nclaim for x in requires):
            reasons.append("missing_required_topic")
        if not population_compatible(claim, card.get("claim", "")):
            reasons.append("different_population")
        if not quantity_compatible(claim, card.get("claim", "")):
            reasons.append("different_quantity")
        if not relation_compatible(claim, card.get("claim", "")):
            reasons.append("different_relation")
        if not attribute_compatible(claim, card.get("claim", "")):
            reasons.append("different_predicate")
        if not object_compatible(claim, card.get("claim", "")):
            reasons.append("different_object")
        if not predicate_compatible(claim, card.get("claim", "")):
            reasons.append("different_outcome")
        if not strength_compatible(claim, card.get("claim", "")):
            reasons.append("different_strength")
        if not subject_compatible(claim, card.get("claim", "")):
            reasons.append("different_subject")
        if not topic_overlap(claim, card.get("claim", "")):
            reasons.append("no_shared_topic")
        # A card may not be reached through its topic labels alone. "COVID-19",
        # "Cancer" and "Earth" are stored as tags on many cards; if those labels
        # are the only words a claim shares with a card, the card's assertion
        # ("... is caused by bacteria") was never matched, and letting it decide
        # turns a topic mention into a verdict. Found on 1,200 externally written
        # claims: 65 of 89 decisions came through this route.
        anchors = matched_anchors(claim, card.get("claim", ""))
        content = [a for a in anchors if a not in REL_TOKENS]
        if (anchors and set(content) <= tag_tokens(card)
                and not same_proposition(claim, card.get("claim", ""))):
            reasons.append("topic_only")
        if (len(content_terms(claim)) >= LONG_CLAIM_TERMS
                and len(anchors) <= THIN_ANCHORS
                and not same_proposition(claim, card.get("claim", ""))):
            reasons.append("thin_anchor")
        if reasons:
            near.append({"card_id": card["card_id"], "score": round(s, 4),
                         "anchor": round(cov, 3), "reasons": sorted(set(reasons)),
                         "card_claim": card.get("claim", "")})
            continue
        scored.append((s, card, cov))
    scored.sort(key=lambda x: -x[0])
    near.sort(key=lambda x: -x["score"])
    hits = []
    for s, card, cov in scored[:top_k]:
        citation = {
            "card_id": card["card_id"],
            "source_id": card["source_id"],
            "source_name": card["source_name"],
            "url": card["url"],
            "snippet": card["snippet"],
            "stance": card["stance"],
            "matched": matched_anchors(claim, card["claim"]),
        }
        hits.append({
            "score": round(s, 4),
            "anchor_coverage": round(cov, 3),
            "stance_weight": card.get("stance_weight", 1.0),
            "card": card,
            "citation": citation,
            "claim_in_lib": card["claim"],
        })
    trace = {
        "step": "retrieve",
        "input": claim,
        "normalized": nclaim,
        "method": "synonym-norm+bm25-lite+idf-anchor+scope",
        "output": [{"card_id": h["citation"]["card_id"], "score": h["score"],
                    "anchor": h["anchor_coverage"], "weight": h["stance_weight"]} for h in hits],
        "detail": "Synonym normalization, word-level TF-IDF, IDF-weighted anchor gate (%.2f), scope guards, Top-%d."
                  % (ANCHOR_MIN, top_k),
        "near_miss": near[:3],
    }
    return hits, trace


def validate_citations(citations):
    """Every citation must carry these five non-empty fields."""
    required = ("card_id", "source_id", "url", "snippet", "stance")
    for c in citations:
        missing = [k for k in required if not c.get(k)]
        if missing:
            return False, missing
    return True, []


