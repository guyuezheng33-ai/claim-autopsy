"""Paragraph-level evidence snapshots, loaded from the archived-page delivery.

Every card in the corpus has one row in `evidence/cards_evidence.jsonl` recording
whether the claim could be located on the archived page, with the paragraph text,
character offsets and two SHA-256 hashes. Six cards were additionally confirmed by
a same-page manual review (`data/external/cards_evidence_review.json`), and two
pages are explicitly flagged as changed since the card was written.

The product uses this only to tell the reader what the citation rests on:

- `verified`      the claim is locatable on the archived page; the paragraph hash
                  is recomputed at load time, so a mismatch downgrades the status.
- `unresolved`    the page was archived but no paragraph carries the claim.
- `page_changed`  the page now serves something else (banner, hub, empty shell).
- `source_changed` the page still loads but its wording has been revised.

No status ever upgrades a verdict: a card with no snapshot is still cited, and the
reader sees that its source could not be re-verified. That is the honest failure
mode, not a hidden one.
"""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(ROOT, "evidence", "cards_evidence.jsonl")
PARAGRAPHS = os.path.join(ROOT, "evidence", "paragraphs.jsonl")
REVIEW = os.path.join(ROOT, "data", "external", "cards_evidence_review.json")

STATUS_TEXT = {
    "verified": "Archived snapshot verified",
    "unresolved": "No archived paragraph for this card",
    "page_changed": "The page now serves different content",
    "source_changed": "The page's wording has been revised",
    "hash_mismatch": "Snapshot hash does not match the stored paragraph",
}

_CACHE = None


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _excerpt(text, limit=180):
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def _reason_text(reason):
    return {
        "below_threshold": "the archived page no longer contains this claim's specifics",
        "language_mismatch": "the archived page is a Chinese edition; no English paragraph was archived",
        "thin_page": "the archived page is a thin landing page, not the article",
    }.get(reason, "no paragraph on the archived page matched this claim")


def _merge_paragraph(row, paragraph):
    """Overlay an archived paragraph row onto the card row."""
    if not paragraph:
        return row
    merged = dict(row)
    for key in ("paragraph_index", "paragraph_text", "selector", "char_offset",
                "sha256_of_paragraph", "sha256_of_page", "url", "source_id",
                "fetched_at", "page_nature", "alignment_url"):
        if key in paragraph:
            merged[key] = paragraph[key]
    merged["reason"] = "matched"
    return merged


def _record(row, status, note="", method=None):
    return {
        "status": status,
        "status_text": STATUS_TEXT.get(status, status),
        "source_id": row.get("source_id", ""),
        "url": row.get("url", ""),
        "alignment_url": row.get("alignment_url", ""),
        "fetched_at": row.get("fetched_at", ""),
        "page_nature": row.get("page_nature", ""),
        "paragraph_index": row.get("paragraph_index"),
        "selector": row.get("selector", ""),
        "char_offset": row.get("char_offset", []),
        "excerpt": _excerpt(row.get("paragraph_text", "")) if status in ("verified", "source_changed") else "",
        "sha256": row.get("sha256_of_paragraph", ""),
        "page_sha256": row.get("sha256_of_page", ""),
        "method": method or row.get("method", ""),
        "note": note,
        "reason_code": row.get("reason", ""),
        "score": row.get("score"),
    }


def load():
    """Return {card_id: snapshot record}. Computed once per process."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    rows = {r["card_id"]: r for r in _read_jsonl(CARDS)}
    paragraphs = {}
    if os.path.exists(PARAGRAPHS):
        for p in _read_jsonl(PARAGRAPHS):
            paragraphs[(p.get("source_id"), p.get("paragraph_index"))] = p

    review = {"confirmed": [], "flagged": []}
    if os.path.exists(REVIEW):
        with open(REVIEW, "r", encoding="utf-8") as f:
            review = json.load(f)

    flags = {f["card_id"]: f for f in review.get("flagged", [])}
    snap = {}
    for card_id, row in rows.items():
        if card_id in flags:
            f = flags[card_id]
            p = paragraphs.get((f.get("source_id", row.get("source_id")), f.get("paragraph_index")))
            merged = _merge_paragraph(row, p)
            rec = _record(merged, f["status"], note=f.get("note", ""), method="page_status_review/v1")
            snap[card_id] = rec
        elif row.get("reason") == "matched":
            snap[card_id] = _record(row, "verified")
        else:
            snap[card_id] = _record(row, "unresolved", note=_reason_text(row.get("reason")))

    for c in review.get("confirmed", []):
        card_id = c["card_id"]
        row = rows.get(card_id)
        p = paragraphs.get((c.get("source_id"), c.get("paragraph_index")))
        if not row or not p:
            snap[card_id] = _record(row or {}, "unresolved",
                                    note="review reference could not be resolved to an archived paragraph")
            continue
        merged = dict(row)
        for key in ("paragraph_index", "paragraph_text", "selector", "char_offset",
                    "sha256_of_paragraph", "sha256_of_page", "url", "source_id",
                    "fetched_at", "page_nature", "alignment_url"):
            if key in p:
                merged[key] = p[key]
        merged["reason"] = "matched"
        rec = _record(merged, "verified", note=c.get("note", ""), method="manual_review/v1")
        snap[card_id] = rec

    # Recompute the paragraph hash: a stored row whose text no longer hashes to its
    # own digest is downgraded rather than trusted.
    for card_id, rec in snap.items():
        if rec["status"] in ("verified", "source_changed") and rec["sha256"]:
            p = paragraphs.get((rec["source_id"], rec["paragraph_index"]))
            if p and _sha(p.get("paragraph_text", "")) != rec["sha256"]:
                rec["status"] = "hash_mismatch"
                rec["status_text"] = STATUS_TEXT["hash_mismatch"]
                rec["note"] = "recomputed hash differs from the stored paragraph hash"

    _CACHE = snap
    return snap


def get(card_id):
    return load().get(card_id)


def summary():
    snap = load()
    counts = {}
    for rec in snap.values():
        counts[rec["status"]] = counts.get(rec["status"], 0) + 1
    return {
        "cards": len(snap),
        "verified": counts.get("verified", 0),
        "unresolved": counts.get("unresolved", 0),
        "page_changed": counts.get("page_changed", 0),
        "source_changed": counts.get("source_changed", 0),
        "hash_mismatch": counts.get("hash_mismatch", 0),
        "counts": counts,
    }
