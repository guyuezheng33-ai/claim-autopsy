"""Regenerate the submission screenshots from the real page.

Runs the built `web/index.html` in a real browser and captures the same
evidence views the docs reference, so screenshots can never drift from the
data. Uses the locally installed browser via Playwright channels (no download).

Usage: python tools/make_screenshots.py
"""
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "file:///" + os.path.join(ROOT, "web", "index.html").replace("\\", "/")
OUT = os.path.join(ROOT, "evidence", "screenshots")

SHOTS = [
    # (file, 1-based demo index or None for first screen, expand trail, target)
    ("01-ai-contrast.png", None, False, "viewport"),
    ("02-result-demo1.png", 1, False, "#result"),
    ("03-conflict-demo4.png", 4, False, "#result"),
    ("04-refusal-demo3.png", 3, False, "#result"),
    ("05-audit-demo6.png", 6, True, "#result"),
    ("06-coverage-demo7.png", 7, False, "#result"),
    ("07-corpus-browser.png", None, False, "#corpusCard"),
    # A refusal caused by a guard, not by a missing topic: the closest card is
    # named with the reason it was excluded (A25/A28).
    ("08-scope-refusal.png", "Coffee causes cancer in children.", False, "#result"),
    # Two atoms that cannot both be true, labelled instead of averaged (A30).
    ("09-contradictory-atoms.png", "The Earth is round and the Earth is flat.", False, "#result"),
    # A contradiction that only exists after two links: the derived statement is
    # printed with its basis so the inference can be checked (A33).
    ("10-chain-conflict.png", "Coffee causes cancer. Cancer causes death. Coffee prevents death.", False, "#result"),
    # A citation that carries the archived paragraph it was checked against (A34).
    ("11-snapshot-evidence.png", "A common cold can resolve on its own.", False, "#result", True),
    # The corpus browser can be filtered to the cards whose paragraph was archived.
    ("12-archived-corpus.png", None, False, "#corpusCard", False, True),
    # A topic collision that used to become a verdict: the claim shares "flu"
    # with card E001 but not the assertion, so the guard refuses and names it.
    ("13-topic-guard.png", "Mask wearing and social distancing for COVID-19 may be slowing influenza spread", False, "#result"),
    # An endpoint mismatch rather than a missing topic: same nouns as the card,
    # different question (A36).
    ("14-endpoint-guard.png", "the lack of Vitamin D make you more susceptible to the Covid-19 coronavirus", False, "#result"),
    # The list mode: five claims in, one table out (A42, /api/batch).
    ("15-batch-table.png", None, False, "#batchCard", False, False,
     "Getting a flu vaccine gives you the flu.\n"
     "A common cold can resolve on its own.\n"
     "Coffee causes cancer in children.\n"
     "The Earth is round.\n"
     "Vitamin C cures the flu."),
    # A refusal that hands the reader the next step: background source plus
    # three clickable searches (core/plan.py, A42).
    ("16-refusal-plan.png", "Coffee stunts growth in teenagers.", False, "#result", True),
    # Citation mode: the second question. All three outcomes are rendered from
    # the real page (A44, /api/citation), including the non-refusal "not stated".
    ("17-citation-refuted.png", None, False, "#result", False, False, None, 0),
    ("18-citation-supported.png", None, False, "#result", False, False, None, 1),
    ("19-citation-not-in-source.png", None, False, "#result", False, False, None, 2),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1200, "height": 1150}, device_scale_factor=1)
        page.goto(PAGE)
        page.wait_for_timeout(600)

        for shot in SHOTS:
            name, demo, expand, target = shot[:4]
            open_snap = bool(shot[4]) if len(shot) > 4 else False
            arch_filter = bool(shot[5]) if len(shot) > 5 else False
            batch_text = shot[6] if len(shot) > 6 else None
            cit_index = shot[7] if len(shot) > 7 else None
            page.evaluate("document.getElementById('result').style.display='none'")
            if cit_index is not None:
                page.evaluate("document.querySelector('#modeSwitch .mode-btn[data-mode=citation]').click()")
                page.wait_for_timeout(250)
                page.evaluate("i => document.querySelectorAll('#citTags .tag')[i].click()", cit_index)
                page.wait_for_timeout(900)
            if batch_text:
                page.evaluate(
                    "t => { document.getElementById('batchInput').value = t;"
                    " document.getElementById('batchBtn').click(); }", batch_text)
                page.wait_for_timeout(900)
            if demo is not None:
                expr = "i => run(DATA.demos[i-1].text)" if isinstance(demo, int) else "t => run(t)"
                page.evaluate(expr, demo)
                page.wait_for_timeout(900)
                if expand:
                    page.evaluate(
                        "document.querySelectorAll('.trace-btn').forEach(b => {"
                        " if (b.nextElementSibling) b.nextElementSibling.style.display='block'; })")
                    page.wait_for_timeout(400)
                if open_snap:
                    page.evaluate("document.querySelectorAll('details.ev-snap').forEach(d => { d.open = true; })")
                    page.wait_for_timeout(300)
            if arch_filter:
                page.evaluate("document.querySelector('#corpusFilters .chip.arch').click()")
                page.wait_for_timeout(400)
            path = os.path.join(OUT, name)
            if target == "viewport":
                page.screenshot(path=path)
            else:
                el = page.locator(target)
                el.scroll_into_view_if_needed()
                page.wait_for_timeout(250)
                el.screenshot(path=path)
            print("wrote", name)
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
