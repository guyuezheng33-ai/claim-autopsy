"""Legacy helper: sync claims.json into the embedded DATA block of web/index.html.

Usage: python tools/sync_frontend.py
Superseded by tools/build_frontend.py. Kept only as a historical reference.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "data", "claims.json")
HTML = os.path.join(ROOT, "web", "index.html")


def js(v):
    return json.dumps(v, ensure_ascii=False)


def build(corpus):
    lines = ["const DATA = {", "  cards:["]
    for c in corpus["evidence_cards"]:
        lines.append(
            "    {id:%s,claim:%s,sid:%s,src:%s,url:%s,snip:%s,stance:%s,w:%s,cgroup:%s,exclude:%s,tags:%s}," % (
                js(c["card_id"]), js(c["claim"]), js(c["source_id"]), js(c["source_name"]),
                js(c["url"]), js(c["snippet"]), js(c["stance"]),
                js(c.get("stance_weight", 1.0)), js(c.get("conflict_group", "")),
                js(c.get("exclude_if", [])), js(c.get("tags", [])))
        )
    lines.append("  ],")
    lines.append("  demos:%s," % js(corpus["demo_inputs"]))
    lines.append("  notice:%s" % js(corpus["meta"]["notice"]))
    lines.append("};")
    return "\n".join(lines) + "\n"


def main():
    with open(CORPUS, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    with open(HTML, "r", encoding="utf-8") as f:
        html = f.read()
    new_block = build(corpus)
    html2, n = re.subn(r"const DATA = \{[\s\S]*?\n\};\n", new_block, html, count=1)
    if n != 1:
        raise SystemExit("DATA block not found or ambiguous (n=%d)" % n)
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(html2)
    print("synced %d cards / %d demos into %s" % (
        len(corpus["evidence_cards"]), len(corpus["demo_inputs"]), HTML))


if __name__ == "__main__":
    main()
