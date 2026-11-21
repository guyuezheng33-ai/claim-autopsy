"""Restate E088 affirmatively (v14.1).

The card paraphrased the NIH tolerable upper intake level as "is not recommended".
A negative card claim is the one shape the stance machinery cannot score safely:
a negated *claim* about the same sentence needs no inversion, but the kernel
inverts every card stance for a negated claim, so an exact restatement was read
as evidence against itself. Restating the card affirmatively ("exceeds the safe
upper limit") keeps the same sourced fact, removes the ambiguity, and lets a
quantity guard do the work instead.
"""
import io, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "claims.json")

NEW_CLAIM = "Taking more than 4,000 IU of vitamin D per day exceeds the safe upper limit"
NEW_SNIP = ("NIH ODS: the tolerable upper intake level for vitamin D ranges from 25 to 100 mcg "
            "(1,000-4,000 IU) per day depending on age; above that level the risk of toxicity rises.")

d = json.load(io.open(P, encoding="utf-8"))
for c in d["evidence_cards"]:
    if c["card_id"] == "E088":
        if c["claim"] == NEW_CLAIM and c["snippet"] == NEW_SNIP:
            print("E088 already restated")
        else:
            c["claim"] = NEW_CLAIM
            c["snippet"] = NEW_SNIP
            io.open(P, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
            print("E088 restated")
        break
