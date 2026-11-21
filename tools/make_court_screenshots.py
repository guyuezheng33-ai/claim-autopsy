"""Capture the current court screens for the submission.

Static shots must show the recorded-AI label. The HTTP shot must wait for the
live badge; if the live run fails, the script fails instead of saving a
misleading image.
"""
import json
import os
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = "file:///" + os.path.join(ROOT, "web", "index.html").replace("\\", "/")
LIVE = "http://127.0.0.1:8765/"
OUT = os.path.join(ROOT, "evidence", "screenshots")


def read_court(page):
    return page.evaluate("""() => ({
      badge: (document.getElementById('courtModeBadge') || {}).textContent || '',
      strip: (document.querySelector('#courtResult .ai-strip') || {}).textContent || '',
      status: (document.getElementById('courtStatus') || {}).textContent || '',
      accepted: document.querySelectorAll('#courtResult .court-arg.accepted').length,
      struck: document.querySelectorAll('#courtResult .court-arg.struck').length
    })""")


def main():
    os.makedirs(OUT, exist_ok=True)
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1200, "height": 1100}, device_scale_factor=1)
        page.goto(STATIC)
        page.wait_for_timeout(800)
        static = read_court(page)
        if "RECORDED LIVE AI RUN" not in static["badge"]:
            raise SystemExit("static page did not show a recorded live-AI run: %s" % static)
        page.screenshot(path=os.path.join(OUT, "23-court-static-ai.png"), full_page=True)
        report["static"] = static

        page.evaluate("document.querySelectorAll('.court-chip')[4].click()")
        page.wait_for_timeout(400)
        struck = read_court(page)
        if "ADVERSARIAL FIXTURE" not in struck["badge"] or struck["struck"] < 1:
            raise SystemExit("static struck fixture did not render: %s" % struck)
        page.screenshot(path=os.path.join(OUT, "24-court-struck.png"), full_page=True)
        report["struck"] = struck

        page.evaluate("document.getElementById('courtBatchExample').click()")
        page.wait_for_timeout(400)
        batch = page.evaluate("""() => ({
          badge: (document.getElementById('courtModeBadge') || {}).textContent || '',
          rows: document.querySelectorAll('#courtResult .court-batch-row').length,
          conflicts: document.querySelectorAll('#courtResult .court-conflict').length,
          summary: (document.querySelector('#courtResult .court-batch-summary') || {}).textContent || ''
        })""")
        if not batch["badge"].startswith("MULTI-SOURCE") or batch["rows"] != 4:
            raise SystemExit("static batch did not render: %s" % batch)
        page.screenshot(path=os.path.join(OUT, "26-court-batch.png"), full_page=True)
        report["batch"] = batch

        page.goto(LIVE)
        deadline = time.time() + 180
        live = read_court(page)
        while time.time() < deadline and not live["badge"].startswith("LIVE AI"):
            page.wait_for_timeout(500)
            live = read_court(page)
        if not live["badge"].startswith("LIVE AI") or live["accepted"] < 1:
            page.wait_for_timeout(300)
            live = read_court(page)
        page.wait_for_timeout(300)
        progress = page.evaluate("""() => ({
          visible: !!(document.getElementById('courtProgress') || {}).offsetParent,
          running: (document.getElementById('courtProgress') || {}).getAttribute('data-running'),
          phase: (document.getElementById('courtProgress') || {}).getAttribute('data-phase'),
          elapsed: (document.getElementById('cpElapsed') || {}).textContent || '',
          done_steps: document.querySelectorAll('#courtProgress .cp-step.done').length,
          title: (document.getElementById('cpTitle') || {}).textContent || ''
        })""")
        if not live["badge"].startswith("LIVE AI") or live["accepted"] < 1:
            raise SystemExit("HTTP page did not reach a verified live docket: %s" % live)
        if not progress["visible"] or progress["running"] != "0" or progress["done_steps"] != 4:
            raise SystemExit("HTTP live run did not finish the visible progress panel: %s" % progress)
        page.screenshot(path=os.path.join(OUT, "25-court-live.png"), full_page=True)
        report["live"] = live
        report["progress"] = progress
        browser.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
