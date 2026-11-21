"""Build the guard benchmark set (v14.2, direction 1).

The golden set measures *deciding* common claims. The guards - dose, percent,
relation, population, attribute, prohibition - were only tested by hardcoded
probes inside individual gates, which means the guard suite itself had no
held-out data. This file is that held-out data: one row per guard family, written
from what a careful reader would demand, not from the kernel's current output.

Each probe declares:
  guard      which family it belongs to
  text       the claim
  atoms      how many independent atoms the splitter must produce
  verdict    the expected verdict for the first atom
  cards      the card ids that may be cited (exact list)
  near       expected (card_id, reason_code) of the closest rejected card, or null
  note       why that is the defensible answer, in one line
"""
import io, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "guard_set.json")


def probe(pid, guard, text, verdict, cards, near, note, atoms=1):
    return {"id": pid, "guard": guard, "text": text, "atoms": atoms,
            "verdict": verdict, "cards": cards, "near": near, "note": note}


PROBES = [
    # ---- dose: a card about one amount cannot settle another amount ----------
    probe("H01", "dose", "Folic acid 200 mcg daily prevents neural tube defects.",
          "undetermined", [], ["E087", "different_quantity"],
          "E087 states 400 mcg; 200 mcg is a different dose, so its stance is out of scope."),
    probe("H02", "dose", "Folic acid 800 mcg daily prevents neural tube defects.",
          "undetermined", [], ["E087", "different_quantity"],
          "Same card, a different amount. A higher dose is not entailed by a card about 400 mcg."),
    probe("H03", "dose", "Vitamin D above 40,000 IU per day is not recommended.",
          "undetermined", [], ["E088", "different_quantity"],
          "E088 gives the magnitude as 4,000 IU; 40,000 IU is ten times that, not a rounding."),
    probe("H04", "dose", "Folic acid 400 mcg daily prevents neural tube defects in men.",
          "undetermined", [], None,
          "The card is population-unmarked and the claim narrows to men, so the scope guard refuses."),
    probe("H05", "dose", "Folic acid 400 mcg daily prevents neural tube defects.",
          "supported", ["E087"], None,
          "Control: same dose, same subject, and the card states it."),
    # ---- percent ------------------------------------------------------------
    probe("H06", "percent", "A hand sanitizer that contains 40% alcohol cleans hands well.",
          "undetermined", [], ["E081", "different_predicate"],
          "The poisoning card is about a harm, not about whether the product cleans; E090's "
          "efficacy threshold is not reachable from a 40% claim, so nothing decides it."),
    probe("H07", "percent", "A hand sanitizer that contains 60% alcohol cleans hands well.",
          "supported", ["E090"], None,
          "Control: 60% is the card's own threshold."),
    # ---- relation: adjacent topic, different proposition ---------------------
    probe("H08", "relation", "Coffee prevents cancer.",
          "undetermined", [], ["E086", "different_relation"],
          "A card that coffee causes cancer cannot decide the opposite relation."),
    probe("H09", "relation", "Coffee causes cancer.",
          "refuted", ["E086"], None,
          "Control: the relation matches the card, and the source refutes it."),
    probe("H10", "relation", "Vitamin C cures the flu.",
          "undetermined", [], None,
          "Curing is not preventing: the vitamin C cards are about colds, and none states a cure."),
    probe("H11", "relation", "Alcohol gel rubbed into the hands stops influenza from spreading.",
          "undetermined", [], ["E001", "different_relation"],
          "An object word (spread) must not make a vaccine-side-effect card decide a prevention claim."),
    # ---- population ---------------------------------------------------------
    probe("H12", "population", "Coffee causes cancer in children.",
          "undetermined", [], ["E086", "different_population"],
          "The card is about adults; a paediatric version is a different proposition."),
    probe("H13", "population", "MSG causes headaches in pregnant women.",
          "undetermined", [], ["E072", "different_population"],
          "A pregnancy card cannot decide a general MSG claim and vice versa."),
    probe("H14", "population", "Vaccination against flu is unsafe for pregnant women.",
          "refuted", ["E009"], None,
          "Control: the eligibility card is exactly about this population."),
    probe("H15", "population", "A baby's immune system is overwhelmed by vaccines.",
          "refuted", ["E041"], None,
          "Control: the card is about infants and refutes it."),
    # ---- attribute: broad safety claim vs one narrow harm -------------------
    probe("H16", "attribute", "Flu vaccines are safe.",
          "undetermined", [], ["E001", "different_predicate"],
          "A refuted side-effect claim is not proof of general safety; the corpus has no safety card."),
    probe("H17", "attribute", "Alcohol hand sanitizer is safe for children.",
          "undetermined", [], None,
          "No card states paediatric safety, so the broad attribute cannot be decided."),
    # ---- prohibition --------------------------------------------------------
    probe("H18", "prohibition", "Taking more than 4,000 IU of vitamin D each day is not advised.",
          "supported", ["E088"], None,
          "A prohibition is not a logical negation: the upper-limit card supports it."),
    probe("H19", "prohibition", "Taking more than 4,000 IU of vitamin D per day is recommended.",
          "refuted", ["E088"], None,
          "Inverted control: the same card refutes the positive form."),
    # ---- negation -----------------------------------------------------------
    probe("H20", "negation", "Our planet is not round.",
          "refuted", ["E004"], None,
          "Polarity flips the supporting card into a refutation."),
    probe("H21", "negation", "It is not true that the Earth is flat.",
          "supported", ["E082"], None,
          "One negation inverts the refuting card back into support."),
    # ---- decomposition ------------------------------------------------------
    probe("H22", "split", "The Earth is round and the Earth is flat.",
          "supported", ["E004"], None,
          "A contradictory compound splits; the first atom keeps its own verdict (second is refuted).",
          atoms=2),
    probe("H23", "split", "Antibiotics can cure both the common cold and influenza.",
          "refuted", ["E002"], None,
          "A coordinated object stays whole; the claim is not truncated to cold.",
          atoms=1),
    # ---- separator ----------------------------------------------------------
    probe("H24", "separator", "Taking more than 4,000 IU of vitamin D a day is not advised.",
          "supported", ["E088"], None,
          "A thousands separator belongs to the number, not to a clause boundary."),
    probe("H25", "separator", "4,000 IU of vitamin D per day is not recommended for adults.",
          "undetermined", [], None,
          "The card gives no adult-specific statement, so the narrowed claim refuses."),
    # ---- controls: the guards must not over-refuse --------------------------
    probe("H26", "control", "The Earth is round.",
          "supported", ["E004"], None, "Plain control."),
    probe("H27", "control", "A flu shot infects you with the flu.",
          "refuted", ["E001"], None, "Plain control."),
    probe("H28", "control", "Antibiotics can treat a common cold.",
          "refuted", ["E002"], None, "Plain control."),
    probe("H29", "control", "Soap and water handwashing prevents respiratory and diarrheal infections.",
          "supported", ["E089"], None, "Plain control for the hygiene card."),
    probe("H30", "control", "Eating carrots supports eye health.",
          "supported", ["E071"], None, "Plain control for the vision card."),
    # ---- polarity: the same proposition, stated from the other side ----------
    probe("H31", "polarity", "Antibiotics cause side effects.",
          "supported", ["E092"], None,
          "E092 reads \"antibiotics have no side effects\", so a positive restatement of the "
          "opposite must land supported. Checking only the claim's own negation would report refuted."),
    probe("H32", "polarity", "Antibiotics do not cause side effects.",
          "refuted", ["E092"], None,
          "The claim repeats the card, so the negation must not be applied twice."),
    # ---- strength: an absolute is not settled by a hedge --------------------
    probe("H33", "strength", "Antibiotics never have side effects.",
          "refuted", ["E092"], None,
          "E093 says side effects are rare in children: rare is not never, so it is excluded "
          "instead of lending support to an absolute."),
    probe("H34", "strength", "Smoking always causes lung cancer.",
          "supported", ["E106"], None,
          "Control: the card's own statement is absolute enough for an absolute claim."),
    # ---- subject: the object of one card is not a subject of the next --------
    probe("H35", "subject", "Cancer causes death.",
          "undetermined", [], ["E086", "different_subject"],
          "Cancer is E086's object, not its subject: coffee causing cancer says nothing about "
          "what cancer causes, so the chain link may not be borrowed from the card."),
    probe("H36", "subject", "Smoking causes lung cancer.",
          "supported", ["E106"], None,
          "Control: the card's subject is the claim's subject, so it still decides."),
]

DOC = {
    "meta": {
        "dataset": "guard benchmark v1 (English, %d probes)" % len(PROBES),
        "design": ("One row per guard family, written from the source text before the kernel is run. "
                   "The golden set measures deciding; this set measures refusing for the right reason, "
                   "with four plain controls so a guard that refuses everything cannot pass."),
    },
    "probes": PROBES,
}

io.open(P, "w", encoding="utf-8").write(json.dumps(DOC, ensure_ascii=False, indent=2) + "\n")
print("wrote guard_set.json with %d probes" % len(PROBES))
