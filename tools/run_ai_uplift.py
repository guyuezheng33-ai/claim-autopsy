"""The real-increment baseline: rules must lose, AI must win.

For each case we first run the rules-only docket. A case only counts if rules
return `not_in_source`. We then prove the mechanism with reference anchors:
the same quotation, the same judge, only the bridged vocabulary changed. A
live run records what the local model actually proposes, including failures.
"""
import argparse
import copy
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import court, llm

CASES = os.path.join(ROOT, "data", "ai_uplift_cases.json")
OUT = os.path.join(ROOT, "evidence", "ai_uplift.json")


def load_cases():
    with open(CASES, "r", encoding="utf-8") as f:
        return json.load(f)["cases"]


def dossier(claim, source, args, mode, model):
    return court.make_dossier(claim, source, "candidate source",
                              ai_arguments=args, mode=mode, model=model)


def run_case(case, live):
    claim, source, side = case["claim"], case["source"], case["side"]
    packet = court.build_evidence(source, "candidate source")
    eid = packet["sentences"][0]["evidence_id"]
    relation = "supports" if side == "defense" else "contradicts"

    rules = court.make_dossier(claim, source, "candidate source")
    rules_verdict = rules["atoms"][0]["verdict"]

    ref_args = {side: [{
        "atom_id": "A1", "evidence_id": eid, "quote": source,
        "relation": relation, "rationale": "reference bridge",
        "anchors": case["reference_anchors"],
    }]}
    ref = dossier(claim, source, ref_args, "ai", "reference-anchors")
    ref_verdict = ref["atoms"][0]["verdict"]
    ref_arg = ref["arguments"][0]
    ref_ok = (rules_verdict == "not_in_source"
              and ref_verdict == case["expected_verdict"]
              and bool(ref_arg.get("bridge")))

    out = {
        "id": case["id"],
        "claim": claim,
        "source": source,
        "side": side,
        "expected_verdict": case["expected_verdict"],
        "rules_verdict": rules_verdict,
        "reference_verdict": ref_verdict,
        "reference_bridge": ref_arg.get("bridge"),
        "reference_ok": ref_ok,
    }
    if not live:
        return out

    ai_args, meta = llm.collect_ai_arguments([claim], packet)
    live_d = dossier(claim, source, ai_args, "ai", llm.active_model())
    live_verdict = live_d["atoms"][0]["verdict"]
    ai_records = [a for a in live_d.get("arguments", []) if a.get("origin") == "ai"]
    accepted = [a for a in ai_records if a.get("status") == "accepted"]
    bridges = [a for a in accepted if a.get("bridge")]

    # Causality control: the exact same model arguments, anchors removed.
    no_anchor_args = copy.deepcopy(ai_args)
    for side_args in no_anchor_args.values():
        for a in side_args:
            a.pop("anchors", None)
    control = dossier(claim, source, no_anchor_args, "ai", llm.active_model())
    control_verdict = control["atoms"][0]["verdict"]

    out.update({
        "live_verdict": live_verdict,
        "live_uplift": rules_verdict == "not_in_source" and live_verdict == case["expected_verdict"],
        "model": meta.get("model") or llm.active_model(),
        "latency_ms": (meta.get("prosecution", {}).get("latency_ms", 0)
                       + meta.get("defense", {}).get("latency_ms", 0)),
        "ai_arguments": len(ai_records),
        "accepted_ai_arguments": len(accepted),
        "bridge_count": len(bridges),
        "bridge": bridges[0].get("bridge") if bridges else None,
        "struck": [{"side": a.get("side"), "codes": a.get("strike_codes"),
                    "anchors_requested": a.get("anchors_requested")}
                   for a in ai_records if a.get("status") == "struck"],
        "without_anchors_verdict": control_verdict,
        "anchor_is_causal": (control_verdict == "not_in_source"
                             and live_verdict == case["expected_verdict"]),
    })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="also run the local model")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    live = args.live and llm.available()
    cases = [run_case(c, live) for c in load_cases()]
    reference_pass = sum(1 for c in cases if c["reference_ok"])
    rule_loss = sum(1 for c in cases if c["rules_verdict"] == "not_in_source")
    if live:
        model_pass = sum(1 for c in cases if c.get("live_uplift"))
        causal = sum(1 for c in cases if c.get("anchor_is_causal"))
        control_ok = sum(1 for c in cases if c.get("without_anchors_verdict") == "not_in_source")
    else:
        model_pass = causal = control_ok = None
    payload = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "benchmark": "rules-lose / anchored-AI-wins",
        "model": (llm.active_model() if live else None),
        "cases": cases,
        "summary": {
            "cases": len(cases),
            "rule_loss": rule_loss,
            "reference_pass": reference_pass,
            "model_live": live,
            "model_uplift": model_pass,
            "anchor_causal": causal,
            "without_anchors_still_not_in_source": control_ok,
        },
        "note": ("reference_pass proves the bridge mechanism on fixed anchors. "
                 "model_uplift is the honest live result; a failed case is kept, not hidden."),
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(json.dumps(payload["summary"], indent=2))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
