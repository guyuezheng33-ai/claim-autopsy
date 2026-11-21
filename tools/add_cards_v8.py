"""One-off corpus patch: add four verified cards (v8 expansion).

Every card below was written from the page it cites, fetched during this session;
the snippet is a paraphrase, not a quotation, matching the corpus notice. Run once:
`python tools/add_cards_v8.py`.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "claims.json")

NEW_SOURCES = [
    {"id": "CDC-FOLIC", "name": "US CDC · About folic acid",
     "url": "https://www.cdc.gov/folic-acid/about/index.html",
     "url_status": "verified_2026_11_20", "authority": "National public health agency"},
    {"id": "NIH-ODS-VITD", "name": "US NIH ODS · Vitamin D fact sheet",
     "url": "https://ods.od.nih.gov/factsheets/VitaminD-HealthProfessional/",
     "url_status": "verified_2026_11_20", "authority": "National institutes of health"},
    {"id": "CDC-CLEANHANDS", "name": "US CDC · About handwashing",
     "url": "https://www.cdc.gov/clean-hands/about/index.html",
     "url_status": "verified_2026_11_20", "authority": "National public health agency"},
]

NEW_CARDS = [
    {"card_id": "E087",
     "claim": "Taking 400 mcg of folic acid daily helps prevent neural tube defects",
     "source_id": "CDC-FOLIC", "source_name": "US CDC · About folic acid",
     "url": "https://www.cdc.gov/folic-acid/about/index.html",
     "snippet": "CDC: 400 micrograms (mcg) of folic acid daily can help prevent serious birth defects called neural tube defects, and that amount is what the US Public Health Service recommends for anyone who could become pregnant.",
     "stance": "supports", "tags": ["Health", "Pregnancy", "Nutrition"],
     "requires_all": ["folic"]},
    {"card_id": "E088",
     "claim": "Taking more than 4,000 IU of vitamin D per day is not recommended",
     "source_id": "NIH-ODS-VITD", "source_name": "US NIH ODS · Vitamin D fact sheet",
     "url": "https://ods.od.nih.gov/factsheets/VitaminD-HealthProfessional/",
     "snippet": "NIH ODS: the tolerable upper intake level for vitamin D ranges from 25 to 100 mcg (1,000-4,000 IU) per day depending on age; vitamin D toxicity is almost always the result of excessive supplement intake.",
     "stance": "supports", "tags": ["Health", "Nutrition", "Dose"],
     "requires_all": ["vitamin d", "iu"]},
    {"card_id": "E089",
     "claim": "Washing hands with soap prevents the spread of respiratory and diarrheal infections",
     "source_id": "CDC-CLEANHANDS", "source_name": "US CDC · About handwashing",
     "url": "https://www.cdc.gov/clean-hands/about/index.html",
     "snippet": "CDC: washing hands can keep you healthy and prevent the spread of respiratory and diarrheal infections, and handwashing with soap is one of the best ways to stay healthy.",
     "stance": "supports", "tags": ["Health", "Hygiene"]},
    {"card_id": "E090",
     "claim": "Hand sanitizer needs at least 60% alcohol to work",
     "source_id": "CDC-CLEANHANDS", "source_name": "US CDC · About handwashing",
     "url": "https://www.cdc.gov/clean-hands/about/index.html",
     "snippet": "CDC: if soap and water are not available, use an alcohol-based hand sanitizer that contains at least 60% alcohol; the label tells you whether it does.",
     "stance": "supports", "tags": ["Health", "Hygiene"],
     "requires_all": ["sanitizer"]},
]


def main():
    with open(PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    have_src = {s["id"] for s in corpus["sources"]}
    for s in NEW_SOURCES:
        if s["id"] not in have_src:
            corpus["sources"].append(s)
    have_card = {c["card_id"] for c in corpus["evidence_cards"]}
    for c in NEW_CARDS:
        if c["card_id"] not in have_card:
            corpus["evidence_cards"].append(c)
    corpus["meta"]["dataset"] = "Claim Autopsy built-in demonstration corpus v8 (English, %d cards)" % len(corpus["evidence_cards"])
    corpus["meta"]["version"] = "2.2.0"
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)
    print("cards=%d sources=%d" % (len(corpus["evidence_cards"]), len(corpus["sources"])))


if __name__ == "__main__":
    main()
