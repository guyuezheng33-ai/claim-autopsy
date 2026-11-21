"""Append 25 held-out cases for the v9 cards (G69-G93), idempotent by id.

Each case is a reworded version of a card, never a copy: the point is to test
whether the wording of the claim, not its identity, drives the verdict.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "golden_set.json")

CASES = [
    ("G69", "Antibiotics do not kill viruses.", "supported", "E091", "Health"),
    ("G70", "Antibiotics never produce side effects.", "refuted", "E092", "Health"),
    ("G71", "Antibiotic side effects send few children to the emergency room.", "refuted", "E093", "Health"),
    ("G72", "Thirty minutes of moderate activity on five days a week meets the adult guideline.", "supported", "E094", "Health"),
    ("G73", "Adults need muscle-strengthening exercise at least twice a week.", "supported", "E095", "Health"),
    ("G74", "Seventy-five minutes of vigorous activity each week counts for adults.", "supported", "E096", "Health"),
    ("G75", "Adults should sleep seven hours or more each night.", "supported", "E097", "Health"),
    ("G76", "Teenagers need eight to ten hours of sleep a day.", "supported", "E098", "Health"),
    ("G77", "Adults should keep sodium under 2,300 mg a day.", "supported", "E099", "Health"),
    ("G78", "Eating too much salt raises blood pressure.", "supported", "E100", "Health"),
    ("G79", "Most skin cancers come from too much ultraviolet light.", "supported", "E101", "Health"),
    ("G80", "Sunscreen should be broad-spectrum with SPF 15 or higher.", "supported", "E102", "Health"),
    ("G81", "Sunscreen is safe for a two-month-old baby.", "refuted", "E103", "Health"),
    ("G82", "Fluoride in drinking water prevents tooth decay.", "supported", "E104", "Health"),
    ("G83", "Water fluoridation cuts cavities by about a quarter.", "supported", "E105", "Health"),
    ("G84", "Smoking can cause lung cancer.", "supported", "E106", "Health"),
    ("G85", "Secondhand smoke can give nonsmokers lung cancer.", "supported", "E107", "Health"),
    ("G86", "Stopping smoking lowers the risk of cancer.", "supported", "E108", "Health"),
    ("G87", "Smoking only harms the lungs.", "refuted", "E109", "Health"),
    ("G88", "Two MMR doses are about 97% effective against measles.", "supported", "E110", "Health"),
    ("G89", "Measles is only mildly contagious.", "refuted", "E112", "Health"),
    ("G90", "Aspartame causes cancer in humans.", "refuted", "E113", "Health"),
    ("G91", "Mobile phones cause brain tumours.", "refuted", "E114", "Health"),
    ("G92", "Antibiotics cannot cause serious infections.", "refuted", "E115", "Health"),
    ("G93", "Adults need at least 150 minutes of moderate exercise a week.", "supported", "E094", "Health"),
]


def main():
    with open(PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    have = {c["id"] for c in data["cases"]}
    added = 0
    for cid, text, expected, card, category in CASES:
        if cid in have:
            continue
        data["cases"].append({"id": cid, "text": text, "expected": expected,
                              "category": category, "expect_card": card,
                              "note": "held-out case for a v9 card; wording differs from the card."})
        added += 1
    data["meta"]["dataset"] = "held-out golden set v6 (%d cases)" % len(data["cases"])
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("added %d cases; total %d" % (added, len(data["cases"])))


if __name__ == "__main__":
    main()
