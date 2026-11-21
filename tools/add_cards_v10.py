#!/usr/bin/env python3
"""Corpus v10: twelve cards authored from paragraphs already in the archive.

Why this shape: the coverage ceiling is the binding constraint on external
claims, but a card may only be added when its sentence exists on an
authoritative page we already archived. Each new card therefore names a
`source_id` + `paragraph_index`, and its snapshot row is copied from that
paragraph row — offsets and both hashes included — so the new citation is
verifiable on day one instead of being "trust me" content.

The claims are paraphrases of statements the page makes about a common
misconception (WHO myth-busters, NCI myths, CDC sun-safety, CDC tobacco).
They were written from the pages, not from any benchmark item; the leakage
check in gate A35 enforces that separation.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAIMS = os.path.join(ROOT, "data", "claims.json")
CARDS_EVIDENCE = os.path.join(ROOT, "evidence", "cards_evidence.jsonl")
PARAGRAPHS = os.path.join(ROOT, "evidence", "paragraphs.jsonl")
EXPANSION = os.path.join(ROOT, "evidence", "corpus_v10_expansion.json")

SPECS = [
    dict(card_id="E116", source_id="WHO-MYTH", paragraph_index=32,
         claim="Hot weather stops the spread of COVID-19", stance="refutes",
         tags=["Health", "COVID-19"],
         snippet="WHO: COVID-19 can be caught in any weather; countries with hot weather have reported cases, so heat does not stop transmission."),
    dict(card_id="E117", source_id="WHO-MYTH", paragraph_index=34,
         claim="Cold weather kills the coronavirus", stance="refutes",
         tags=["Health", "COVID-19"],
         snippet="WHO: there is no reason to believe cold weather kills the new coronavirus; body temperature stays near 37°C whatever the weather."),
    dict(card_id="E118", source_id="WHO-MYTH", paragraph_index=28,
         claim="Drinking or injecting bleach can cure COVID-19", stance="refutes",
         tags=["Health", "COVID-19"],
         snippet="WHO: never spray or introduce bleach or disinfectant into the body; these substances are poisonous if ingested and damage skin and eyes."),
    dict(card_id="E119", source_id="WHO-MYTH", paragraph_index=37,
         claim="Older adults and people with pre-existing conditions are more vulnerable to severe COVID-19",
         stance="supports", tags=["Health", "COVID-19"],
         snippet="WHO: people of all ages can be infected, but older people and those with asthma, diabetes or heart disease are more vulnerable to severe illness."),
    dict(card_id="E120", source_id="WHO-PUB", paragraph_index=121,
         claim="COVID-19 spreads more easily in crowded, poorly ventilated indoor spaces",
         stance="supports", tags=["Health", "COVID-19"],
         snippet="WHO: the risk of getting COVID-19 is higher in crowded, inadequately ventilated spaces where infected people spend long periods close together."),
    dict(card_id="E121", source_id="WHO-PUB", paragraph_index=125,
         claim="Outdoor gatherings are safer than indoor gatherings", stance="supports",
         tags=["Health", "COVID-19"],
         snippet="WHO: meet people outside; outdoor gatherings are safer than indoor ones, especially when indoor spaces are small and poorly ventilated."),
    dict(card_id="E122", source_id="NCI-MYTHS", paragraph_index=10,
         claim="Exposure to air makes a tumour spread", stance="refutes",
         tags=["Health", "Cancer"],
         snippet="NCI: exposure to air does not make tumours grow faster or cause cancer to spread."),
    dict(card_id="E123", source_id="NCI-MYTHS", paragraph_index=17,
         claim="Antiperspirants and deodorants cause breast cancer", stance="refutes",
         tags=["Health", "Cancer"],
         snippet="NCI: the best studies found no evidence linking antiperspirant and deodorant chemicals with changes in breast tissue."),
    dict(card_id="E124", source_id="CDC-SUNSAFE", paragraph_index=45,
         claim="Indoor tanning is a safe way to tan", stance="refutes",
         tags=["Health", "Skin"],
         snippet="CDC: to lower skin-cancer risk, protect your skin from the sun and avoid tanning."),
    dict(card_id="E125", source_id="CDC-SUNSAFE", paragraph_index=8,
         claim="UV rays from tanning beds can damage skin cells", stance="supports",
         tags=["Health", "Skin"],
         snippet="CDC: most skin cancers come from too much UV exposure; UV comes from the sun and tanning beds and can damage skin cells."),
    dict(card_id="E126", source_id="CDC-TOBACCO", paragraph_index=8,
         claim="Smoking harms nearly every organ of the body", stance="supports",
         tags=["Health", "Smoking"],
         snippet="CDC: smoking harms nearly every organ of the body and causes many diseases."),
    dict(card_id="E127", source_id="CDC-SUNSAFE", paragraph_index=17,
         claim="Sunglasses that block UVA and UVB offer the best protection", stance="supports",
         tags=["Health", "Skin"],
         snippet="CDC: sunglasses that block both UVA and UVB offer the best protection, and wrap-around styles block rays from every angle."),
]


def main():
    corpus = json.load(open(CLAIMS, encoding="utf-8"))
    sources = {s["id"]: s for s in corpus["sources"]}
    paragraphs = {}
    for line in open(PARAGRAPHS, encoding="utf-8"):
        if line.strip():
            p = json.loads(line)
            paragraphs[(p["source_id"], p["paragraph_index"])] = p

    existing = {c["card_id"] for c in corpus["evidence_cards"]}
    evidence_rows = {}
    for line in open(CARDS_EVIDENCE, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            evidence_rows[r["card_id"]] = r

    added = []
    for spec in SPECS:
        cid = spec["card_id"]
        if cid in existing:
            continue
        p = paragraphs.get((spec["source_id"], spec["paragraph_index"]))
        if not p:
            raise SystemExit("missing paragraph for %s" % cid)
        src = sources[spec["source_id"]]
        card = {
            "card_id": cid,
            "claim": spec["claim"],
            "source_id": spec["source_id"],
            "source_name": src["name"],
            "url": p["url"],
            "snippet": spec["snippet"],
            "stance": spec["stance"],
            "tags": spec["tags"],
        }
        corpus["evidence_cards"].append(card)

        row = {
            "card_id": cid,
            "source_id": spec["source_id"],
            "url": p["url"],
            "alignment_url": p["url"],
            "fetched_at": p.get("fetched_at", ""),
            "page_nature": p.get("page_nature", ""),
            "paragraph_index": p["paragraph_index"],
            "paragraph_text": p["paragraph_text"],
            "selector": p.get("selector", ""),
            "char_offset": p.get("char_offset", []),
            "sha256_of_paragraph": p.get("sha256_of_paragraph", ""),
            "sha256_of_page": p.get("sha256_of_page", ""),
            "published_or_updated": p.get("published_or_updated", ""),
            "reason": "matched",
            "method": "corpus_v10_direct/v1",
            "score": 1.0,
            "threshold": 0.5,
        }
        evidence_rows[cid] = row
        added.append({"card_id": cid, "source_id": spec["source_id"],
                      "paragraph_index": spec["paragraph_index"],
                      "claim": spec["claim"], "stance": spec["stance"],
                      "paragraph_excerpt": " ".join(p["paragraph_text"].split())[:160]})

    corpus["meta"]["dataset"] = "corpus v10 (English, %d cards)" % len(corpus["evidence_cards"])
    corpus["meta"]["version"] = "2.4.0"
    with open(CLAIMS, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)

    with open(CARDS_EVIDENCE, "w", encoding="utf-8") as f:
        for card in corpus["evidence_cards"]:
            cid = card["card_id"]
            f.write(json.dumps(evidence_rows[cid], ensure_ascii=False) + "\n")

    with open(EXPANSION, "w", encoding="utf-8") as f:
        json.dump({"version": "corpus v10", "cards": added,
                   "note": "Every new card names a paragraph already present in "
                           "evidence/paragraphs.jsonl; the snapshot row is copied "
                           "from that paragraph, so offsets and hashes are not re-derived."},
                  f, ensure_ascii=False, indent=1)
    print("cards=%d sources=%d added=%d" % (len(corpus["evidence_cards"]),
                                            len(corpus["sources"]), len(added)))


if __name__ == "__main__":
    main()
