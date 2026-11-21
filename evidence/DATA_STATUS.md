# External data status — what was actually collected

**Scope:** Tier 0 of `DATA_PLAN.md` (benchmarks, paragraph snapshots, retraction sweep,
external evaluation). Tier 1 (subscriptions) and Tier 2 (human sessions) are out of scope
for an agent run and are left to the user.
**Run date:** 2026-11-20 (UTC). **Seed:** 20261120. **Producer:** data-supply agent
(`D:\桌面\数据Agent工程化`, package `datasupply.claim`).
**Rule applied throughout:** no fabrication. Every gap below is a reported failure with a
reason, not a silent substitution.

---

## 1. Headline numbers

| Item | Result | Target in plan |
|---|---|---|
| Sources with a paragraph snapshot | **41 / 41** | 41 / 41 |
| Paragraph rows stored | **1,812** (1,800 live + 12 language-variant) | — |
| Cards resolved to a paragraph + offset + hash | **97 / 112 (87%)** = 75 matcher + 10 manual same-page review + 12 cards added from archived paragraphs | 100% |
| Claims (after de-duplicating identical claim text) | 99 | — |
| Benchmark rows sampled | **1,200** (5 datasets) | ~1,500 (6 datasets) |
| Sources with freshness date + retraction status | **41 / 41** (`not_indexed` for DOI) | 100% |
| External dev-slice accuracy | **above baseline on 1 of 5, below on 4; 11 answered, 10 right, 1 adjudicated** (see §5) | reported honestly |

The two results that matter for the submission: citations are now **87% offline-verifiable**
(up from 0%, from 75% after a second manual re-read of the same pages, and from 85% before the 12-card expansion), and the external
numbers show the kernel does **not** generalise beyond its own corpus — but the same claims
found a real defect (a topic tag buying a verdict), which is now a guard and a gate rather
than a footnote. The second is the finding the plan was written to expose.

---

## 2. Paragraph-level evidence snapshots

`evidence/paragraphs.jsonl` (1 row per paragraph, 1,812 rows), `evidence/cards_evidence.jsonl`
(1 row per card, 100 rows), `data/external/pages/pages_index.json` (page hashes).

| Measure | Value |
|---|---|
| Pages fetched successfully | 41 / 41 |
| Pages that needed a Wayback archived copy | 3 (`USDA-MW`, `USDA-FOOD`, `NIH-ODS-VITD`, all live 403) |
| Archived copies are labelled | `page_nature="archived_copy"` + `archive_timestamp` + `original_url_status=403` |
| Low-yield pages | `NCI-ALK` 1 paragraph / 193 chars (page now serves an executive-order banner, not the article); `WHO-COVID` 2 paragraphs / 83 chars (hub page) |
| Fetch politeness | 1 request per URL, 2 s delay, project UA, robots.txt honoured |

**Card → paragraph resolution.** Method `semantic_lexical/v3`: MiniLM sentence embeddings
(ONNX, local) × 0.5 + snippet-token coverage in the candidate paragraph × 0.5, plus a number
check; threshold 0.50 fixed before evaluation, not tuned per card.

| Reason | Cards |
|---|---|
| matched by the matcher (threshold 0.50) | 75 |
| recovered by manual same-page review (`data/external/cards_evidence_review.json`) | 10 |
| below threshold, still unresolved (page text does not contain the claim's specifics) | 8 |
| language mismatch, still unresolved (page is Chinese, snippet English — `CDSTM-BRAIN`) | 4 |
| page too thin to contain the body (`WHO-COVID` hub) | 1 |
| explicit page-status flags (`source_changed` `CDC-AUT`, `page_changed` `NCI-ALK`) | 2 |

For `WHO-FLU-5M`, the official English edition of the same WHO document was fetched and 3
of 5 cards resolved there; `alignment_url` records the variant page while `url` keeps the
Chinese citation. `CDSTM-BRAIN` has no English edition, so its 3 cards stay unresolved.

**Honest read:** the 8 remaining `below_threshold` cards are not a matcher defect alone — some
of their cited pages no longer carry the specific sentence (`NCI-ALK` now serves a federal
notice banner instead of the article body, which is also why it yields a single 193-character
paragraph), some are hub pages that only list article titles (`CDC-ABX`), and the sleep page
carries its hours in a table the extractor does not turn into paragraphs. The 10 manual
recoveries were accepted only when the paragraph sits on the card's own page and literally
addresses the claim; the threshold was not lowered and no cross-source paragraph was used. That is exactly the "page changed under us" signal the plan wants surfaced, and
it is why the resolution rate is not forced to 100%.

---

## 3. Retraction / correction sweep

`evidence/retractions.jsonl` (41 rows).

- All 41 sources are institutional web pages: **no DOI, no PMID** → `retraction_status:
  not_indexed`, stated as such rather than faked.
- Page-text marker scan (`retracted|withdrawn|correction|erratum|superseded`) found **0**
  explicit markers; `status: none_detected`, `checked_at` per row.
- Crossref / OpenAlex / Europe PMC work-level checks are **not applicable** here and are not
  claimed. The one demo of "withdrawn evidence" is `evidence/withdrawn_demo.json` and uses a
  **synthetic** retraction signal, clearly disclaimed; it shows the mechanic (verdict drops
  from `refuted` to `undetermined`, status `suspect`, card removed from the usable set),
  not a real accusation against any source.

---

## 4. Benchmark samples

`data/external/samples/*.jsonl` + `sample_manifest.json` + `samples_index.json`.
70 / 30 dev / hold-back via `sha256(dataset|sample_id) % 10 < 7`. Overlap with
`golden_set.json` / `guard_set.json` removed (token Jaccard ≥ 0.60), never relabelled.

| Dataset | Rows | Label mix (sampled) | Dev / hold-back |
|---|---|---|---|
| FEVER | 300 | supported 100 / refuted 100 / undetermined 100 | 203 / 97 |
| HealthVer | 300 | supported 84 / refuted 61 / undetermined 155 | 214 / 86 |
| AVeriTeC | 200 | supported 53 / refuted 131 / undetermined 16 | 149 / 51 |
| PUBHEALTH | 200 | supported 119 / refuted 72 / undetermined 9 | 143 / 57 |
| VitaminC | 200 | supported 99 / refuted 72 / undetermined 29 | 131 / 69 |
| **SciFact** | **0** | — | — |

**Why SciFact is 0.** The public archive downloaded on 2026-11-20
(`scifact_data.tar.gz`, 3,115,079 B, sha256 `11c621288d41…`) contains
`data/claims_dev.jsonl` and `data/claims_train.jsonl` **without a `label` field**; the
GitHub raw copies return 404. Labels cannot be recovered from evidence lists without
inventing them, so the dataset is reported as not collected.

**Corrections to `DATA_PLAN.md`:**
1. **CoVERT** is 300 tweets in the released corpus, not ~3.4k; the old GitHub path 404s. Not collected.
2. **HealthVerity** is a commercial claims-data vendor, not a benchmark. Replaced by
   **HealthVer** (`github.com/sarrouti/healthver`, CC BY 4.0).
3. FEVER's native labels are `SUPPORTS` / `REFUTES` / `NOT ENOUGH INFO` (not
   `SUPPORTED` / `REFUTED`); the mapping table in the plan should say so.
4. `covert` and `healthverity` rows are carried in `samples_index.json → failed`, not dropped.

---

## 5. External evaluation (dev slice, five passes)

`evidence/external_eval_v4.json` is the current run; `evidence/external_eval_v3.json`,
`evidence/external_eval_v2.json` and `evidence/external_eval.json` (v1) are kept so the
change is auditable rather than asserted. Kernel run offline (`use_llm=False`), one verdict
per claim, seed 20261120, dev slice first; **the hold-back slice was opened once at the end** (§5.1).

| Dataset | n | Accuracy (v5) | v4 | v3 | v2 | v1 | Macro-F1 | Refusal (v5) | On decided (v5) | All-`undetermined` baseline |
|---|---|---|---|---|---|---|---|---|---|---|
| FEVER | 203 | 0.315 | 0.315 | 0.315 | 0.315 | 0.310 | 0.160 | 1.000 | — (0 decided) | 0.345 |
| HealthVer | 214 | 0.556 | 0.551 | 0.542 | 0.542 | 0.491 | 0.327 | 0.963 | 0.875 | 0.523 |
| AVeriTeC | 149 | 0.094 | 0.094 | 0.094 | 0.107 | 0.154 | 0.067 | 0.980 | 1.000 | 0.658 |
| PUBHEALTH | 143 | 0.056 | 0.056 | 0.056 | 0.056 | 0.063 | 0.035 | 1.000 | — (0 decided) | 0.601 |
| VitaminC | 131 | 0.176 | 0.176 | 0.176 | 0.176 | 0.176 | 0.100 | 1.000 | — (0 decided) | 0.489 |
| SciFact | — | not collected | — | — | — | — | — | — | — | — |

**What the five passes say.** v1 answered 89 dev claims and got 58 of them wrong: a card
tagged `COVID-19` was deciding any sentence containing "COVID-19", because the matched
anchors were `['19', 'covid']` — a digit and a filing label. v2 added `topic_only` (a card
whose only matched words are its own tags cannot decide) and fell to 19 answered / 11 wrong.
v3 excludes relation verbs from the anchor test and adds `thin_anchor` (a six-plus-word claim
sharing exactly one word with a card is a topic collision): 10 answered, 8 right. v4 adds an
explicit endpoint class (risk / cure / prevention / transmission / harm / severity) and gates
sentences that only report that research exists, then expands the corpus from 100 to 112
cards: **12 answered, 10 right**. v5 changes no guard and no threshold; it normalises outcome
classes (`tumour/tumor/neoplasm/carcinoma` → cancer, `coronavirus/SARS-CoV-2/COVID-19` → covid)
so that a shared topic word is no longer a shared event: **11 answered, 10 right, 1 wrong.**
Accuracy per dataset barely moves, because accuracy counts refusals as errors — the honest
summary is precision bought with coverage, and both numbers are published.

**The one error that remains (v5), stated exactly:**
- `The pandemic coronavirus will wane with warmer weather, like some other respiratory viruses.`
  gold `supported`, kernel `refuted` on E117 ("Cold weather kills the coronavirus", a WHO myth
  card). The same sentence occurs 12 times in `healthver_dev.csv` with **8 Supports / 3 Refutes
  / 1 Neutral**, and 115 of the file's 230 distinct claim texts carry more than one gold label
  (1,071 of 1,917 rows). The label on this row is not a settled fact about the claim, so the
  entry in `data/error_review.json` records the disagreement, the label counts and the measured
  cost of the only patch that would flip it (a hedge/modal rule: 3 correct answers lost for 2
  recovered). It is not counted as a rule violation, and it is not patched away.
- The other v4 error — `dry indoor air may encourage Coronavirus spread`, refuted by the
  ventilation card — is gone: it is now refused with E122 named as a near miss on
  `different_object` (a cancer card cannot settle a coronavirus claim), while
  `Exposure to air makes a tumour spread` is still refuted by that card and
  `Cold weather kills the coronavirus` still by E117. H37–H39 hold both directions in the
  guard set.

**Reading, without spin:** the kernel answers about 1.3% of externally written claims. When
it does answer, it is right 10 times in 11; on the rest it refuses. Against the trivial
"always undetermined" baseline it is above on one dataset (HealthVer, 0.556 vs 0.523) and
below on four, because those slices are mostly `supported`/`refuted` and refusing is scored
as a miss. Two consequences:
- The kernel's coverage, not its rules, is the binding constraint on external accuracy.
- Selective accuracy at 50% coverage does not rescue the accuracy figure (FEVER 0.297),
  because the confidence proxy is stance-margin, which is high on confidently wrong calls;
  the fix that did work was tightening what counts as an anchor, not re-ranking by margin.

### 5.1 Hold-back slice, opened exactly once

The hold-back slice (360 claims: FEVER 97, HealthVer 86, AVeriTeC 51, PUBHEALTH 57,
VitaminC 69) was scored once, after the kernel and the corpus were frozen at 112 cards, and
before any further tuning. It is stored in `evidence/external_eval_holdback.json`; it is
deliberately **not** an acceptance gate, because a one-shot slice that a build can fail
becomes a set someone will tune against. Its numbers belong to the kernel that was frozen at
that moment: they are history, the slice is not re-scored after the v5 outcome fix, and the
ledger makes a re-open a visible act.

| Dataset | n | Accuracy | Refusal | All-`undetermined` baseline |
|---|---|---|---|---|
| FEVER | 97 | 0.371 | 1.000 | 0.371 |
| HealthVer | 86 | 0.547 | 0.895 | 0.500 |
| AVeriTeC | 51 | 0.118 | 0.980 | 0.647 |
| PUBHEALTH | 57 | 0.018 | 1.000 | 0.579 |
| VitaminC | 69 | 0.087 | 1.000 | 0.507 |

**10 answered, 5 right, 5 wrong** — decisions land exactly on a coin flip out of sample,
against 10 right of 11 on dev. The five errors are printed below, because they are the
argument for the next milestone. One of them is in the same family as the dev row that
survived: the corpus holds the myth card ("hot weather stops the spread"), not a seasonality
card, so the kernel answers a neighbouring question.
- `Favipiravir … is currently being studied` (gold supported) → refuted: a sentence about a
  trial in progress, again an endpoint/shape mismatch.
- `Coronavirus can Be Crushed By Warmer Weather` and `The pandemic coronavirus will wane
  with warmer weather` (gold supported) → refuted on E116: the corpus has the myth card and
  not the seasonality card.
- `no clinical evidence on vitamin D in COVID-19` (gold refuted) → supported: a negation
  scoped to evidence, read as evidence about vitamin D.
- `5G networks facilitate the spread of the coronavirus` (gold supported) → refuted on a
  COVID-19 transmission card: a claim outside the corpus's scope answered by a neighbour.

The honest reading: on claims written by strangers the kernel is safe (it refuses 95–100%)
but its few decisions are not better than chance. Coverage and claim shape, not extra guards,
are what move this number.

### 5.2 A receipt for the run itself

Every number in this file was once a sentence in a document, and a sentence about a run is
not a run. `tools/make_receipt.py` now performs the acceptance itself and writes
`evidence/run_receipt.json`: exit code, a SHA-256 of the audit's own output, the command,
UTC time, the interpreter and Node versions, the gate tally, and the SHA-256 of 15 artefacts
(seven kernel modules including `core/plan.py`, `data/claims.json`, the golden and guard sets,
both evidence files, `web/index.html`, `web/app.js`, `tools/js_ui_verify.js`). Gate **A37**
recomputes all of it.

Shipped receipt: id `bf5a44781b881687ec175643f10e6c9b`, exit 0, 42 attested gates — the tree
carries 43, and A37 is excluded from the tally it attests, because no receipt could otherwise
be written. The run behind that receipt was green at 42 of 42 of the gates it could attest.
Tested by making it fail: one
artefact hash replaced by zeros gave `receipt_id_mismatch` + `artefact_changed` and a red run;
restoring the file returned green.

### 5.3 A receipt for the external table, and a ledger for the hold-outs

The dev numbers are recomputed by A35, which proves they reproduce today. It does not prove
which run produced them or that the sample files are the ones that produced them.
`tools/make_eval_receipt.py` runs the evaluation and the detail pass itself, then writes
`evidence/eval_receipt.json`: two run records with exit codes and output hashes, every
dataset's n / accuracy / refusal / answers / correct / wrong read back from the file the run
wrote, and the SHA-256 of 17 artefacts — five sample files, the samples index, both result
files, the hold-back result, the hold-back ledger, `data/claims.json` and the six kernel
modules. Gate **A39** recomputes the receipt id, requires zero drift against the live result
file, re-hashes every artefact, and requires the hold-back block to be one open from a file
whose hash still matches, with the ledger entry embedded in the receipt matching that run.

- Shipped receipt: id `f618f0cb0d2ddb7191378509675325c2`, 840 claims, 11 answered, 10 correct,
  1 wrong, 17 artefacts, hold-back recorded as opened once.
- Fault injection: setting `datasets.fever.answers` to 5 in the receipt produced two
  violations (`eval_receipt_id_mismatch`, `eval_drift:fever.answers`) and a red A39; restoring
  the file returned it to green.
- The hold-out cannot be quietly re-scored. `evidence/holdback_ledger.json` holds one entry
  for `holdback`, written from the result file of the single open at 14:43Z and marked
  `recorded_retroactively: true` because the ledger did not exist at the time. The tool now
  refuses a second scoring of a slice with an entry unless `--force-rerun` is passed, and that
  entry then carries `forced: true`.
- A second slice exists and is still sealed: 434 claims in `data/external/samples2/` (fever
  120 / healthver 74 / averitec 80 / pubhealth 80 / vitaminc 80), drawn from the raw archives,
  sha256-ordered for reproducibility, excluding every already-used sample and every corpus,
  golden and guard text, with `freeze.json` recording per-file hashes and the dedup counts.
  It has not been scored, so it can still be an out-of-sample check after the next change.

### 5.4 Where the coverage ceiling actually is

The 1.3% is the number most likely to be misread as a matcher that is too strict.
`tools/coverage_headroom.py` settles it on the dev slice (`evidence/coverage_headroom.json`):

- With every guard switched off, the highest share of any card's content restated by a refused
  claim is the 0.6–0.8 band, reached by 21 of 829 refusals; 438 restate less than a fifth. No
  threshold change can create an answer that no card supports.
- 280 of the 829 refusals share no content word with any card (outside the corpus's subject);
  549 are inside the subject and simply not asserted yet.
- Coverage inside the corpus's own subject is therefore **1.96% (11 of 560)** rather than
  1.31% of everything, and 0% on three of the five datasets even in-domain.
- The per-dataset split is in the file, with the 25 highest-overlap in-domain refusals listed
  as the missing propositions they are. Those are not used to author cards: a card written from
  a benchmark claim would be training on the test.

### 5.5 A session record, because the commercial paragraph had no evidence

`tools/session_log.py` records inputs, atoms, verdicts, cited source ids, kernel and corpus
fingerprints and an operator label; `tools/verify_sessions.py` replays each input and compares
all three; gate **A40** fails the build on an unreplayable record and prints the number of
sessions made by someone outside the build.

- Four records exist, all operator `self`. The oldest
  (`evidence/sessions/2026-11-20T15-50-06Z_self.json`, id
  `cc57c4a864fbdfce17cc3c8cb797d903`) has 6 inputs / 5 atoms / 2 answered / 3 refused / 1
  input with no checkable claim; the second (`2026-11-20T16-19-40Z_self.json`) recorded the
  outcome-class fix; the third (`2026-11-20T17-10-45Z_self.json`) was the list-mode and
  refusal-plan record. All three are labelled `historical:kernel_changed`: their verdicts belong
  to the kernel that wrote them, and the gate says so instead of replaying an old transcript as
  today's behaviour.
- The newest (`evidence/sessions/2026-11-20T18-01-06Z_self.json`, id
  `c87bc8d82cc86a65d9820e926100fd8f`) was recorded after a kernel-file rewrite and replays
  `replay_match`: 3 inputs, 2 answered, 1 refused — the refusal is the dry-air/coronavirus claim
  with E122 named as a different object, the two refutations are the tumour-spread claim and the
  cold-weather myth, i.e. the evidence that the outcome fix separated the pair without losing
  recall. It has to be re-recorded after any change to the six verdict-bearing modules, which is
  why the recorder and the replay are both shipped as tools rather than as a one-off transcript.
- `tools/run_external_session.py` walks a reviewer through three fixed claims in one named scenario
  (paper abstract, news brief or customer-service reply; one refuted, one supported, one refused),
  prints the real verdict, cited sources and refusal reason, and then writes the reviewer block as
  a normal session file; `--rehearse` prints without writing. The claims are fixed per scenario so
  that two outside sessions are comparable.
- A session by a `customer` or `external-reviewer` must also carry the reviewer block:
  `outcome` (`used` / `discarded` / `re_prompted` / `no_opinion`), a note of at least one real
  sentence, and `would_pay` (`no` / `unsure` / `yes`). `tools/session_log.py` refuses to write
  such a session without it, and `verify_sessions.py` / A40 report
  `external_session_missing_reviewer` or `reviewer_note_too_short` if one is edited in without
  it. A self session must not carry the block.
- Fault injection: flipping one verdict in the first record produced `session_id_mismatch` and
  `turn_0_verdict:supported!=refuted`; restoring the file returned it to structural validity
  (and to `historical` once the kernel changed).
- External operators: **0**. No customer has used the tool, and the gate says so rather than
  leaving it to prose. The reviewer block exists so that the first real one cannot arrive as
  praise with no outcome attached.

### 5.6 The last wrong verdict, and the benchmark's own contradictions

`data/error_review.json` holds one entry per wrong dev decision, and gate **A41** enforces it:
the entry set must equal the current wrong set in both directions, each entry is pinned to the
run's own gold / prediction / cited cards, and a `contradictory_benchmark_label` claim must
match a counted group in `evidence/label_conflicts.json`.

- Entry `ER-001` / `healthver-674`: gold `supported`, kernel `refuted` on E117, with
  `label_evidence` = raw `healthver_dev.csv`, that sentence **12 rows: 8 Supports, 3 Refutes,
  1 Neutral**. Category: `contradictory_benchmark_label`.
- The census behind it (`tools/check_label_noise.py`): committed samples 1,200 rows /
  1,052 distinct / **27 conflicting texts / 79 rows**; raw HealthVer dev 1,917 rows /
  230 distinct / **115 conflicting texts / 1,071 rows**. The samples half is recomputed live
  inside A41, so a hand-edited count fails the build; the raw half is a recorded measurement
  pinned by filename and a 64-hex SHA-256 of the CSV in the file (A41 fails with
  `label_evidence_not_pinned` if either is missing), because the raw archive is not part of
  the repo and a reader needs the hash to re-measure it.
- The only patch that would flip the row is a hedge/modal rule. Measured on the same 840 rows:
  3 correct answers lost, 2 errors recovered (one of them this row) — rejected on the numbers,
  and recorded in the entry rather than left to memory.
- Fault injection: changing the entry's `gold` to `refuted` gives `gold_mismatch:healthver-674`
  and 40/41; deleting the entry gives `unreviewed_wrong:healthver-674`; editing the claimed
  counts gives `label_counts_mismatch:healthver-674`.


`citation_precision / citation_recall` are reported as `null` with a reason: sampled
benchmark evidence documents deliberately carry **no URLs**, so URL-level citation metrics
cannot be computed on this slice. The paragraph-level equivalents are in
`evidence/cards_evidence.jsonl`.

---

## 6. Acceptance checklist (`DATA_PLAN.md` §7)

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Accuracy per dataset with n, seed, mapping, commit | **pass (numbers reported, commit = working tree)** | `evidence/external_eval_v4.json` |
| 2 | Sampled claims text-disjoint from golden/guard | **partial** — overlap filter runs in the sampler, not in the eval script | `sample_manifest.json → excluded_by_overlap` |
| 3 | Hold-back evaluated once | **pass** — one open, in `external_eval_holdback.json`, recorded in `holdback_ledger.json` (entry marked `recorded_retroactively`); a second scoring is refused by `tools/eval_external.py` unless forced; a second 434-claim slice is frozen and unscored (`data/external/samples2/`) | `holdback_ledger.json`, `samples2/freeze.json` |
| 4 | 100% citations resolve to stored paragraph + hash | **partial — 97/112; the 15 non-verified rows carry a reason, not a silent pass** | §2 table, `cards_evidence.jsonl`, `cards_evidence_review.json` |
| 5 | 100% sources freshness + retraction status | **pass** (`not_indexed` displayed) | `retractions.jsonl`, `pages_index.json` |
| 6 | Withdrawn-evidence demo recomputes verdict | **pass (synthetic signal, disclaimed)** | `evidence/withdrawn_demo.json` |
| 7 | κ ≥ 0.70 on 40 dual-annotated items | **not attempted** (Tier 2, human) | — |
| 8 | Usability note | **not attempted** (Tier 2, human) | — |
| 9 | SOURCES.md licence + redistribution | **pass** | `data/external/SOURCES.md` |
| 10 | One command per script, offline where possible | **partial** — wrappers need `DATASUPPLY_ROOT` | `tools/fetch_*.py`, `tools/check_retractions.py`, `tools/eval_external.py` |
| 11 | The green run is bound to the bytes it describes | **pass** — 14 artefacts, receipt id recomputed, exit code and interpreter checked; fails on a single altered hash | `evidence/run_receipt.json`, gate A37 |
| 12 | The shipped page was actually clicked | **pass** — 10/10 demos in Edge, 112 corpus items, 0 exceptions, 0 external requests; reported as `skipped_no_browser` where no browser exists | gate A38, `tools/browser_check.py` |

Frozen artefacts untouched: `tools/check_manifest.py` reports **0 hash mismatches and 0
missing files**; its 65 reported problems are all `[DRIFT] unlisted`, i.e. the new files in
this delivery (additive only).

---

## 7. Synthetic samples (not a benchmark)

`data/external/synthetic/` — 400 rows × 2 batches, generated in a clean room from the 75
verified observations only (label share, length, number rate, domain mix). `tier=S`,
`mode=simulate`, `generator_version=synth-1.0`, parent claim id on every row.

| Check | Result |
|---|---|
| T1 lineage (no orphan rows, no fact/simulated mixing) | **pass** (0 orphans, 0 bad tier) |
| Deterministic replay (same seed → byte-identical file) | **pass** |
| T3 cross-batch (length KS, label TV) | **pass** (KS 0.04, TV 0.068) |
| T2 drift vs facts (length KS) | **fail** — 0.21 vs critical 0.171 at n=400; prefix operators (`It is not true that…`, `A review says…`) lengthen claims by ~8 chars at the median |

T2 is left failing on purpose: the fix is length-neutral mutation operators or an offline
paraphraser, not a threshold change. These rows are **never** used for evaluation —
`DATA_PLAN.md` §9 explicitly rejects LLM-generated claims as a benchmark.

---

## 8. Reproduce

```bash
# agent side (owns network fetches and raw dumps)
export PYTHONPATH=/path/to/数据Agent工程化/src
python tools/run_claim_snapshots.py           # 41 pages, paragraphs, hashes
python tools/run_claim_resolve.py             # cards -> paragraphs
python -m datasupply.claim.retractions
python tools/run_claim_observations.py        # observations + gates
python -c "from datasupply.claim.benchmarks import build_all; build_all()"
python tools/run_claim_synth_checks.py
python tools/build_claim_delivery.py          # writes into this repo

# repo side
python tools/eval_external.py --split dev
python tools/check_manifest.py                # frozen-file integrity
```

---

## 9. What this means for the submission

1. **Use the 97 verified cards as the citation story.** Every one of them now has paragraph
   text, character offsets, page hash and paragraph hash; a judge can recompute all four
   offline, and the page shows the quoted paragraph with its character range. Say 85%, not "all".
2. **Lead with the external failure, not around it.** "On 1,200 claims we did not write, the
   kernel refuses 76–99.5% of the time and scores below the all-undetermined baseline on four
   of five datasets" is a stronger originality claim than a cherry-picked number, and it
   points at the next milestone: retrieval coverage, not more rules.
3. **The 15 unresolved cards are evidence, not debt.** Each carries the paragraph that came
   closest and the reason it failed; several are pages that changed since the card was
   written. That is the "sources expire" demo, with hashes.
4. **Do not present the synthetic rows as benchmark data.** They exist to show the isolation
   and replay mechanics; T2 still fails.

