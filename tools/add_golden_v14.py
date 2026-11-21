"""Add eight held-out cases for the v14 corpus (G61-G68), idempotently.

These are written from the sources, not from the kernel's current output: each
expectation is the verdict a careful reader would defend from the card text
alone, and the run afterwards either agrees or exposes a defect.
"""
import io, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "golden_set.json")

NEW = [
    ("G61", "Folic acid 400 mcg every day helps prevent neural tube defects at birth.",
     "supported", "Dose", "E087 states exactly 400 mcg; the dose guard must pass it through."),
    ("G62", "Folic acid 40 mcg every day helps prevent neural tube defects at birth.",
     "undetermined", "Dose", "A card about 400 mcg cannot settle 40 mcg; refusal is the honest answer."),
    ("G63", "Taking more than 4,000 IU of vitamin D per day is not recommended.",
     "supported", "Dose", "E088 restates the NIH upper intake level; a thousands separator is not a clause break."),
    ("G64", "Vitamin D 10,000 IU a day is safe.",
     "undetermined", "Dose", "E088 is about the upper limit, not about safety at 10,000 IU, and the dose differs."),
    ("G65", "Washing hands with soap prevents respiratory and diarrheal infections.",
     "supported", "Hygiene", "E089 covers both infection classes named in the claim."),
    ("G66", "Hand sanitizer with 60% alcohol works well.",
     "supported", "Hygiene", "E090 requires at least 60%, so 60% is inside the card's scope."),
    ("G67", "Hand sanitizer with 40% alcohol works well.",
     "undetermined", "Hygiene", "The nearest card is about poisoning, not efficacy, and the dose is out of scope."),
    ("G68", "Rubbing hands with alcohol gel prevents the spread of flu.",
     "undetermined", "Hygiene", "A card about a flu shot causing flu says nothing about alcohol gel preventing it."),
]

d = json.load(io.open(P, encoding="utf-8"))
ids = {c["id"] for c in d["cases"]}
added = 0
for cid, text, exp, cat, note in NEW:
    if cid in ids:
        continue
    d["cases"].append({"id": cid, "text": text, "expected": exp, "category": cat, "note": note})
    added += 1
if added:
    d["meta"]["dataset"] = "Claim Autopsy held-out golden set v5 (English, %d cases)" % len(d["cases"])
    d["meta"]["design"] = (d["meta"]["design"].split(" Class distribution")[0]
                           + " Class distribution is deliberately skewed toward refuted because the corpus "
                             "targets common misinformation; the v5 additions cover dose, efficacy and hygiene "
                             "so the quantity and relation guards are measured, not merely present.")
    io.open(P, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
print("added %d cases; total=%d" % (added, len(d["cases"])))
