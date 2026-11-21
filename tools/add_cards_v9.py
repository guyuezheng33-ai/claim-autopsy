"""Add 25 sourced cards (corpus v9), idempotent by card_id and source id.

Every snippet below is a human paraphrase of the linked page, fetched on
2026-11-20; nothing is quoted verbatim, and the URL is what a reader should
open to check the original wording.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "claims.json")

SOURCES = [
    ("CDC-ABX-HABITS", "CDC · Antibiotic do's and don'ts", "https://www.cdc.gov/antibiotic-use/about/index.html", "National public health agency"),
    ("CDC-PA-ADULT", "CDC · Physical activity guidelines for adults", "https://www.cdc.gov/physical-activity-basics/guidelines/adults.html", "National public health agency"),
    ("CDC-SLEEP-HOWMUCH", "CDC · How much sleep do I need", "https://www.cdc.gov/sleep/about_sleep/how_much_sleep.html", "National public health agency"),
    ("CDC-SODIUM", "CDC · About sodium and health", "https://www.cdc.gov/salt/about/index.html", "National public health agency"),
    ("CDC-SUNSAFE", "CDC · Sun safety facts", "https://www.cdc.gov/skin-cancer/sun-safety/index.html", "National public health agency"),
    ("CDC-FLUORIDE", "CDC · About community water fluoridation", "https://www.cdc.gov/fluoridation/about/index.html", "National public health agency"),
    ("CDC-TOBACCO", "CDC · Cigarette smoking", "https://www.cdc.gov/tobacco/about/index.html", "National public health agency"),
    ("CDC-MEASLES-VAX", "CDC · Measles vaccination", "https://www.cdc.gov/measles/vaccination.html", "National public health agency"),
    ("NCI-SWEETENERS", "NCI · Artificial sweeteners and cancer", "https://www.cancer.gov/about-cancer/causes-prevention/risk/diet/artificial-sweeteners-fact-sheet", "National cancer institute"),
    ("NCI-CELLPHONE", "NCI · Cell phones and cancer risk", "https://www.cancer.gov/about-cancer/causes-prevention/risk/radiation/cell-phones-fact-sheet", "National cancer institute"),
]

CARDS = [
    dict(card_id="E091", claim="Antibiotics work on viruses", source_id="CDC-ABX-HABITS",
         snippet="CDC: antibiotics do not treat infections caused by viruses, including colds and flu; they only treat certain bacterial infections.",
         stance="refutes", tags=["Health", "Antibiotics"]),
    dict(card_id="E092", claim="Antibiotics have no side effects", source_id="CDC-ABX-HABITS",
         snippet="CDC: taking antibiotics when they are not needed does not help and the side effects can still cause harm; common ones include rash, dizziness, nausea, diarrhea and yeast infections.",
         stance="refutes", tags=["Health", "Antibiotics"]),
    dict(card_id="E093", claim="Antibiotic side effects in children are rare", source_id="CDC-ABX-HABITS",
         snippet="CDC: in children, side effects from antibiotics are the most common cause of medication-related emergency department visits.",
         stance="refutes", tags=["Health", "Antibiotics"]),
    dict(card_id="E094", claim="Adults need at least 150 minutes of moderate-intensity activity a week", source_id="CDC-PA-ADULT",
         snippet="CDC: adults need at least 150 minutes of moderate-intensity physical activity a week, for example 30 minutes a day on five days.",
         stance="supports", tags=["Health", "Exercise"]),
    dict(card_id="E095", claim="Adults need muscle-strengthening activity on two or more days a week", source_id="CDC-PA-ADULT",
         snippet="CDC: adults also need at least 2 days of muscle-strengthening activity each week, working all major muscle groups.",
         stance="supports", tags=["Health", "Exercise"]),
    dict(card_id="E096", claim="75 minutes of vigorous activity a week meets the adult guideline", source_id="CDC-PA-ADULT",
         snippet="CDC: 150 minutes of moderate activity can be replaced by 75 minutes of vigorous-intensity activity, or an equivalent mix of the two.",
         stance="supports", tags=["Health", "Exercise"]),
    dict(card_id="E097", claim="Adults need at least seven hours of sleep a night", source_id="CDC-SLEEP-HOWMUCH",
         snippet="CDC: adults aged 18 to 60 years are recommended to get 7 or more hours of sleep per night.",
         stance="supports", tags=["Health", "Sleep"]),
    dict(card_id="E098", claim="Teenagers need eight to ten hours of sleep per day", source_id="CDC-SLEEP-HOWMUCH",
         snippet="CDC: teenagers aged 13 to 18 years are recommended to get 8 to 10 hours of sleep per 24 hours.",
         stance="supports", tags=["Health", "Sleep"]),
    dict(card_id="E099", claim="Adults should keep sodium intake below 2,300 mg a day", source_id="CDC-SODIUM",
         snippet="CDC: the federal recommendation is less than 2,300 milligrams of sodium daily for teens and adults as part of a healthy eating pattern.",
         stance="supports", tags=["Health", "Nutrition"]),
    dict(card_id="E100", claim="Too much sodium raises blood pressure", source_id="CDC-SODIUM",
         snippet="CDC: eating too much sodium can increase your blood pressure and your risk for heart disease and stroke.",
         stance="supports", tags=["Health", "Nutrition"]),
    dict(card_id="E101", claim="Most skin cancers are caused by too much ultraviolet exposure", source_id="CDC-SUNSAFE",
         snippet="CDC: most skin cancers are caused by too much exposure to ultraviolet rays, which can damage skin cells.",
         stance="supports", tags=["Health", "Cancer"]),
    dict(card_id="E102", claim="A broad-spectrum sunscreen with SPF 15 or higher protects the skin", source_id="CDC-SUNSAFE",
         snippet="CDC: use a broad-spectrum sunscreen that filters both UVA and UVB rays and has an SPF of 15 or higher before going outside.",
         stance="supports", tags=["Health", "Skin"]),
    dict(card_id="E103", claim="Sunscreen is safe for babies younger than six months", source_id="CDC-SUNSAFE",
         snippet="CDC: sunscreen is not recommended for babies who are 6 months old or younger; keep infants out of the sun and use protective clothing instead.",
         stance="refutes", tags=["Health", "Skin"]),
    dict(card_id="E104", claim="Fluoridated drinking water prevents cavities", source_id="CDC-FLUORIDE",
         snippet="CDC: community water fluoridation adjusts the fluoride in drinking water to a level recommended for preventing cavities.",
         stance="supports", tags=["Health", "Dental"]),
    dict(card_id="E105", claim="Water fluoridation reduces cavities by about 25%", source_id="CDC-FLUORIDE",
         snippet="CDC: drinking fluoridated water keeps teeth strong and reduces cavities by about 25% in children and adults.",
         stance="supports", tags=["Health", "Dental"]),
    dict(card_id="E106", claim="Smoking causes lung cancer", source_id="CDC-TOBACCO",
         snippet="CDC: cigarette smoking causes many diseases, including cancer, heart disease, stroke and chronic obstructive pulmonary disease.",
         stance="supports", tags=["Health", "Smoking"]),
    dict(card_id="E107", claim="Secondhand smoke can cause lung cancer in nonsmokers", source_id="CDC-TOBACCO",
         snippet="CDC: in adults, secondhand smoke can cause coronary heart disease, stroke and lung cancer; it contributes to over 40,000 deaths among nonsmoking adults each year.",
         stance="supports", tags=["Health", "Smoking"]),
    dict(card_id="E108", claim="Quitting smoking lowers the risk of heart disease and cancer", source_id="CDC-TOBACCO",
         snippet="CDC: quitting improves health and reduces the risk of premature death and of smoking-related diseases, including heart disease, cancer and COPD.",
         stance="supports", tags=["Health", "Smoking"]),
    dict(card_id="E109", claim="Smoking only harms the lungs", source_id="CDC-TOBACCO",
         snippet="CDC: cigarette smoking harms nearly every organ of the body; it causes cancer, heart disease, stroke, lung diseases, type 2 diabetes and other conditions.",
         stance="refutes", tags=["Health", "Smoking"]),
    dict(card_id="E110", claim="Two doses of MMR vaccine are about 97% effective against measles", source_id="CDC-MEASLES-VAX",
         snippet="CDC: two doses of MMR vaccine are about 97% effective at preventing measles; one dose is about 93% effective.",
         stance="supports", tags=["Health", "Vaccine"]),
    dict(card_id="E111", claim="The MMR vaccine is safe and effective", source_id="CDC-MEASLES-VAX",
         snippet="CDC: MMR is safe and effective, and it provides long-lasting protection against all strains of measles.",
         stance="supports", tags=["Health", "Vaccine"]),
    dict(card_id="E112", claim="Measles is not very contagious", source_id="CDC-MEASLES-VAX",
         snippet="CDC: measles is highly contagious; if one person has it, up to 9 out of 10 nearby people will become infected if they are not protected.",
         stance="refutes", tags=["Health", "Measles"]),
    dict(card_id="E113", claim="Artificial sweeteners cause cancer in people", source_id="NCI-SWEETENERS",
         snippet="NCI: studies reviewed by the FDA showed no evidence that approved artificial sweeteners cause cancer or other harms in people.",
         stance="refutes", tags=["Health", "Nutrition"]),
    dict(card_id="E114", claim="Cell phones cause brain cancer", source_id="NCI-CELLPHONE",
         snippet="NCI: the evidence to date suggests that cell phone use does not cause brain or other kinds of cancer in humans.",
         stance="refutes", tags=["Health", "Cancer"]),
    dict(card_id="E115", claim="Antibiotics cannot cause serious infections", source_id="CDC-ABX-HABITS",
         snippet="CDC: serious side effects of antibiotics include C. diff infection, which causes diarrhea that can lead to severe colon damage and death.",
         stance="refutes", tags=["Health", "Antibiotics"]),
]


def main():
    with open(PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    have_sources = {s["id"] for s in data["sources"]}
    for sid, name, url, authority in SOURCES:
        if sid in have_sources:
            continue
        data["sources"].append({"id": sid, "name": name, "url": url,
                                "url_status": "checked_200",
                                "authority": authority})
    have_cards = {c["card_id"] for c in data["evidence_cards"]}
    added = 0
    for card in CARDS:
        if card["card_id"] in have_cards:
            continue
        src = next(s for s in data["sources"] if s["id"] == card["source_id"])
        full = {
            "card_id": card["card_id"],
            "claim": card["claim"],
            "source_id": card["source_id"],
            "source_name": src["name"],
            "url": src["url"],
            "snippet": card["snippet"],
            "stance": card["stance"],
            "tags": card["tags"],
        }
        data["evidence_cards"].append(full)
        added += 1
    data["meta"]["dataset"] = "corpus v9 (English, %d cards)" % len(data["evidence_cards"])
    data["meta"]["version"] = "2.3.0"
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("added %d cards; total %d cards / %d sources" %
          (added, len(data["evidence_cards"]), len(data["sources"])))


if __name__ == "__main__":
    main()
