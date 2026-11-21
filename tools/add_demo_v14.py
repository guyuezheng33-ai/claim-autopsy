"""Add the v14 contradictory-atoms demo (idempotent)."""
import io, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "claims.json")
DEMO = {"id": "DEMO-9", "label": "Two atoms that cannot both be true",
        "text": "The Earth is round and the Earth is flat."}

d = json.load(io.open(P, encoding="utf-8"))
demos = d["demo_inputs"]
if not any(x.get("id") == "DEMO-9" for x in demos):
    demos.append(DEMO)
    d["meta"]["dataset"] = "corpus v8 (English, %d cards)" % len(d["evidence_cards"])
    io.open(P, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    print("added DEMO-9; demos=%d" % len(demos))
else:
    print("DEMO-9 already present; demos=%d" % len(demos))
