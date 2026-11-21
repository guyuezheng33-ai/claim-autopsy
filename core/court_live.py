"""Run the court with a real model and record the result.

This script never fabricates a live run. It uses a cloud key when present, or
the local Qwen2.5-3B model served by llama.cpp on loopback (1.5B is the fast
fallback). Without either it exits with `no_credentials` and writes nothing.
With a model it calls the prosecution and defence once each, lets the
deterministic judge verify every quotation, and writes an evidence file that
the submission can cite. A second local model is kept under `runs` rather than
overwriting the first: `cases` stays the 1.5B recording used by the static
replay, while `runs` holds every recorded model.
"""
import datetime
import json
import os

from . import court, llm


OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evidence", "court_live.json")


def _model_key(model):
    low = (model or "").lower()
    if "3b" in low:
        return "3b"
    if "1.5b" in low:
        return "1.5b"
    if "7b" in low:
        return "7b"
    return "cloud"


def _publish(payload, out_path):
    """Write the run, preserving other models under `runs`.

    `cases` remains the 1.5B recording the static replay has always used; a
    later 3B run is added to `runs` instead of replacing it. The root fields are
    updated only by a 1.5B run or when the file has no cases yet.
    """
    key = _model_key(payload.get("model"))
    existing = None
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = None
    if not existing or existing.get("schema") != "claim-autopsy/court-live/2":
        existing = {
            "schema": "claim-autopsy/court-live/2",
            "ok": payload.get("ok"),
            "generated_at": payload.get("generated_at"),
            "model": payload.get("model"),
            "provider": payload.get("provider"),
            "mode": payload.get("mode"),
            "cases": payload.get("cases", []),
            "summary": payload.get("summary"),
            "runs": [],
        }
    runs = [r for r in (existing.get("runs") or []) if r.get("model_key") != key]
    runs.append({
        "model_key": key,
        "model": payload.get("model"),
        "provider": payload.get("provider"),
        "generated_at": payload.get("generated_at"),
        "mode": payload.get("mode"),
        "summary": payload.get("summary"),
        "cases": payload.get("cases", []),
    })
    runs.sort(key=lambda r: ["1.5b", "3b", "7b", "cloud"].index(r.get("model_key"))
              if r.get("model_key") in ["1.5b", "3b", "7b", "cloud"] else 4)
    existing["runs"] = runs
    existing["models"] = [r.get("model") for r in runs]
    existing["summary_by_model"] = {r.get("model_key"): r.get("summary") for r in runs}
    existing["note"] = ("`cases` is the 1.5B run used by the recorded static replay. "
                        "`runs` records every local model; a later model is not substituted "
                        "into the replay.")
    if key == "1.5b" or not existing.get("cases"):
        for field in ("ok", "generated_at", "model", "provider", "mode", "cases", "summary"):
            existing[field] = payload.get(field)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
        f.write("\n")


def run(limit=6, out_path=OUT):
    if not llm.available():
        return {"ok": False, "error": "no_credentials",
                "detail": "Run `python tools/get_model.py` (local, no key) or set LLM_API_KEY; nothing was written."}
    data = court.fixtures()
    cases = []
    for case in data["cases"][:limit]:
        atoms = court.rule_split(case["claim"]) or [case["claim"]]
        atoms = atoms[:court.MAX_ATOMS]
        packet = court.build_evidence(case["source"], case.get("source_name", "live fixture"))
        ai_args, meta = llm.collect_ai_arguments(atoms, packet)
        rules = court.make_dossier(case["claim"], case["source"],
                                   case.get("source_name", "live fixture"))
        live = court.make_dossier(case["claim"], case["source"],
                                  case.get("source_name", "live fixture"),
                                  ai_arguments=ai_args, mode="ai", model=llm.active_model(),
                                  trace=[{"step": "advocates", "meta": meta}])
        expected = case["expected"] if isinstance(case["expected"], list) else [case["expected"]]
        live["__source"] = case["source"]
        live["replay_mode"] = "live-run-recording"
        live["demo_label"] = "RECORDED LIVE AI RUN · %s" % llm.active_model()
        cases.append({
            "id": case["id"],
            "replay_key": case["id"].split("-", 2)[2].replace("-", "_"),
            "claim": case["claim"],
            "source": case["source"],
            "expected": expected,
            "rules": {"verdicts": [a["verdict"] for a in rules["atoms"]],
                      "run_id": rules["receipt"]["run_id"]},
            "live": {"verdicts": [a["verdict"] for a in live["atoms"]],
                     "run_id": live["receipt"]["run_id"],
                     "arguments": live["arguments"],
                     "summary": live["summary"],
                     "dossier": live},
            "model_meta": meta,
        })
    rules_ok = sum(1 for c in cases if c["rules"]["verdicts"] == c["expected"])
    live_ok = sum(1 for c in cases if c["live"]["verdicts"] == c["expected"])
    accepted = sum(c["live"]["summary"]["accepted_arguments"] for c in cases)
    struck = sum(c["live"]["summary"]["struck_arguments"] for c in cases)
    payload = {
        "ok": True,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model": llm.active_model(),
        "provider": "cloud" if os.environ.get("LLM_API_KEY") else "local-llama.cpp",
        "mode": "live AI advocates + deterministic judge",
        "cases": cases,
        "summary": {
            "cases": len(cases),
            "rules_accuracy": round(rules_ok / len(cases), 4) if cases else 0,
            "live_accuracy": round(live_ok / len(cases), 4) if cases else 0,
            "accepted_arguments": accepted,
            "struck_arguments": struck,
            "uplift": round((live_ok - rules_ok) / len(cases), 4) if cases else 0,
        },
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    _publish(payload, out_path)
    return payload


def main():
    out = run()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
