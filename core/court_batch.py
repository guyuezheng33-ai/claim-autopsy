"""Multi-source citation court.

One claim, many candidate sources. The rules docket triages every source first;
AI advocates are spent only on the sources the rules cannot settle. The judge
still owns every finding. A cross-source conflict is surfaced, never adjudicated
as truth.
"""
import datetime
import hashlib
import json
import os

from . import court, llm

MAX_SOURCES = 8
MAX_TOTAL_CHARS = 80000
MAX_AI_SOURCES = 3
FIXTURES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "court_batch_cases.json")


def _hash(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def _source_verdict(dossier):
    verdicts = [a["verdict"] for a in dossier.get("atoms", [])]
    if not verdicts:
        return "not_in_source"
    if "conflict" in verdicts or ("supported" in verdicts and "refuted" in verdicts):
        return "conflict"
    if "refuted" in verdicts:
        return "refuted"
    if "supported" in verdicts:
        return "supported"
    return "not_in_source"


def _quote_for(dossier):
    for atom in dossier.get("atoms", []):
        ids = atom.get("accepted_argument_ids") or []
        for arg in dossier.get("arguments", []):
            if arg.get("argument_id") in ids and arg.get("status") == "accepted":
                return {
                    "quote": arg["quote"],
                    "evidence_id": arg["evidence_id"],
                    "char_start": arg["char_start"],
                    "char_end": arg["char_end"],
                    "origin": arg.get("origin", "rule"),
                    "bridge": arg.get("bridge"),
                }
    return None


def run_batch(claim, sources, live=False, ai_limit=MAX_AI_SOURCES, model=None):
    """Audit one claim against up to eight candidate sources.

    Rules-only is always computed. Live AI is used only for sources whose rules
    docket returns `not_in_source`, capped so a long batch cannot become an
    unbounded model call.
    """
    claim = (claim or "").strip()
    if not claim:
        return {"error": "empty_claim"}
    if len(claim) > court.MAX_CLAIM_CHARS:
        return {"error": "claim_too_long", "limit": court.MAX_CLAIM_CHARS}
    if not isinstance(sources, list) or not sources:
        return {"error": "empty_sources"}
    if len(sources) > MAX_SOURCES:
        return {"error": "too_many_sources", "limit": MAX_SOURCES}

    clean = []
    seen = {}
    duplicates = []
    for item in sources:
        if isinstance(item, str):
            name, text = "source", item
        elif isinstance(item, dict):
            name = str(item.get("name") or "source").strip() or "source"
            text = str(item.get("text") or "").strip()
        else:
            return {"error": "bad_source"}
        if not text:
            continue
        if len(text) > court.MAX_SOURCE_CHARS:
            return {"error": "source_too_long", "source": name,
                    "limit": court.MAX_SOURCE_CHARS}
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if sha in seen:
            duplicates.append({"name": name, "duplicate_of": seen[sha]})
            continue
        seen[sha] = name
        clean.append({"name": name, "text": text, "sha256": sha})
    if not clean:
        return {"error": "empty_sources"}
    if sum(len(s["text"]) for s in clean) > MAX_TOTAL_CHARS:
        return {"error": "batch_too_long", "limit": MAX_TOTAL_CHARS}

    try:
        ai_limit = max(0, min(int(ai_limit), MAX_AI_SOURCES))
    except (TypeError, ValueError):
        ai_limit = 0

    atoms = court.rule_split(claim)[:court.MAX_ATOMS] or [claim]
    rows = []
    ai_used = 0
    ai_skipped = 0
    total_ai_ms = 0
    for i, src in enumerate(clean, 1):
        sid = "B%d" % i
        rules = court.make_dossier(claim, src["text"], src["name"])
        if rules.get("error"):
            return rules
        mode = "rules"
        dossier = rules
        ai_meta = None
        if live and ai_used < ai_limit and _source_verdict(rules) == "not_in_source":
            packet = court.build_evidence(src["text"], src["name"])
            ai_args, meta = llm.collect_ai_arguments(atoms, packet)
            dossier = court.make_dossier(
                claim, src["text"], src["name"], ai_arguments=ai_args,
                mode="ai", model=model or llm.active_model(),
                trace=[{"step": "advocates", "meta": meta}],
            )
            mode = "ai"
            ai_used += 1
            total_ai_ms += (meta.get("prosecution", {}).get("latency_ms", 0)
                            + meta.get("defense", {}).get("latency_ms", 0))
            ai_meta = {"prosecution": meta.get("prosecution", {}),
                       "defense": meta.get("defense", {})}
        elif live and _source_verdict(rules) == "not_in_source":
            ai_skipped += 1
        rows.append({
            "source_id": sid,
            "name": src["name"],
            "sha256": src["sha256"],
            "chars": len(src["text"]),
            "mode": mode,
            "verdict": _source_verdict(dossier),
            "quote": _quote_for(dossier),
            "summary": dossier.get("summary", {}),
            "dossier": dossier,
            "ai_meta": ai_meta,
        })

    counts = {"supported": 0, "refuted": 0, "not_in_source": 0, "conflict": 0}
    for row in rows:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    cross = counts["supported"] > 0 and counts["refuted"] > 0
    generated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    payload = {
        "mode": "multi-source court",
        "input": {"claim": claim},
        "sources": [{k: r[k] for k in ("source_id", "name", "sha256", "chars", "mode")} for r in rows],
        "rows": rows,
        "duplicates": duplicates,
        "summary": {
            "sources": len(rows),
            "supported": counts["supported"],
            "refuted": counts["refuted"],
            "not_in_source": counts["not_in_source"],
            "conflict": counts["conflict"],
            "cross_source_conflict": cross,
            "ai_used": ai_used,
            "ai_skipped": ai_skipped,
            "total_ai_ms": total_ai_ms,
        },
        "receipt": {
            "run_id": _hash({
                "claim": claim,
                "sources": [r["sha256"] for r in rows],
                "verdicts": [r["verdict"] for r in rows],
                "arguments": [[a.get("argument_id") for a in r["dossier"].get("arguments", [])]
                              for r in rows],
                "mode": "multi",
            })[:16],
            "generated_at": generated_at,
            "model": model or (llm.active_model() if live else None),
            "engine": "deterministic judge + rules triage" if not live else
                      "deterministic judge + rules triage + targeted AI",
        },
        "disclaimer": (
            "Each source is judged on its own. A cross-source conflict means the "
            "supplied sources disagree; the court does not decide which source is "
            "right, and it is not an authoritative fact-check."
        ),
    }
    return payload


def run_fixtures(path=None):
    """Run the batch fixtures offline. Every case is a behavioural assertion."""
    with open(path or FIXTURES, "r", encoding="utf-8") as f:
        cases = json.load(f).get("cases", [])
    out = []
    for case in cases:
        res = run_batch(case.get("claim", ""), case.get("sources", []), live=False)
        want = case.get("expected") or {}
        bad = []
        if case.get("expected_error"):
            if res.get("error") != case["expected_error"]:
                bad.append("error:%s" % res.get("error"))
        else:
            if res.get("error"):
                bad.append("unexpected_error:%s" % res.get("error"))
            else:
                got = [r["verdict"] for r in res.get("rows", [])]
                if got != want.get("verdicts"):
                    bad.append("verdicts:%s" % got)
                if res["summary"]["sources"] != want.get("sources"):
                    bad.append("source_count:%s" % res["summary"]["sources"])
                if len(res.get("duplicates") or []) != want.get("duplicates"):
                    bad.append("duplicates:%s" % len(res.get("duplicates") or []))
                if res["summary"]["cross_source_conflict"] != want.get("cross_source_conflict"):
                    bad.append("cross_source_conflict")
        out.append({"id": case["id"], "pass": not bad, "bad": bad})
    passed = sum(1 for c in out if c["pass"])
    return {"passed": passed, "total": len(out), "all_pass": passed == len(out), "cases": out}


def receipt_markdown(payload):
    lines = ["# Claim Autopsy — multi-source receipt", ""]
    lines.append("- Claim: " + payload.get("input", {}).get("claim", ""))
    lines.append("- Run: `" + payload.get("receipt", {}).get("run_id", "") + "`")
    lines.append("- Sources: %d" % payload.get("summary", {}).get("sources", 0))
    lines.append("- Model: " + str(payload.get("receipt", {}).get("model") or "none"))
    lines.append("")
    for row in payload.get("rows", []):
        lines.append("## %s — %s" % (row["name"], row["verdict"].upper()))
        lines.append("- Source id: `%s` · SHA-256 `%s`" % (row["source_id"], row["sha256"]))
        q = row.get("quote")
        if q:
            lines.append("- Accepted quote: `%s` · chars %s–%s · %s" % (
                q["quote"], q["char_start"], q["char_end"], q["origin"].upper()))
            if q.get("bridge"):
                pairs = ", ".join("%s → %s" % (a, b) for a, b in q["bridge"]["anchors"])
                lines.append("- AI bridge: " + pairs)
        else:
            lines.append("- No accepted quotation.")
        lines.append("")
    if payload.get("summary", {}).get("cross_source_conflict"):
        lines.append("**Cross-source conflict:** at least one source supports and one refutes the claim. "
                     "This receipt does not pick a winner.")
        lines.append("")
    lines.append("---")
    lines.append(payload.get("disclaimer", ""))
    return "\n".join(lines)
