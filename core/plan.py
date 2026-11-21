"""What the corpus does and does not cover, and what would settle a refusal.

Three things live here, all of them derived from strings already on the card or
in the claim, so the front end can mirror them exactly:

  scope_of(claim, corpus)      -> is this claim inside the corpus's subject?
  plan_for(claim, near, scope) -> the sentences someone would have to find
  enrich_near(corpus, near)    -> near-miss cards become openable sources

A refusal is only useful if it says where the corpus ends and what would end the
refusal. Neither of those changes a verdict: both are descriptions of the
evidence that is missing, not guesses about the truth of the claim.
"""

PLAN_WOULD_CHANGE = (
    "A card asserting this proposition, for the same population and endpoint, from a "
    "source this corpus already treats as authoritative would settle it. A card that "
    "only shares the topic cannot: that is the guard this refusal is standing on."
)
PLAN_BASIS = "verbatim claim + the nearest card's own assertion + the corpus's nearest topic"


from .evidence import outcome_classes


def _tag_counts(corpus):
    counts = {}
    for card in corpus["evidence_cards"]:
        for tag in card.get("tags") or []:
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def _order(names, counts):
    """Count desc, then case-insensitive name, then exact name.

    The comparator is written out so the JavaScript mirror can sort identically
    instead of relying on locale collation.
    """
    return sorted(names, key=lambda n: (-counts.get(n, 0), n.lower(), n))


def scope_of(claim, corpus):
    """Is the claim inside the subject the corpus covers, and which topics touch it.

    Deliberately coarse: a tag matches when its text occurs in the claim, so
    "Health" covers most health claims and "Health" is also the corpus's largest
    tag. This is a coverage statement, not a relevance score — it is used to say
    "outside what 112 cards can settle", never to decide anything.
    """
    text = (claim or "").lower()
    tags = _tag_counts(corpus)
    counts = {tag: n for tag, n in tags.items() if tag.lower() in text}
    tagged_cards = sum(
        1 for card in corpus["evidence_cards"]
        if any(tag.lower() in text for tag in (card.get("tags") or []))
    )
    # A condition the corpus has a word for ("diabetes") is inside the corpus's
    # subject even when no card carries its topic label: the gap is evidence,
    # not scope. An iPhone claim matches neither, and is honestly out of scope.
    has_condition = bool(outcome_classes(claim))
    if counts:
        topics = _order(list(counts.keys()), counts)[:3]
    else:
        topics = _order(list(tags.keys()), tags)[:3]
    return {
        "in_corpus": bool(counts) or has_condition,
        "topics": topics,
        "tagged_cards": tagged_cards,
        "basis": "topic label or a condition word the corpus knows",
    }


def plan_for(claim, near, scope):
    """Search strings and the sentence that would end this refusal.

    The first query is the claim itself, because a verbatim sentence is the
    strongest search a reader can run. The second is the nearest card's own
    assertion, which is what a same-proposition card would look like. The third
    is the corpus's nearest topic plus "official guidance", for when neither of
    the first two returns anything.
    """
    queries = [claim.strip().rstrip(",.;:") + " evidence"]
    if near:
        queries.append(near[0]["card_claim"])
    if scope and scope.get("topics"):
        queries.append(scope["topics"][0] + " official guidance")
    return {
        "queries": queries,
        "would_change": PLAN_WOULD_CHANGE,
        "basis": PLAN_BASIS,
    }


def enrich_near(corpus, near):
    """Attach the source, link and archived snippet to each near-miss card.

    A refusal that names a card but cannot open it is still a dead end. These
    fields let the page show the closest sources as background — clearly
    labelled as not used for the verdict.
    """
    by_id = {c["card_id"]: c for c in corpus["evidence_cards"]}
    for entry in near or []:
        card = by_id.get(entry.get("card_id"), {})
        entry["source_id"] = card.get("source_id")
        entry["source_name"] = card.get("source_name")
        entry["url"] = card.get("url")
        entry["snippet"] = card.get("snippet")
        entry["stance"] = card.get("stance")
    return near


def overall_verdict(summary):
    """One word for a whole submission, used by the batch table.

    Mixed submissions stay mixed: averaging a refuted atom with an undetermined
    one would invent a state the kernel never produced.
    """
    n = summary.get("claims", 0)
    if n == 0:
        return "not_checkable"
    if summary.get("supported", 0) == n:
        return "supported"
    if summary.get("refuted", 0) == n:
        return "refuted"
    if summary.get("undetermined", 0) == n:
        return "undetermined"
    return "mixed"
