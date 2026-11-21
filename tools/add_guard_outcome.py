"""Append the three outcome-class probes to data/guard_set.json (idempotent)."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "guard_set.json")

PROBES = [
    {"id": "H37", "guard": "outcome",
     "text": "Dry indoor air may encourage coronavirus spread",
     "atoms": 1, "verdict": "undetermined", "cards": [],
     "near": ["E122", "different_object"],
     "note": "E122 asserts that exposure to air spreads a tumour. Air and spread are the only "
             "shared words; the conditions are different, so the card cannot decide a coronavirus "
             "claim. This exact pair was answered refuted on the dev slice before the outcome "
             "vocabulary knew the word tumour."},
    {"id": "H38", "guard": "control",
     "text": "Exposure to air makes a tumour spread",
     "atoms": 1, "verdict": "refuted", "cards": ["E122"],
     "near": [],
     "note": "The control for H37: the same card still decides the claim it is actually about. "
             "A guard that refused this as well would be a blanket refusal, not a comparison."},
    {"id": "H39", "guard": "control",
     "text": "Cold weather kills the coronavirus",
     "atoms": 1, "verdict": "refuted", "cards": ["E117"],
     "near": [],
     "note": "The second control: coronavirus and covid are now one condition class, so the "
             "weather cards must keep deciding weather claims. Merging the two words was required "
             "by this fix; refusing these as well would have paid for precision with coverage "
             "that already worked."},
]


def main():
    with open(PATH, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    have = {p["id"] for p in doc["probes"]}
    added = [p for p in PROBES if p["id"] not in have]
    doc["probes"].extend(added)
    doc["meta"]["count"] = len(doc["probes"])
    with open(PATH, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print("guard probes: %d (added %d)" % (len(doc["probes"]), len(added)))


if __name__ == "__main__":
    main()
