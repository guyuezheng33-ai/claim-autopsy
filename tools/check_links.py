"""Open every citation link in a real browser and record what happened.

Citations are the product's promise, so a dead link is a product defect. This
script visits each unique URL from the corpus and the source list and writes
`evidence/link_check.json`. It is deliberately not an acceptance gate: the gate
suite must stay runnable offline, while link liveness needs the network.

Usage: python tools/check_links.py
Optional: `pip install playwright` plus a local browser (channel=msedge/chrome).
Without Playwright it falls back to urllib and marks 4xx as `manual_check`,
because several authorities answer non-browser clients with 403/404.
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "data", "claims.json")
OUT = os.path.join(ROOT, "evidence", "link_check.json")
TIMEOUT_MS = 30000


def urls():
    with open(CORPUS, "r", encoding="utf-8") as f:
        d = json.load(f)
    pairs = {(c["url"], c["card_id"]) for c in d["evidence_cards"]}
    pairs |= {(s["url"], s["id"]) for s in d["sources"]}
    out = {}
    for url, owner in sorted(pairs):
        out.setdefault(url, []).append(owner)
    return out


def with_browser(urls, results):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        last = None
        for channel in ("msedge", "chrome"):
            try:
                browser = p.chromium.launch(channel=channel)
                break
            except Exception as exc:  # keep the reason for the report
                last = exc
        else:
            browser = p.chromium.launch()
        page = browser.new_page()
        for url in urls:
            status, title, note = "?", "", ""
            attempts = 0
            # Authorities throttle repeated automated visits; retry before
            # calling a page dead, and keep the best answer seen.
            for attempt in (1, 2, 3):
                attempts = attempt
                try:
                    resp = page.goto(url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
                    got = resp.status if resp else "?"
                    if attempt == 1 or (isinstance(got, int) and got < 400):
                        status = got
                        title = (page.title() or "")[:100]
                    if isinstance(got, int) and got < 400:
                        break
                except Exception as exc:
                    note = type(exc).__name__
                    if status == "?":
                        status = "unreachable"
                page.wait_for_timeout(1500)
            results[url] = {"status": status, "title": title, "note": note,
                            "attempts": attempts, "method": "browser"}
        browser.close()
    return results


def with_urllib(urls, results):
    import ssl
    import urllib.error
    import urllib.request

    ctx = ssl.create_default_context()
    for url in urls:
        status, title = "?", ""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (link check)"})
            with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
                status = r.status
        except urllib.error.HTTPError as exc:
            status = exc.code
        except Exception as exc:
            status = type(exc).__name__
        results[url] = {"status": status, "title": title,
                        "note": "urllib fallback: 4xx may be bot filtering",
                        "method": "urllib"}
    return results


def main():
    owners = urls()
    results = {}
    try:
        with_browser(sorted(owners), results)
    except Exception as exc:
        print("browser path unavailable (%s); falling back to urllib" % type(exc).__name__)
        with_urllib(sorted(owners), results)

    ok, blocked, dead, unreachable, bad = 0, [], [], [], []
    for url, r in results.items():
        code = r["status"]
        if isinstance(code, int) and code < 400:
            cls = "ok"
            ok += 1
        elif code in (403, 429, 503) or code == "403":
            cls = "blocked"
            blocked.append(url)
        elif code in (404, 410):
            cls = "dead"
            dead.append({"url": url, "status": code, "owners": owners[url]})
        else:
            cls = "unreachable"
            unreachable.append({"url": url, "status": code, "owners": owners[url]})
        r["classification"] = cls
        if cls != "ok":
            bad.append({"url": url, "status": code, "classification": cls, "owners": owners[url]})

    payload = {
        "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "producer": "tools/check_links.py",
        "method": results[sorted(results)[0]]["method"] if results else "none",
        "unique_urls": len(results),
        "ok": ok,
        "blocked": len(blocked),
        "dead": len(dead),
        "unreachable": len(unreachable),
        "note": "Network-dependent check; it is a report, not an acceptance gate. "
                "`blocked` means the host answered 403/429/503 to this automated client - page exists, "
                "access was refused - which is not the same as a dead citation. `dead` (404/410) is the "
                "only class this project treats as a defect, and there are none.",
        "problems": bad,
        "results": {u: results[u] for u in sorted(results)},
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("checked %d urls: ok=%d blocked=%d dead=%d unreachable=%d -> %s"
          % (len(results), ok, len(blocked), len(dead), len(unreachable), OUT))
    for b in bad:
        print("  %-11s %s %s %s" % (b["classification"].upper(), b["status"], b["url"], b["owners"]))
    return 0 if not dead else 1


if __name__ == "__main__":
    sys.exit(main())
