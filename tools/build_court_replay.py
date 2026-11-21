"""Merge the recorded rules-only dossiers with real recorded local-AI runs.

The static page is allowed to replay a real model run, but every such dossier
stays labelled as a recording. Only `serve.py` can produce a live badge.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "data", "court_replay.json")
LIVE = os.path.join(ROOT, "evidence", "court_live.json")
OUT_JSON = os.path.join(ROOT, "data", "court_replay.json")
OUT_JS = os.path.join(ROOT, "web", "court_replay.js")

KEY_MAP = {
    "refuted_flu": "flu",
    "supported_eiffel": "eiffel",
    "not_in_source_coffee": "coffee",
    "quantity_mismatch": "quantity",
    "population_mismatch": "population",
    "relation_mismatch": "relation",
}


def main():
    with open(BASE, "r", encoding="utf-8") as fh:
        base = json.load(fh)
    with open(LIVE, "r", encoding="utf-8") as fh:
        live = json.load(fh)
    if not live.get("ok"):
        raise SystemExit("court_live.json is not a successful run; refusing to build a replay")
    cases = base.setdefault("cases", {})
    used = []
    for case in live.get("cases", []):
        key = KEY_MAP.get(case.get("replay_key"))
        if not key:
            continue
        dossier = case["live"].get("dossier")
        if not dossier:
            continue
        dossier["__source"] = case["source"]
        dossier["replay_mode"] = "live-run-recording"
        dossier["demo_label"] = "RECORDED LIVE AI RUN · %s" % live.get("model", "model")
        cases[key] = dossier
        used.append(key)
    base["meta"] = {
        "label": "recorded dossiers: real local-AI runs, rules-only controls, and one adversarial fixture",
        "note": ("Every AI dossier here is a recording of an actual local Qwen run; the page says so. "
                 "Only `python serve.py` calls the model live. The adversarial fixture is labelled and is not a model run."),
        "live_run": {
            "model": live.get("model"),
            "provider": live.get("provider"),
            "generated_at": live.get("generated_at"),
            "cases": used,
        },
    }
    text = json.dumps(base, ensure_ascii=False, indent=2)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    with open(OUT_JS, "w", encoding="utf-8") as fh:
        fh.write("window.COURT_REPLAY = " + text + ";\n")
    print("merged %d recorded AI case(s): %s" % (len(used), ", ".join(used)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
