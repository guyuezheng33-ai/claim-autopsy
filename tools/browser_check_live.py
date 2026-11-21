"""Open the live court page in a real browser and watch the streamed progress panel.

`browser_check.py` covers the static `file://` page. This script covers the one thing the
static page cannot: a real HTTP run against `/api/trial_stream`, where the page must render
ordered phase progress, heartbeat elapsed time, and a completed four-step panel instead of a
blank spinner. The server and its local model are started by `python serve.py`.

Usage: python tools/browser_check_live.py [--url http://127.0.0.1:8765/]
Exit code 0 when the panel behaved and the page raised no exceptions.
"""
import argparse
import json
import sys
import time


READ = """() => {
  const panel = document.getElementById('courtProgress');
  const steps = [...document.querySelectorAll('#courtProgress .cp-step')];
  return {
    visible: !!(panel && panel.offsetParent),
    running: panel ? panel.getAttribute('data-running') : null,
    phase: panel ? panel.getAttribute('data-phase') : null,
    elapsed: (document.getElementById('cpElapsed') || {}).textContent || '',
    title: (document.getElementById('cpTitle') || {}).textContent || '',
    note: (document.getElementById('cpNote') || {}).textContent || '',
    done_steps: steps.filter(s => s.classList.contains('done')).length,
    active_steps: steps.filter(s => s.classList.contains('active')).length,
    steps: steps.map(s => s.className),
    badge: (document.getElementById('courtModeBadge') || {}).textContent || '',
    status: (document.getElementById('courtStatus') || {}).textContent || '',
    accepted: document.querySelectorAll('#courtResult .court-arg.accepted').length,
    struck: document.querySelectorAll('#courtResult .court-arg.struck').length,
    strip: (document.querySelector('#courtResult .ai-strip') || {}).textContent || ''
  };
}"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8765/")
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print(json.dumps({"skipped": "playwright_not_installed"}))
        return 0

    errors = []
    phases = set()
    start = time.time()
    with sync_playwright() as p:
        browser = None
        for channel in ("msedge", "chrome", None):
            try:
                browser = (p.chromium.launch(channel=channel) if channel
                           else p.chromium.launch())
                break
            except Exception:
                continue
        if browser is None:
            print(json.dumps({"skipped": "no_browser"}))
            return 0
        page = browser.new_page(viewport={"width": 1200, "height": 1200})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(args.url, wait_until="domcontentloaded")
        page.wait_for_selector("#courtProgress", state="visible", timeout=15000)
        final = None
        while time.time() - start < args.timeout:
            state = page.evaluate(READ)
            if state["phase"]:
                phases.add(state["phase"])
            final = state
            if state["running"] == "0":
                break
            page.wait_for_timeout(500)
        page.wait_for_timeout(300)
        final = page.evaluate(READ)
        browser.close()

    ok = bool(final and final["visible"] and final["running"] == "0"
              and final["done_steps"] == 4 and final["title"] == "Judge verified"
              and final["phase"] == "judge" and final["accepted"] >= 1
              and final["struck"] >= 1 and not errors
              and ("ai" in phases or "judge" in phases))
    print(json.dumps({
        "url": args.url,
        "phases_observed": sorted(phases),
        "seconds": round(time.time() - start, 1),
        "final": final,
        "page_errors": errors,
        "ok": ok
    }, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
