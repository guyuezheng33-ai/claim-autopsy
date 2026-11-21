"""Single front-end build entry: claims.json + web/app.js -> <script> in web/index.html.

Usage: python tools/build_frontend.py
Re-run after any data or front-end change. A14 verifies front/back-end verdict parity.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import snapshots  # noqa: E402
CORPUS = os.path.join(ROOT, "data", "claims.json")
REPLAY = os.path.join(ROOT, "data", "ai_recall_replay.json")
GOLDEN = os.path.join(ROOT, "data", "golden_set.json")
LIFT = os.path.join(ROOT, "evidence", "ai_lift.json")
COVERAGE = os.path.join(ROOT, "evidence", "coverage_headroom.json")
APP = os.path.join(ROOT, "web", "app.js")
HTML = os.path.join(ROOT, "web", "index.html")
PLACEHOLDER = "/* __DATA_PLACEHOLDER__ */"


def js(v):
    return json.dumps(v, ensure_ascii=False)


def snap_block():
    """Compact snapshot map for the page: status, date, paragraph, hash prefix, note."""
    snaps = snapshots.load()
    out = {}
    for card_id, rec in snaps.items():
        note = rec.get("note", "")
        if len(note) > 160:
            note = note[:157].rstrip() + "..."
        out[card_id] = {
            "st": rec["status"],
            "d": (rec.get("fetched_at") or "")[:10],
            "p": rec.get("paragraph_index"),
            "h": (rec.get("sha256") or "")[:12],
            "ph": (rec.get("page_sha256") or "")[:12],
            "x": rec.get("excerpt", ""),
            "o": rec.get("char_offset") or [],
            "note": note,
        }
    return out


def data_block(corpus, replay, stats):
    lines = ["const DATA = {", "  cards:["]
    for c in corpus["evidence_cards"]:
        lines.append(
            "    {id:%s,claim:%s,sid:%s,src:%s,url:%s,snip:%s,stance:%s,w:%s,cgroup:%s,exclude:%s,requires:%s,tags:%s}," % (
                js(c["card_id"]), js(c["claim"]), js(c["source_id"]), js(c["source_name"]),
                js(c["url"]), js(c["snippet"]), js(c["stance"]),
                js(c.get("stance_weight", 1.0)), js(c.get("conflict_group", "")),
                js(c.get("exclude_if", [])), js(c.get("requires_all", [])),
                js(c.get("tags", [])))
        )
    lines += ["  ],", "  demos:%s," % js(corpus["demo_inputs"]),
              "  notice:%s," % js(corpus["meta"]["notice"]),
              "  replay:%s," % js(replay),
              "  snaps:%s," % js(snap_block()),
              "  stats:%s" % js(stats), "};"]
    return "\n".join(lines) + "\n"


def main():
    with open(CORPUS, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    with open(REPLAY, "r", encoding="utf-8") as f:
        replay = json.load(f)
    with open(GOLDEN, "r", encoding="utf-8") as f:
        golden = json.load(f)
    with open(LIFT, "r", encoding="utf-8") as f:
        lift = json.load(f)
    snap_sum = snapshots.summary()
    coverage = {}
    if os.path.exists(COVERAGE):
        with open(COVERAGE, "r", encoding="utf-8") as f:
            coverage = json.load(f)
    stats = {
        "cards": len(corpus["evidence_cards"]),
        "sources": len(corpus["sources"]),
        "cases": len(golden["cases"]),
        "delta": lift["delta"]["deep_recall"],
        "verified": snap_sum["verified"],
        # The coverage card is built from the measured file, not typed by hand.
        "ext_claims": coverage.get("claims"),
        "answered": coverage.get("answered"),
        "refused": coverage.get("refused"),
        "in_domain": coverage.get("coverage_in_domain"),
        "with_contact": coverage.get("refusals_with_contact"),
    }
    with open(APP, "r", encoding="utf-8") as f:
        app = f.read()
    if PLACEHOLDER not in app:
        raise SystemExit("app.js placeholder missing")
    script = app.replace(PLACEHOLDER, data_block(corpus, replay, stats), 1)

    with open(HTML, "r", encoding="utf-8") as f:
        html = f.read()
    html2, n = re.subn(r"<script>[\s\S]*?</script>",
                       lambda m: "<script>\n" + script + "\n</script>", html, count=1)
    if n != 1:
        raise SystemExit("script block not found or ambiguous (n=%d)" % n)
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(html2)
    print("built %s | cards=%d demos=%d" % (
        HTML, len(corpus["evidence_cards"]), len(corpus["demo_inputs"])))


if __name__ == "__main__":
    main()
