# Data plan — what would actually make Claim Autopsy better

**Status:** written 2026-11-20 as an acquisition contract; items 1, 2 and 3 have since been
collected and are in the repo. Item 4 (human review) is still open.
**Premise:** the corpus is now 112 cards / 41 sources, the golden set 93 cases, the guard
benchmark 39 probes, and the kernel passes A1–A44. A separate coverage audit records why adding
pages alone could not fix the 1.96%: even with the benchmark's own gold evidence the lexical
ceiling is 30.0%, which is why citation mode was added alongside the corpus.

**Collection result (2026-11-20):**

| # | Collected | Acceptance line | Outcome |
|---|---|---|---|
| 1 | 1,200 claims from FEVER, HealthVer, AVeriTeC, PUBHEALTH, VitaminC (`data/external/samples/`) | ≥1,000 claims, fixed split, committed result file | met; scored on dev only (`evidence/external_eval_v4.json`), accuracy 0.315 / 0.556 / 0.094 / 0.056 / 0.176 against baselines 0.345 / 0.523 / 0.658 / 0.601 / 0.489 — **above baseline on 1/5**; the kernel answers 11 of 840 claims and gets 10 right (v1 answered 89 and got 58 wrong); the one remaining error is adjudicated in `data/error_review.json` against a label census showing 115 of 230 HealthVer dev claim texts carry contradictory gold labels |
| 2 | 1,812 paragraphs / 41 sources + one resolution row per card (`evidence/paragraphs.jsonl`, `evidence/cards_evidence.jsonl`) | every citation resolvable offline with selector + offset + SHA-256 | 97/112 verified, 13 unresolved with a reason, 1 page replaced, 1 source reworded, 0 hash mismatch (gate A34) |
| 3 | Retraction index (`evidence/retractions.jsonl`) | signal attached to every cited source | 41/41 `not_indexed`, 0 page-level markers; `evidence/withdrawn_demo.json` is synthetic and labelled as such — not counted as a capability |
| 4 | Human walkthrough | ≥3 external users, task success recorded | **not done**; the recorder and a guided protocol in three scenarios — paper abstract, news brief, customer-service reply (`tools/run_external_session.py`) — are ready, but no outside person has run them yet |

Adding more self-authored cards has hit
diminishing returns: every new card is still written by the same author as the expected
answer. The next gains come from **four kinds of external data**, not from a bigger corpus.

| # | Missing data | What it fixes | Scoring weight it feeds |
|---|---|---|---|
| 1 | Public claim-verification benchmarks | "you graded your own exam" | Testing & expression (20%), originality (25%) |
| 2 | Paragraph-level evidence snapshots | citations cannot be checked against the source | Usefulness & UX (25%), testing (20%) |
| 3 | Retraction / correction signals | evidence is treated as permanently valid | Originality (25%) |
| 4 | Human task and annotation data | no proof anyone but the author can use it | Usefulness & UX (25%) |

Everything below is written as an acquisition contract: what, where, which fields, how it
enters the repo, and how it is accepted. Anything that cannot meet its acceptance line is
reported as a failure, not quietly dropped.

---

## 1. What "better" has to mean, numerically

Five measurable targets. If a data item does not move one of these, it is not worth collecting.

1. **External accuracy.** Three-state accuracy on at least 1,000 claims the author never wrote,
   reported per dataset, with a fixed seed and a committed result file.
2. **Citation verifiability.** For every cited card, the claim text must be locatable in the
   stored source snapshot (paragraph + character offset + SHA-256). Target: 100% of citations
   resolvable offline, 0 citations pointing at a page that changed under us.
3. **Evidence freshness.** Share of sources fetched within 180 days, and share of sources
   checked against retraction/correction records. Target: 100% checked, staleness displayed.
4. **Refusal calibration.** Selective accuracy across the abstention boundary: report
   accuracy at 100% coverage, at 70% coverage and at 50% coverage, so "refuses a lot" and
   "refuses well" become different numbers.
5. **Human usability.** 5–8 participants, 3 tasks each, task success rate, time on task,
   SUS score, and a written list of misinterpretations.

---

## 2. Tier 0 — collectable by the agent, no account, no payment

### 2.1 Public claim-verification benchmarks

The single highest-value item. These give a genuinely held-out test set whose labels were
written by someone else, which is exactly what an "accuracy" claim needs.

| Dataset | Scale | Native labels | Why it fits | Access |
|---|---|---|---|---|
| FEVER | ~185k claims from Wikipedia | SUPPORTED / REFUTED / NOT ENOUGH INFO | Label space is isomorphic to our three-state verdict | `fever.ai` |
| SciFact | ~1.4k claims, 518 abstracts | SUPPORT / REFUTE / NO INFO | Scientific claims with abstract-level evidence; closest to this product | `github.com/allenai/scifact` |
| HealthVerity | ~15k health claims | Supported / Refuted / Not Enough Info + evidence | Health domain, matches the corpus | official repo, follow its download instructions |
| CoVERT | ~3.4k COVID claims | three-state + evidence | Real-world rumour phrasing | GitHub, search `CoVERT claim verification` |
| PUBHEALTH | ~12k claims | true / false / unproven / mixture | Stress-tests mapping honesty | `github.com/neemakot/Health-Fact-Checking` |
| VitaminC | ~4.8k claims + rationales | SUPPORT / REFUTE + evidence sentences | Gives sentence-level rationales to compare against our citations | `github.com/TalSchuster/VitaminC` |
| AVeriTeC | ~4.5k claims | Supported / Refuted / Not Enough Evidence / Conflicting | Web evidence, closer to our card shape | `github.com/MichSchli/AVeriTeC` |

**Sampling contract**

- 300 claims per dataset for FEVER, SciFact, HealthVerity; 200 for CoVERT, PUBHEALTH,
  AVeriTeC; total ~1,500.
- Stratified by label and domain, fixed `random_state`, sample ids committed.
- 70% dev slice (used to find failures), 30% hold-back slice (touched once, at the end).
  No rule may be tuned on the hold-back slice.
- Text-normalised overlap check against `data/golden_set.json` and `data/guard_set.json`;
  any hit is removed and replaced, never relabelled.
- Raw dumps stay out of git (FEVER wiki pages are multiple GB). Only the sampled JSONL,
  the sampling script and the result file are committed.

**Label mapping (must be printed in the report, not hidden)**

| Source label | Our verdict | Note |
|---|---|---|
| SUPPORTED / SUPPORT / true | supported | direct |
| REFUTED / REFUTE / false | refuted | direct |
| NOT ENOUGH INFO / NO INFO / unproven | undetermined | source-specific gap semantics, see below |
| mixture (PUBHEALTH) | excluded | not a three-state case; reported separately |
| Conflicting (AVeriTeC) | excluded | our product labels conflicts inside a submission, not inside a source set |

**Honesty rule.** FEVER's NOT ENOUGH INFO means "Wikipedia does not contain the evidence",
not "our corpus does not contain it". We therefore report two numbers per dataset:
three-state accuracy over all sampled claims, and accuracy restricted to claims whose gold
evidence is present in our corpus. Reporting only the first would be a scoring trick; the
pair is the honest result.

**Required output per dataset** in `evidence/external_eval_v4.json` (v1, v2 and v3 are kept for comparison):
`{dataset, n, mapping, accuracy, macro_f1, per_label{precision,recall}, refusal_rate,
selective_accuracy{100,70,50}, citation_precision, citation_recall, runtime_s, seed, commit}`.

`citation_precision` is defined as: cited card's source URL equals the gold evidence URL
(normalised) **or** the cited paragraph overlaps a gold evidence sentence by ≥0.5 token
Jaccard. `citation_recall` is the share of gold evidence documents that produced at least
one citation. The second metric is only computable after item 2.2 exists.

### 2.2 Paragraph-level evidence snapshots

Today a card is one hand-written sentence plus a URL. A judge cannot tell whether the
sentence is faithful. This turns each card into a verifiable record.

**Sources to snapshot** (all public, all already in or adjacent to the whitelist):

- CDC: Health Myths, Vaccine Safety, Antibiotic Do's and Don'ts, Physical Activity, Sleep, Sodium, Sun Safety, Fluoridation, Tobacco, Measles.
- WHO: Question & Answer pages, Myth busters.
- NIH: NCCIH "Know the Science", NHLBI, NIA.
- NCI: Common Cancer Myths and Misconceptions, Diet and Cancer.
- FDA: Health Fraud and Scams, consumer updates.
- NHS: Behind the Headlines archive.
- Mayo Clinic: Diseases & Conditions "myths" pages.

**Record schema** (one JSONL row per paragraph):

```json
{"card_id": "E092",
 "source_id": "CDC-ABX",
 "url": "https://www.cdc.gov/...",
 "fetched_at": "2026-11-21T10:00:00Z",
 "published_or_updated": "2024-04-01",
 "paragraph_index": 3,
 "paragraph_text": "...",
 "selector": "main > section:nth-of-type(2) p:nth-of-type(3)",
 "char_offset": [1840, 2061],
 "sha256_of_page": "...",
 "sha256_of_paragraph": "...",
 "language": "en"}
```

**Fetcher contract**: one request per URL, 2 s delay, `User-Agent` identifying the project,
respect `robots.txt`, store raw HTML under `data/external/pages/` (git-ignored beyond 200 KB
per file, only hashes committed). Re-fetch monthly; a changed hash marks the card
`source_changed` and blocks citation until re-reviewed.

**Acceptance**: every one of the 41 sources has at least one snapshot; every card resolves to
a paragraph; 0 cards cite a paragraph that fails its own hash; the page shows "verified
against snapshot of YYYY-MM-DD" on each evidence card.

### 2.3 Retraction and correction signals

This is the cheapest originality point available: almost no demo in this space admits that
evidence can expire.

- **Crossref REST** `https://api.crossref.org/works/{doi}` → fields `relation`,
  `update-to`, `updated-by`; a retraction appears as a relation of type `is-retracted-by`.
- **OpenAlex** `https://api.openalex.org/works?filter=doi:{doi}` → `is_retracted`,
  `is_paratext`, `cited_by_count`.
- **Europe PMC** `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=...&format=json`
  → `pubType` includes `Retraction of publication`, `Erratum`.
- **PubPeer** public pages (no official API; obey terms and rate limits).
- **Retraction Watch Database** — bulk access requires an application; until granted, use
  Crossref as the machine-readable substitute and say so.

**Record schema**: `{source_id, doi, pmid, checked_at, status: ok|corrected|retracted|
expression_of_concern, evidence_url, note}`.

**Product behaviour**: a retracted or corrected source cannot support a verdict. The card is
kept for transparency but rendered as "withdrawn evidence" with the correction link, and the
verdict recomputes without it. This must be demonstrated with one crafted card so judges can
see the mechanism, not just read about it.

**Acceptance**: all 41 sources resolved (DOI/PMID where available; grey literature marked
`not_indexed`); 0 sources silently skipped; one screenshot showing a withdrawn-evidence card.

### 2.4 Guideline and trial baselines

The dose and efficacy guards currently use hand-set thresholds. Anchor them to an external
authority instead.

- **ClinicalTrials.gov API v2** `https://clinicaltrials.gov/api/v2/studies` — phase, status,
  enrollment, primary outcome. Used to answer "is there a trial at this dose/outcome?".
- **WHO ICTRP** — international registry coverage for non-US trials.
- **USPSTF** recommendation grades (A/B/C/D/I) — the cleanest public grading scale for
  screening/prevention claims.
- **NICE** guidance and **GRADE** evidence tables — for "strength of recommendation" as a
  field on a card.

**Fields to attach to a card**: `evidence_level` (guideline | systematic review | RCT |
observational | mechanistic | none), `recommendation_grade`, `registry_ids`, `population`,
`outcome`, `dose`.

**Acceptance**: every dose-bearing card carries an `evidence_level`; A29's three dose probes
cite an external range rather than an internal constant; the card UI shows the level.

### 2.5 Free literature APIs (no subscription)

- **PubMed E-utilities**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` and
  `efetch` — 3 requests/second without a key; use a tool email.
- **Europe PMC REST** — full-text search, citations, retraction flags.
- **OpenAlex** — citation graph, `referenced_works`, `related_works`.
- **Semantic Scholar Graph API** — `paper/search`, `citations`, `tl;DR` summaries; free tier
  rate-limited.
- **arXiv / bioRxiv / medRxiv** — preprints, clearly labelled as non-peer-reviewed.

**Use**: for any claim with ≥2 cards, retrieve the citing literature and compute an
"agreement ratio" (how many independent sources support vs refute). This upgrades a card
from a single sentence to a small evidence set, and gives the UI something honest to show
when sources disagree.

---

## 3. Tier 1 — needs the user's login or an institutional subscription

Half a day of export work on the user side; the agent does the cleaning, joining and modelling.

| Source | What to export | Why it cannot be replaced |
|---|---|---|
| Cochrane Library | Reviews with conclusions, GRADE ratings, plain-language summaries | The only curated source of "certainty of evidence" |
| Embase / Scopus | Records for 30–50 claims: title, abstract, publication type, citations | Finds opposing studies a keyword pass misses; Scopus also gives citation counts |
| UpToDate / BMJ Best Practice | Topic summaries for 15 claims | Clinical bottom line written by clinicians, useful as an adjudication reference |
| PolitiFact API / Google Fact Check Tools API | Claim + ruling + source list, 300 rows | Human verdicts from professional fact-checkers; lets us report agreement with humans |
| Full Fact / AFP / Reuters Fact Check | Public fact-check articles (RSS/pages), 100 rows | Non-US coverage; adds phrasing variety |
| Snopes | Only if terms allow programmatic access | Popular-claim phrasing; otherwise skip and say so |

**Export format**: CSV/JSON with `claim, verdict, sources[], evidence_quote, reviewer,
published_at, url`. Keep the original file under `data/external/licensed/` (git-ignored) and
commit only derived, licence-cleared aggregates. Every dataset gets a row in
`data/external/SOURCES.md`: name, URL, licence, retrieval date, citation string, redistribution
allowed yes/no.

**Acceptance**: agreement-with-human-verdict rate computed on ≥300 claims, with disagreements
listed and explained; nothing paywalled is redistributed in the repo or the page.

---

## 4. Tier 2 — only humans can generate this

### 4.1 Usability sessions (5–8 participants, 3 tasks)

Tasks (the same script for everyone, read aloud, no coaching):

- **T0** Decide whether "Antibiotics cure a cold" is supported, refuted, or undecidable, and say why.
- **T1** Find the original source behind the verdict and confirm the quoted sentence exists.
- **T2** Explain why "Coffee causes cancer in children" was refused, in your own words.
- **T3** Paste two contradictory sentences and describe what the tool says about them.
- **T4** Find a topic the corpus does cover, starting from a refusal.
- **T5** Say what would make you distrust the verdict.

Recorded per participant: task success (yes/partial/no), seconds, verbatim confusion quotes,
one SUS form (10 items, 1–5), and one 1–5 trust rating. Anonymised id `P01…P08`; consent
script stored; no names, no contact details, no screen recordings of personal data.

**Deliverables**: `evidence/usability_note.md` (methods, results, quotes, fixes),
`data/human/usability_sessions.csv`, and a list of UI changes traced to a specific quote.

### 4.2 Dual annotation for inter-annotator agreement

- 40 items sampled from the 93 golden cases, stratified by label.
- Two annotators label independently: verdict (3 states) + which sentence decides it.
- Report Cohen's κ for verdict and for evidence sentence; disagreements adjudicated by a
  third pass, with the reason written down.
- Target κ ≥ 0.70 for verdict. Below that, the golden set is the problem, and we say so.

**Deliverables**: `data/human/annotations.csv`, `evidence/agreement.json`
(`{n, kappa_verdict, kappa_evidence, disagreements:[...]}`).

### 4.3 Error-analysis corpus

200 claims sampled three ways: 100 random from the corpus topics, 50 adversarial paraphrases
(negation, quantifier, population, relation swap), 50 out-of-corpus. For each, a human judge
records `kernel_verdict`, `expert_verdict`, `error_class` (lexical match, relation,
population, quantity/strength, object/outcome, multi-source conflict, corpus gap), and a
one-line justification. This is the input for the next guard set, and the honest "known
failure modes" section of the submission.

**Deliverables**: `data/human/error_analysis.csv`, `evidence/error_taxonomy.json`,
and at least three new guard probes derived from real errors.

### 4.4 Expert adjudication of boundary cases

10–15 cases where the kernel and the annotators disagree, sent to someone with domain
training (a public-health or statistics graduate student is enough). Purpose: separate
"our rule is wrong" from "the claim is genuinely ambiguous". Store the reasoning, not just
the label.

---

## 5. Schemas (copy-paste ready)

**Benchmark sample** `data/external/samples/fever.jsonl`

```json
{"id":"fever-000123","dataset":"fever","text":"...","gold":"refuted",
 "evidence_docs":[{"doc_id":"wiki-123","title":"...","url":"...","sentences":["..."]}],
 "domain":"health","split":"dev","mapped_from":"REFUTED"}
```

**Evidence snapshot** — see 2.2. One row per paragraph, hash + selector mandatory.

**Retraction record** — see 2.3.

**Annotation record** `data/human/annotations.csv`

```text
item_id,annotator,verdict,evidence_sentence_id,confidence,seconds,notes
G01,A1,refuted,S3,4,38,
G01,A2,refuted,S3,5,41,
```

**Usability record** `data/human/usability_sessions.csv`

```text
participant,task,success,seconds,sus_total,trust_1to5,quote
P01,T1,partial,74,68,3,"I could not tell which sentence was the source"
```

---

## 6. Layout and what is committed

```text
data/external/
  SOURCES.md            # licence, URL, retrieval date, citation, redistribution yes/no
  samples/              # 200-300 row JSONL per dataset, committed
  pages/                # raw HTML snapshots, git-ignored above 200 KB per file
  licensed/             # subscription exports, git-ignored, never redistributed
data/human/             # annotations, usability, error analysis (anonymised)
evidence/external_eval_v4.json
evidence/agreement.json
evidence/error_taxonomy.json
evidence/usability_note.md
tools/fetch_benchmarks.py
tools/fetch_snapshots.py
tools/check_retractions.py
tools/eval_external.py
tools/kappa.py
```

Rules: the deployed page never loads a benchmark or a human file; the page stays small and
static. Benchmarks are evaluation-only and never enter retrieval, so external labels cannot
leak into the product's answers.

---

## 7. Acceptance criteria (gate-style, one line each)

1. External accuracy is reported per dataset with n, seed, mapping and commit; no merged
   "overall accuracy" headline.
2. Every sampled claim is text-disjoint from the golden and guard sets; the overlap check is
   part of the eval script, not a manual step.
3. Hold-back slice is evaluated once; any rule change after that re-runs the whole suite.
4. 100% of citations resolve to a stored paragraph with a matching hash.
5. 100% of sources have a freshness date and a retraction status; "not indexed" is allowed
   but must be displayed as such.
6. One withdrawn-evidence demo exists and recomputes the verdict without the card.
7. κ ≥ 0.70 for verdict on 40 dual-annotated items, or a written explanation of why not.
8. Usability note contains methods, 5–8 participants, per-task success, SUS, and ≥5 concrete
   UI changes each traced to a quote.
9. `data/external/SOURCES.md` lists licence and redistribution status for every dataset; no
   paywalled text appears in the repo or the page.
10. All of the above is reproducible by one command per script, offline where possible.

---

## 8. Cost, time, and who does what

| Tier | Work | Who | Time | Cash |
|---|---|---|---|---|
| 0.1 | Benchmark download, adapters, first external numbers | agent | 1 day | 0 |
| 0.2 | 41-source paragraph snapshots + hashes + UI label | agent | 4–6 h | 0 |
| 0.3 | Retraction sweep for 41 sources + one withdrawn demo | agent | 2–3 h | 0 |
| 0.4 | Guideline/trial fields on dose cards | agent | 2 h | 0 |
| 0.5 | Literature agreement ratio for multi-card claims | agent | 3 h | 0 |
| 1 | Cochrane / Embase / UpToDate / fact-check exports | user (NTU login) | 0.5 day | subscription |
| 2.1 | Usability sessions | user + 5–8 volunteers | 3 h | 0 |
| 2.2 | Dual annotation + κ | user + 1 annotator | 2–3 h | 0 |
| 2.3 | Error analysis of 200 claims | agent proposes, user confirms | 4 h | 0 |
| 2.4 | Expert adjudication of 10–15 cases | user's contact | 1–2 h | 0 |

**Sequence that maximizes score per hour**

1. Day 1: benchmarks + adapters + first external accuracy (this alone answers the strongest
   judge objection).
2. Day 2: paragraph snapshots + retraction sweep (makes every citation checkable and gives
   the "evidence can expire" originality point).
3. Day 3: dual annotation + 5-person usability session (the only hard evidence for the 25%
   usefulness criterion).

---

## 9. What we explicitly do not need

- **WRDS / Compustat, Capital IQ Pro, Passport, CEIC, Bloomberg** — financial and market
  databases. They say nothing about health or science claims. Only relevant if a separate
  "corporate claim" track is opened.
- **Social-media scrapes** — terms-of-service risk, no ground truth, and the product does not
  adjudicate popularity.
- **Synthetic claims generated by an LLM as a benchmark** — a model grading a model; the
  current self-authored set is already stronger than that.
- **Full-text paywalled papers** — cannot be redistributed; conclusions plus citation are
  enough, and the licence column must say so.
- **More self-written cards** — the marginal card now teaches the kernel nothing that the
  guard set does not already test.

---

## 10. Risks and how each is handled

- **Licence contamination.** Every dataset row in `SOURCES.md`; paywalled text never committed;
  licence checked before any redistribution.
- **Benchmark leakage into tuning.** Dev/hold-back split, evaluation-only status, overlap
  check, and a rule that the hold-back slice is run once.
- **Mapping dishonesty.** FEVER's "not enough info" is about Wikipedia, not about us; both
  numbers are reported and the difference is named.
- **Repo and page size.** Raw dumps git-ignored; sampled JSONL only; the page never imports
  evaluation data.
- **API rate limits.** 2 s delay, tool email for NCBI, cached responses keyed by URL+date.
- **Retraction false positives.** Two-source confirmation (Crossref + Europe PMC) before a
  card is marked withdrawn; otherwise `status: unverified`.
- **Human data privacy.** Consent script, anonymised ids, no names or contact details, no
  personal screen recordings, raw forms stored outside the repo.
- **Staleness of snapshots.** Monthly re-fetch; hash mismatch marks the card for review
  instead of silently trusting the old text.
