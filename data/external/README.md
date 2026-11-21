# data/external

Everything in this folder is data the product did not author. Read
`../evidence/DATA_STATUS.md` first — it is the single source of truth for what was
collected, what failed, and why. `SOURCES.md` carries per-source licence and
redistribution terms.

```
samples/            1,200 benchmark claims (dev/holdback split), one JSONL per dataset
                    + sample_manifest.json (counts, mapping, raw hash)
                    + samples_index.json (status incl. failed datasets)
pages/              41 archived HTML pages, named sha256(url)[:16].html
                    + pages_index.json (sha256, bytes, live|archived_copy, timestamp)
                    (gitignored: the index is the committed artefact, not the HTML)
synthetic/          400 × 2 clean-room rows + synth_checks.json + attestation
                    synthetic demo data — NOT a benchmark
```

Paragraph text, offsets and per-card resolution live in `../evidence/`:

```
paragraphs.jsonl        1,812 paragraphs with page/paragraph hashes
cards_evidence.jsonl    100 cards: matched | reason | score | offsets | hashes
retractions.jsonl       41 sources: retraction_status + checked_at
external_eval.json      dev-slice metrics for the offline kernel
withdrawn_demo.json     synthetic retraction, before/after verdict
DATA_STATUS.md          collection status + acceptance checklist
```
