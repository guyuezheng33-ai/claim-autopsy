"""Write or verify FINAL_MANIFEST.md.

The manifest is a freeze record: a table of path / bytes / SHA256 (first 16) for every
deliverable file. `python tools/check_manifest.py --write` regenerates it after an
intentional change; without --write it only verifies the current table and exits non-zero
on drift, so "has this been edited since the freeze?" is a command, not a memory.
"""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "FINAL_MANIFEST.md"
SKIP_DIRS = {"evidence/history"}
# Runtime logs change whenever the demo starts or stops; they are not deliverables
# and must not make the frozen manifest drift after a successful run.
SKIP_FILES = {
    "evidence/serve_stdout.log",
    "evidence/serve_stderr.log",
    "evidence/llama_stdout.log",
    "evidence/llama_stderr.log",
}


def tracked():
    out = []
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel == "FINAL_MANIFEST.md" or rel in SKIP_FILES:
            continue
        if any(rel.startswith(d + "/") for d in SKIP_DIRS):
            continue
        if rel.startswith("evidence/acceptance_") and rel != "evidence/acceptance_final.json":
            continue
        if rel.startswith(".git/"):
            continue
        out.append(rel)
    return out


def digest(rel):
    data = (ROOT / rel).read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()[:16]


HEAD = """# Final manifest — what "final" means, and how to prove it later

Freeze point: **2026-11-21** (project root `claim-autopsy/`). This file records the exact byte state
that passed the acceptance suite, so a later change is detectable instead of being a matter of memory.

**Gate result at this freeze point** (generated from `evidence/acceptance_final.json`, never typed by
hand, so the summary below cannot drift from the run it describes):

```
{gate}
```

`evidence/acceptance_final.json` is the machine-readable copy of that run.

**How to use this file**: `python tools/check_manifest.py` re-hashes every row and exits non-zero on
drift (no arguments needed), or use `Get-FileHash <path> -Algorithm SHA256` and compare the first 16
hex characters with the column below, one file at a time. If every row still matches, the delivered
state is untouched; if a row differs, that file changed after the freeze — re-run
`python -m core.audit final` before claiming the numbers again.

**Intentionally not final** (these are outputs of the submitter's own actions, not unfinished work):
the public repository URL, the hosted demo URL, the 60-second video, and the Devpost form.
`USER_TODO.md` holds those four steps in order. `LICENSE` carries the placeholder holder
"Claim Autopsy authors" — change it to your legal name before publishing if you prefer.

`evidence/history/` is deliberately excluded from the table below: it holds superseded
run credentials kept for traceability, not part of the deliverable. This manifest is the only
project file not listed in its own table — it cannot hash itself.

"""


def gate_block():
    """Render the acceptance summary from the frozen run, not from prose."""
    p = ROOT / "evidence" / "acceptance_final.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    total, passed = d["total"], d["passed"]
    lines = ['total=%d  passed=%d  all_pass=%s  run_tag=%s  llm_mode=%s'
             % (total, passed, d["all_pass"], d.get("run_tag"),
                '"%s"' % d.get("llm_mode", ""))]
    for key in sorted(d["results"]):
        v = d["results"][key]
        detail = v.get("detail", "")
        if len(detail) > 110:
            detail = detail[:107] + "..."
        lines.append("%-4s %s %s" % (key.split("_")[0], "PASS" if v.get("pass") else "FAIL", detail))
    return "\n".join(lines)


def build():
    rows = ["| File | Bytes | SHA256 (first 16) |"]
    for rel in tracked():
        size, h = digest(rel)
        rows.append(f"| {rel} | {size} | {h} |")
    return HEAD.replace("{gate}", gate_block()) + "\n".join(rows) + "\n", len(rows) - 1


def verify():
    text = MANIFEST.read_text(encoding="utf-8")
    rows = [ln for ln in text.splitlines() if ln.startswith("| ") and "SHA256" not in ln]
    bad = []
    for ln in rows:
        parts = [p.strip() for p in ln.strip("|").split("|")]
        if len(parts) != 3:
            bad.append("malformed:" + ln[:40])
            continue
        rel, size, h = parts
        if not (ROOT / rel).exists():
            bad.append("missing:" + rel)
            continue
        real = digest(rel)
        if str(real[0]) != size or real[1] != h:
            bad.append("drift:" + rel)
    listed = {ln.strip("|").split("|")[0].strip() for ln in rows}
    for rel in tracked():
        if rel not in listed:
            bad.append("unlisted:" + rel)
    return bad


if __name__ == "__main__":
    if "--write" in sys.argv:
        text, n = build()
        MANIFEST.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote FINAL_MANIFEST.md with {n} files")
    else:
        bad = verify()
        for b in bad:
            print("[DRIFT]", b)
        print(f"manifest rows verified, {len(bad)} problems")
        sys.exit(1 if bad else 0)
