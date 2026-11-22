"""Open the built page in a real browser and check what a judge would click.

The Node harness (`tools/js_ui_verify.js`) executes the front-end *functions* against a DOM
stub. That proves kernel parity; it does not prove that clicking a demo on a rendered page
produces the same claim list, the same verdict badges and the same cited cards, that the page
raises no exceptions, or that it asks the network for nothing. This script does that with a
real browser and prints one JSON object on stdout; gate A38 consumes it.

Usage: python tools/browser_check.py
Exit code 0 when the page behaved (or when no browser is available, reported as `skipped`).
"""
import json
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "file:///" + os.path.join(ROOT, "web", "index.html").replace("\\", "/")

READ = """() => {
  const heads = [...document.querySelectorAll('#result .claim-head')];
  const srcs = [...document.querySelectorAll('#result .ev-src')];
  return {
    claims: heads.map(h => ({
      badge: (h.querySelector('.badge') || {}).className || '',
      text: (h.querySelector('.claim-txt') || {}).textContent || ''
    })),
    ev_count: document.querySelectorAll('#result .ev').length,
    ev_text: srcs.map(e => e.textContent).join(' | '),
    corpus: document.querySelectorAll('#corpusList .corpus-item').length
  };
}"""

ENGINE = """(t) => {
  const r = analyze(t);
  return {verdicts: r.verdicts.map(v => ({claim: v.claim, verdict: v.verdict,
           sids: (v.citations || []).map(c => c.sid)})), summary: r.summary};
}"""

READ_CIT = """() => {
  const heads = [...document.querySelectorAll('#result .claim-head')];
  return {
    claims: heads.map(h => ({
      badge: (h.querySelector('.badge') || {}).className || '',
      text: (h.querySelector('.claim-txt') || {}).textContent || ''
    })),
    quotes: document.querySelectorAll('#result .cit-quote').length,
    meta: (document.getElementById('runmeta') || {}).textContent || ''
  };
}"""

READ_COURT = """() => {
  const badge = document.getElementById('courtModeBadge');
  const strip = document.querySelector('#courtResult .ai-strip');
  const status = document.getElementById('courtStatus');
  return {
    badge: badge ? badge.textContent : '',
    strip: strip ? strip.textContent : '',
    status: status ? status.textContent : '',
    trap: (document.getElementById('courtProofVerdict') || {}).textContent || '',
    accepted: document.querySelectorAll('#courtResult .court-arg.accepted').length,
    struck: document.querySelectorAll('#courtResult .court-arg.struck').length,
    atoms: document.querySelectorAll('#courtResult .court-atom').length,
    visible: !!(document.getElementById('courtResult') || {}).offsetParent
  };
}"""

ENGINE_CIT = """(i) => {
  const d = CIT_DEMOS[i];
  const r = citationAudit(d.claim, d.source);
  return {verdicts: r.verdicts.map(v => ({claim: v.claim, verdict: v.verdict,
           quote: !!v.source_sentence})), summary: r.summary};
}"""


def main():
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print(json.dumps({"skipped": "playwright_not_installed"}))
        return 0

    errors, requests = [], []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="msedge")
            named = "edge"
        except Exception:
            browser = p.chromium.launch()
            named = "chromium"
        page = browser.new_page(viewport={"width": 1200, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("request", lambda r: requests.append(r.url)
                if r.url.startswith(("http://", "https://")) else None)
        page.goto(PAGE)
        page.wait_for_timeout(700)

        demos = page.evaluate("DATA.demos.map(d => d.text)")
        cases = []
        for i, text in enumerate(demos):
            page.evaluate("i => document.querySelectorAll('.tag')[i].click()", i)
            page.wait_for_timeout(1100)
            got = page.evaluate(READ)
            want = page.evaluate(ENGINE, text)
            claims_match = len(got["claims"]) == len(want["verdicts"])
            badges, texts = True, True
            if claims_match:
                for g, w in zip(got["claims"], want["verdicts"]):
                    cls = g["badge"].split()
                    badges = badges and "badge" in cls and w["verdict"] in cls
                    texts = texts and g["text"].strip() == w["claim"].strip()
            want_sids = [c for v in want["verdicts"] for c in v["sids"] if c]
            # the page prints the source, not the card id, so the check is that every
            # source the engine cited is named in a citation block, and that no block
            # was rendered that the engine did not produce
            sids_ok = all(s in got["ev_text"] for s in want_sids) \
                and got["ev_count"] == len(want_sids)
            cases.append({
                "demo": i + 1,
                "claims_rendered": len(got["claims"]),
                "claims_expected": len(want["verdicts"]),
                "claims_match": claims_match,
                "badges_match": badges,
                "texts_match": texts,
                "citations_match": sids_ok,
                "citations_rendered": got["ev_count"],
                "citations_expected": len(want_sids),
                "summary": want["summary"],
            })
        corpus = page.evaluate("document.querySelectorAll('#corpusList .corpus-item').length")

        # Court mode: a judge opens the static page and must see a real recorded
        # model run, not a rules-only placeholder and not a fake "live" badge.
        court_default = page.evaluate(READ_COURT)
        court_receipt = page.evaluate("() => window.COURT_RECEIPT ? window.COURT_RECEIPT() : ''")
        page.click("#courtProofRun")
        page.wait_for_timeout(300)
        proof_fake = page.evaluate(READ_COURT)
        page.click("#courtProofReal")
        page.wait_for_timeout(300)
        proof_real = page.evaluate(READ_COURT)
        proof_ok = (
            "ADVERSARIAL FIXTURE" in proof_fake["badge"]
            and proof_fake["struck"] >= 1
            and "quote_not_found" in proof_fake["trap"]
            and "The flu vaccine contains live virus" in proof_fake["trap"]
            and "REFUTED" in proof_fake["trap"].upper()
            and "RECORDED LIVE AI RUN" in proof_real["badge"]
            and proof_real["struck"] >= 1
            and "side_mismatch" in proof_real["trap"]
        )
        court_cases = []
        upload_text = "The Eiffel Tower is located in Paris, France. It opened in 1889."
        upload_path = os.path.join(tempfile.gettempdir(), "claim-autopsy-upload.txt")
        with open(upload_path, "w", encoding="utf-8") as f:
            f.write(upload_text)
        page.set_input_files("#courtSourceFile", upload_path)
        page.wait_for_timeout(250)
        court_upload = page.evaluate("""() => ({
            value: document.getElementById('courtSource').value,
            note: document.getElementById('courtFileName').textContent,
            length: document.getElementById('courtSource').value.length
        })""")
        upload_ok = (court_upload["value"] == upload_text
                     and str(len(upload_text)) in court_upload["note"]
                     and "claim-autopsy-upload.txt" in court_upload["note"])
        for i in range(5):
            page.evaluate("i => document.querySelectorAll('.court-chip')[i].click()", i)
            page.wait_for_timeout(250)
            court_cases.append(page.evaluate(READ_COURT))
        court_ok = (
            "RECORDED LIVE AI RUN" in court_default["badge"]
            and "qwen2.5-" in court_default["strip"].lower()
            and court_default["atoms"] >= 1
            and court_default["accepted"] >= 1
            and any("ADVERSARIAL FIXTURE" in c["badge"] for c in court_cases)
            and any(c["struck"] >= 1 for c in court_cases)
            and not court_default["badge"].startswith("LIVE AI")
            and "# Claim Autopsy — citation receipt" in court_receipt
            and "chars 0–45" in court_receipt
            and upload_ok
        )

        # Batch mode: load the frozen four-source docket and confirm the page
        # renders every source, one cross-source conflict, and a multi receipt.
        page.evaluate("document.getElementById('courtBatchExample').click()")
        page.wait_for_timeout(300)
        batch = page.evaluate("""() => ({
            badge: (document.getElementById('courtModeBadge') || {}).textContent || '',
            rows: document.querySelectorAll('#courtResult .court-batch-row').length,
            conflicts: document.querySelectorAll('#courtResult .court-conflict').length,
            quotes: document.querySelectorAll('#courtResult .court-batch-quote').length,
            status: (document.getElementById('courtStatus') || {}).textContent || ''
        })""")
        batch_receipt = page.evaluate("() => window.COURT_RECEIPT ? window.COURT_RECEIPT() : ''")
        batch_ok = (batch["badge"].startswith("MULTI-SOURCE")
                    and batch["rows"] == 4 and batch["conflicts"] == 1
                    and batch["quotes"] >= 3
                    and "# Claim Autopsy — multi-source receipt" in batch_receipt
                    and "Cross-source conflict" in batch_receipt)

        # Citation mode: the second product. Click the mode switch, then each of
        # the three citation demos, and compare the rendered finding, badge and
        # quoted sentence against the page's own citation kernel.
        page.evaluate("document.querySelector('#modeSwitch .mode-btn[data-mode=citation]').click()")
        page.wait_for_timeout(200)
        cit_cases = []
        for i in range(3):
            page.evaluate("i => document.querySelectorAll('#citTags .tag')[i].click()", i)
            page.wait_for_timeout(700)
            got = page.evaluate(READ_CIT)
            want = page.evaluate(ENGINE_CIT, i)
            claims_match = len(got["claims"]) == len(want["verdicts"])
            badges = True
            if claims_match:
                for g, w in zip(got["claims"], want["verdicts"]):
                    cls = g["badge"].split()
                    badges = badges and "badge" in cls and w["verdict"] in cls
            quotes_ok = got["quotes"] == sum(1 for v in want["verdicts"] if v["quote"])
            cit_cases.append({
                "demo": i + 1,
                "claims_rendered": len(got["claims"]),
                "claims_expected": len(want["verdicts"]),
                "claims_match": claims_match,
                "badges_match": badges,
                "quotes_rendered": got["quotes"],
                "quotes_expected": sum(1 for v in want["verdicts"] if v["quote"]),
                "quotes_match": quotes_ok,
                "total_100": "(100%)" in got["meta"],
            })

        # Judge mode: a fresh page with ?judge=1 must hide the form, start on
        # step 1, and let one Next click reach the recorded 1.5B mistake.
        judge_page = browser.new_page(viewport={"width": 1200, "height": 900})
        judge_page.on("pageerror", lambda e: errors.append(str(e)))
        judge_page.on("request", lambda r: requests.append(r.url)
                      if r.url.startswith(("http://", "https://")) else None)
        judge_page.goto(PAGE + "?judge=1")
        judge_page.wait_for_timeout(700)
        judge_initial = judge_page.evaluate("""() => ({
            mode: document.body.className,
            cardHidden: getComputedStyle(document.querySelector('.court-card')).display === 'none',
            active: (document.querySelector('[data-judge-step].active') || {}).textContent || '',
            trap: (document.getElementById('courtProofVerdict') || {}).textContent || '',
            exitLink: (() => {
                const a = document.getElementById('courtJudgeExit');
                return !!a && a.getAttribute('href') === 'index.html';
            })()
        })""")
        judge_page.click("#courtJudgeNext")
        judge_page.wait_for_timeout(350)
        judge_second = judge_page.evaluate("""() => ({
            active: (document.querySelector('[data-judge-step].active') || {}).textContent || '',
            code: (document.querySelector('#courtProofVerdict .pv-code') || {}).textContent || ''
        })""")
        judge_page.click("[data-judge-step='3']")
        judge_page.wait_for_timeout(400)
        judge_conflict = judge_page.evaluate("""() => ({
            active: (document.querySelector('[data-judge-step].active') || {}).textContent || '',
            rows: document.querySelectorAll('#courtResult .court-batch-row').length,
            conflicts: document.querySelectorAll('#courtResult .court-conflict').length
        })""")
        judge_page.click("[data-judge-step='4']")
        judge_page.wait_for_timeout(400)
        judge_receipt = judge_page.evaluate("""() => ({
            active: (document.querySelector('[data-judge-step].active') || {}).textContent || '',
            actions: !!document.querySelector('#courtResult .court-actions'),
            pulse: !!document.querySelector('#courtResult .court-actions.receipt-pulse'),
            trap: document.getElementById('courtProofVerdict') ? document.getElementById('courtProofVerdict').textContent : ''
        })""")
        judge_page.set_viewport_size({"width": 390, "height": 844})
        judge_page.reload()
        judge_page.wait_for_timeout(700)
        judge_mobile = judge_page.evaluate("""() => ({
            active: (document.querySelector('[data-judge-step].active') || {}).textContent || '',
            railVisible: (() => {
                const r = document.getElementById('courtJudgeRail');
                return !!r && r.getBoundingClientRect().height > 0;
            })(),
            overflow: document.documentElement.scrollWidth - window.innerWidth
        })""")
        judge_page.close()
        judge_path_ok = (
            "court-judge-mode" in judge_initial["mode"]
            and judge_initial["cardHidden"]
            and judge_initial["active"].startswith("1")
            and "quote_not_found" in judge_initial["trap"]
            and judge_initial["exitLink"]
            and judge_second["active"].startswith("2")
            and judge_second["code"] == "side_mismatch"
            and judge_conflict["active"].startswith("4")
            and judge_conflict["rows"] == 4 and judge_conflict["conflicts"] == 1
            and judge_receipt["active"].startswith("5")
            and judge_receipt["actions"] and judge_receipt["pulse"]
            and "quote_not_found" in judge_receipt["trap"]
            and judge_mobile["active"].startswith("1")
            and judge_mobile["railVisible"] and judge_mobile["overflow"] <= 1
        )
        browser.close()

    bad = [c for c in cases if not (c["claims_match"] and c["badges_match"]
                                    and c["texts_match"] and c["citations_match"])]
    cit_bad = [c for c in cit_cases if not (c["claims_match"] and c["badges_match"]
                                          and c["quotes_match"] and c["total_100"])]
    payload = {
        "browser": named,
        "demos": len(cases),
        "cases": cases,
        "citation_demos": len(cit_cases),
        "citation_cases": cit_cases,
        "citation_mismatch": [c["demo"] for c in cases if not c["citations_match"]],
        "render_mismatch": [c["demo"] for c in bad],
        "citation_render_mismatch": [c["demo"] for c in cit_bad],
        "corpus_items": corpus,
        "court_default": court_default,
        "court_cases": court_cases,
        "proof_fake": proof_fake,
        "proof_real": proof_real,
        "proof_ok": proof_ok,
        "court_receipt_chars": len(court_receipt),
        "court_upload": court_upload,
        "court_ok": court_ok,
        "batch": batch,
        "batch_receipt_chars": len(batch_receipt),
        "batch_ok": batch_ok,
        "judge_path_initial": judge_initial,
        "judge_path_second": judge_second,
        "judge_path_conflict": judge_conflict,
        "judge_path_receipt": judge_receipt,
        "judge_path_mobile": judge_mobile,
        "judge_path_ok": judge_path_ok,
        "page_errors": errors,
        "external_requests": requests,
        "ok": not bad and not cit_bad and court_ok and proof_ok and batch_ok and judge_path_ok and not errors and not requests and corpus == 112,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
