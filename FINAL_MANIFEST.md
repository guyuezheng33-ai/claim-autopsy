# Final manifest — what "final" means, and how to prove it later

Freeze point: **2026-11-21** (project root `claim-autopsy/`). This file records the exact byte state
that passed the acceptance suite, so a later change is detectable instead of being a matter of memory.

**Gate result at this freeze point** (generated from `evidence/acceptance_final.json`, never typed by
hand, so the summary below cannot drift from the run it describes):

```
total=48  passed=48  all_pass=True  run_tag=final  llm_mode="Local Qwen2.5-3B · llama.cpp CPU"
A10  PASS 112 cards (>=40), 41 sources (>=8), 0 off-whitelist URLs, 0 without status
A11  PASS accuracy 100.0% (93/93); distribution={'refuted': 41, 'supported': 37, 'undetermined': 15}; false refusals=...
A12  PASS consistency 100.0% (12/12); verdicts dropped to refusal=0
A13  PASS zero evidence + AI says supported -> undetermined; evidence + AI says refuted -> supported
A14  PASS 93 golden + 24 paraphrase pairs compared; 0 mismatches
A15  PASS 3 guard inputs checked; 0 unrelated sources entered citations
A16  PASS 6 polarity fixtures checked; 0 wrong
A17  PASS keys=0, CJK files=0, dangling doc paths=0
A18  PASS 4 recall guards checked (real id / stored stance / citation / relevance); 0 violations
A19  PASS 14 recorded cases cross-checked against the live benchmark; 0 violations; tampered counterexample rejected=...
A1   PASS 2 claims with no evidence, 0 verdicts leaked
A20  PASS browser lists 112/112 cards, 14 replay chips, 3 refusal renders; 0 violations; tampered counterexample reje...
A21  PASS 3 unreadable inputs refused with a full notice (kind/title/body/action), 0 verdicts leaked; front-end rende...
A22  PASS 3 injection payloads kept their verdict; 7700 chars refused as too_long; prompt data-quoted; 0 violations
A23  PASS 3 claims analysed with sockets blocked in a child process; verdicts identical=True; a forced model call ret...
A24  PASS 7 traps (contradiction / kept object list / reversed causation / adjacent product / adjacent outcome / quan...
A25  PASS 5 scope probes (5 narrowed claims refused, 3 matched-population controls decided); front-end parity on all ...
A26  PASS 40 affirmative golden claims inverted and flipped; 11 double-negated claims refused; identity negator rejec...
A27  PASS 3 probes: every citation names shared vocabulary; rendered 'Matched on' in the page; front-end parity; 0 vi...
A28  PASS 5 probes: closest card named with the guard that stopped it (4 with a near-miss, 1 with none); front-end pa...
A29  PASS 6 probes (2 dose mismatches and 1 relation mismatch refused, 3 controls decided); front-end parity; 0 viola...
A2   PASS 15 verdicts checked, 0 with missing citation
A30  PASS 5 submissions: 3 contradictions labelled with their basis, 2 controls left unlabelled; front-end parity; 0 ...
A31  PASS 4 probes: a thousands separator stays in the number, an object word does not create a relation match, a pro...
A32  PASS 39 held-out probes (disjoint from the golden set), 7 controls that still decide; every verdict, atom count,...
A33  PASS 5 probes: a two-step chain is derived and labelled, an agreeing third atom is not called a conflict, a pair...
A34  PASS 97/112 cards carry an archived paragraph: 97 verified, 13 unresolved, 1 page_changed, 1 source_changed; exc...
A35  PASS 5 external dev datasets recomputed from the frozen slice; accuracy and refusal match the published run with...
A36  PASS risk/cure classified and kept apart, risk/prevention kept together, harm/harm still decided; susceptibility...
A37  PASS the acceptance run carries a receipt (66c9fe84feb621c75d6932681b5cdb8f) that binds 46 artefacts by SHA-256,...
A38  PASS the built page ran in edge; the court docket plus 10 corpus demos and 3 citation demos were clicked, each r...
A39  PASS the external table carries a receipt (f618f0cb0d2ddb7191378509675325c2): two runs with exit codes and outpu...
A3   PASS comma input -> 3 atoms; enumeration input -> 3 atoms; compound subject -> 1 atom(s), first noun kept=True
A40  PASS 4 recorded session(s), 1 of them replayable against the current kernel and corpus, 0 by an external operato...
A41  PASS 1 wrong dev decision(s), 1 reviewed entry/entries covering exactly the wrong set; categories contradictory_...
A42  PASS 12 texts compared between the page and the kernel (verdict, scope, plan); a 12-row batch matches the single...
A43  PASS serve.py started on an ephemeral port with the local model disabled and no key: /api/health reports its gat...
A44  PASS 12 citation fixtures, every atom receives supported/refuted/not_in_source, the totals sum to the atom count...
A45  PASS 33 court fixtures (12 verdicts, 13 arguments, 5 anchor bridges, 3 inputs), every atom has a finding, accept...
A46  PASS a valid AI quotation is accepted, a forged quotation is struck as quote_not_found, an unknown evidence id i...
A47  PASS 6 batch fixtures: duplicate sources collapse by SHA-256, one claim can be audited against eight sources, a ...
A48  PASS 8 cases are genuine rule losses (rules return not_in_source); fixed reference anchors make the same judge v...
A4   PASS steps=['decompose', 'negation', 'retrieve', 'semantic', 'adjudicate', 'negation', 'retrieve', 'semantic', '...
A5   PASS index.html present and self-contained=True
A6   PASS DEMO-3 all refused=True
A7   PASS two offline runs field-for-field identical=True
A8   PASS real key patterns found=0
A9   PASS README states limitations and non-authoritative scope=True
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

| File | Bytes | SHA256 (first 16) |
| .dockerignore | 77 | db1f318ffb3c55dd |
| .gitattributes | 170 | 74ed165b86ef4389 |
| .gitignore | 71 | 6d7883021efeaced |
| ARCHITECTURE.md | 103509 | 2752818d4196eb74 |
| COMPETITION_SCORECARD_CN.md | 10817 | 921c78f403ddc4b4 |
| core/__init__.py | 89 | 0797e0173f8c3939 |
| core/adjudicate.py | 9515 | e826227a3cc5b240 |
| core/audit.py | 134578 | c05c77edd8660903 |
| core/citation.py | 10774 | 77be1c2b7ea0bf1b |
| core/consistency.py | 9645 | 344da114011f9500 |
| core/court.py | 28185 | 9e47519be52b746d |
| core/court_batch.py | 10293 | 975d783fad82b473 |
| core/court_live.py | 6751 | dec2cccb516a9864 |
| core/decompose.py | 10156 | 5d179890a87cf2e3 |
| core/evidence.py | 29436 | 807bf0c1444fa1dc |
| core/language.py | 3157 | 816391571b4824c3 |
| core/llm.py | 29111 | 56a8711f572a7399 |
| core/negation.py | 2346 | bdcd2edf1d45810c |
| core/pipeline.py | 13156 | 78ec484310f2446e |
| core/plan.py | 4982 | a5f86ab679f069ac |
| core/prompt.py | 2516 | e8ed40f6b22a9fca |
| core/recall.py | 4462 | 6d472e1ceb9ea2f6 |
| core/semantic.py | 1978 | 17740087a6d79afe |
| core/snapshots.py | 7231 | b94853a2b09b06ec |
| data/_claims_backup.json | 68868 | f25bc0be0c109866 |
| data/ai_recall_replay.json | 25623 | be778affb638e4ca |
| data/ai_uplift_cases.json | 2831 | 748c0315bc10add4 |
| data/citation_cases.json | 2873 | f2fb5b9b60258bb6 |
| data/claims.json | 75184 | 0c96925411fed34a |
| data/court_batch_cases.json | 3663 | f505f7a070ba7c35 |
| data/court_batch_replay.json | 19187 | cccd8429a1562466 |
| data/court_cases.json | 14731 | 903fbf3a58565299 |
| data/court_replay.json | 31216 | 49032301a7352641 |
| data/error_review.json | 4011 | fcc8cc087312df84 |
| data/external/cards_evidence_review.json | 4504 | 0edf5ad950d0d3ba |
| data/external/pages/.gitignore | 78 | 780664a5ab2d78cd |
| data/external/pages/0283b9f79e5e3a97.html | 20488 | 62c235f937a23f0b |
| data/external/pages/0575eb8a7ba8989f.html | 145440 | a13733825106d1e0 |
| data/external/pages/0a5f9ca57bd3b31f.html | 288531 | 5e7b2dc9327cd3dd |
| data/external/pages/21a96505c92d8027.html | 304381 | bbfd0ad9ca6efb0f |
| data/external/pages/2d24a53da0db8ad0.html | 64499 | be5037197ad6b019 |
| data/external/pages/2e5fb500819c3523.html | 62561 | 2fbdfa0e8535c9e8 |
| data/external/pages/3a556ae0866278eb.html | 59071 | 2b6f282615cc4207 |
| data/external/pages/3b144ad160a97226.html | 113292 | 42712af44040e20b |
| data/external/pages/450fd8c9b7049844.html | 487731 | c814dc80b8bd4d9f |
| data/external/pages/4e18ed093affa0ab.html | 58252 | 87044bd15f1be7a1 |
| data/external/pages/4e3b84d0bdd978bd.html | 373530 | c7060f92a82bf044 |
| data/external/pages/537289d65f98ac7b.html | 52507 | ed4fff5a02b59851 |
| data/external/pages/552ec8819479e0ca.html | 136489 | bdbccb513a6c842e |
| data/external/pages/60b007e3dc16da33.html | 46672 | d4e6ba5e722d40db |
| data/external/pages/6435cde393af3bb7.html | 60706 | e4661901a6192033 |
| data/external/pages/6df649adff80ca67.html | 34797 | e482993aa4208093 |
| data/external/pages/781d02e67e9dac35.html | 183450 | 73762aed19104557 |
| data/external/pages/7b6022e6541b52e6.html | 91139 | 1d4d0c51671636e4 |
| data/external/pages/7d90636550eaddd5.html | 67907 | fa596bd228dcba15 |
| data/external/pages/8d9b2dac8fba0518.html | 53749 | cfbcc7a8b36cf9af |
| data/external/pages/9578be24123e8ed3.html | 64825 | e523c0532da5093c |
| data/external/pages/9994b0d40576fd4f.html | 88308 | 1d7e08b85da2cc98 |
| data/external/pages/a0f0a3c0f92deb94.html | 159018 | e116587301120df0 |
| data/external/pages/a3c4eae74bf135c4.html | 58423 | 8c4f894ad0103826 |
| data/external/pages/aa21df5ea57e1a30.html | 124601 | aaa38d6ecc6d4f33 |
| data/external/pages/b0c4995da17b9f8d.html | 60499 | ba03c38fdb39296e |
| data/external/pages/b15be5f785171eeb.html | 96718 | 4e6cf40beb7f463c |
| data/external/pages/b2b1d483f118a3e8.html | 58241 | f8e6b2c711c5b8ad |
| data/external/pages/b5f59eefdcdedc14.html | 45254 | 24e39104de93f137 |
| data/external/pages/b74b256cd0f0200d.html | 53440 | ba0e04f736715b61 |
| data/external/pages/b95595a719874220.html | 55487 | ac6f5f94f1bebd4d |
| data/external/pages/bca0460d29dbe271.html | 52806 | deaffd2da8553aaf |
| data/external/pages/c1eb2b7cf105c47d.html | 59650 | 0604b8bc52455a48 |
| data/external/pages/c53686a1fca4e288.html | 50753 | a24fbab3fdce84f8 |
| data/external/pages/d56015e847f173f4.html | 489947 | 73d371936618be5a |
| data/external/pages/df0d71c93f773b5a.html | 64596 | 98d5d1a7f3adc611 |
| data/external/pages/e979225fc93f357e.html | 53449 | 5665f220bc9074c6 |
| data/external/pages/ea0acfa9c1430b20.html | 27814 | 39e3ee3874586c11 |
| data/external/pages/ea68bf66cd2b5e99.html | 282505 | bdea3f6d505f2431 |
| data/external/pages/ef7f17eef654b29c.html | 527710 | ef19d3eeb9a4190c |
| data/external/pages/fcd3a2a989fb60fe.html | 29947 | 283107346225b09c |
| data/external/pages/pages_index.json | 26041 | 303cd0331ce9c2a4 |
| data/external/README.md | 1381 | a12d926bc51f5d52 |
| data/external/samples/averitec.jsonl | 250867 | f15c13f487ab869b |
| data/external/samples/fever.jsonl | 111030 | 26cf2fcd5f8f7e23 |
| data/external/samples/healthver.jsonl | 211414 | 0cb693a846ce94db |
| data/external/samples/pubhealth.jsonl | 897612 | b92d60453c352bdf |
| data/external/samples/sample_manifest.json | 6161 | e07e1337ad3d28f6 |
| data/external/samples/samples_index.json | 2173 | f3bdd43095bf66e1 |
| data/external/samples/vitaminc.jsonl | 119846 | b56940a16a60a2e0 |
| data/external/samples2/averitec.jsonl | 27287 | de939147480a78a9 |
| data/external/samples2/fever.jsonl | 33851 | 3100b986224a4691 |
| data/external/samples2/freeze.json | 1497 | 9e9f51c09286fc4a |
| data/external/samples2/healthver.jsonl | 25398 | 277958631a5e18e1 |
| data/external/samples2/pubhealth.jsonl | 26227 | 1d7192412e7145f1 |
| data/external/samples2/samples_index.json | 1543 | b9beec5840691c2b |
| data/external/samples2/vitaminc.jsonl | 28656 | f7988cc0c806abdb |
| data/external/SOURCES.md | 7683 | cf4385dea1fd5e62 |
| data/external/synthetic/claim_b1.attestation.json | 1144 | fb2192fc5d8af0cd |
| data/external/synthetic/claim_b1.jsonl | 157322 | fb1587827a7ab7e4 |
| data/external/synthetic/claim_b2.jsonl | 156560 | 9b227d375828aa80 |
| data/external/synthetic/synth_checks.json | 2120 | 3754da6bfd3c58b4 |
| data/golden_set.json | 20395 | babc18d96641ac99 |
| data/guard_set.json | 13994 | e1f87a536476bd5c |
| data/paraphrase_deep.json | 3077 | e82c385526d219d3 |
| DATA_PLAN.md | 23831 | 38bb51e3baed1104 |
| Dockerfile | 294 | 6da19eeaf6e7c68f |
| evidence/_cards_evidence_backup.jsonl | 98792 | 19cbc8e885f9e17e |
| evidence/acceptance_final.json | 14740 | 3c3a9150a8a40122 |
| evidence/ai_lift.json | 12123 | 6c3d3d77a0ac80d3 |
| evidence/ai_uplift.json | 14722 | 0107c24d1c6eb0ac |
| evidence/cards_evidence.jsonl | 110368 | e48986cd0aabaa48 |
| evidence/corpus_v10_expansion.json | 4508 | 51936372d3653713 |
| evidence/court_live.json | 177238 | 2c0e6d63c2920e61 |
| evidence/coverage_headroom.json | 10510 | e3a03eaa486f2396 |
| evidence/DATA_STATUS.md | 28296 | 39200846e0129189 |
| evidence/eval_receipt.json | 6465 | dcae4e0fce30f921 |
| evidence/external_dev_detail.json | 308648 | b6fff9d8545acd73 |
| evidence/external_eval_holdback.json | 7909 | 3e28d0465a407849 |
| evidence/external_eval_v2.json | 7902 | ad0d19c189557c15 |
| evidence/external_eval_v3.json | 7904 | 6401a3a1e1b8ca2f |
| evidence/external_eval_v4.json | 8805 | 95650f8382c2cd3f |
| evidence/holdback_ledger.json | 980 | 8ac57eef6d1a3558 |
| evidence/label_conflicts.json | 53977 | 9c776ba54d443594 |
| evidence/link_check.json | 12476 | 1d05cf321aa418f1 |
| evidence/oracle_eval.json | 48940 | a297b4780629f86c |
| evidence/paragraphs.jsonl | 2000248 | 0ce605a42abeef50 |
| evidence/retractions.jsonl | 13631 | a6e72415f240b003 |
| evidence/run_receipt.json | 5573 | c819bfbe0a5b2568 |
| evidence/screenshots/01-ai-contrast.png | 99016 | d1e1543f70d8a7db |
| evidence/screenshots/02-result-demo1.png | 84045 | 8a21d5e6be8c8b0a |
| evidence/screenshots/03-conflict-demo4.png | 110226 | 970e22dc872279fa |
| evidence/screenshots/04-refusal-demo3.png | 140129 | 6e60050ab2b741d0 |
| evidence/screenshots/05-audit-demo6.png | 133306 | 5238ba5afc9241f5 |
| evidence/screenshots/06-coverage-demo7.png | 124881 | af9c34a71d585a1f |
| evidence/screenshots/07-corpus-browser.png | 52764 | 3acd137f172e54fb |
| evidence/screenshots/08-scope-refusal.png | 92625 | 72f21891c6ee8603 |
| evidence/screenshots/09-contradictory-atoms.png | 91187 | 45f7920a4488ab08 |
| evidence/screenshots/10-chain-conflict.png | 221045 | 0dd4917c5f2c38e0 |
| evidence/screenshots/11-snapshot-evidence.png | 53718 | b7387250ca658050 |
| evidence/screenshots/12-archived-corpus.png | 54239 | ac918c235dc279aa |
| evidence/screenshots/13-topic-guard.png | 112554 | 6d11c218d96ac307 |
| evidence/screenshots/14-endpoint-guard.png | 111982 | 9b7c7e6ac3c55f5a |
| evidence/screenshots/15-batch-table.png | 43344 | bf0986986ac0fe4a |
| evidence/screenshots/16-refusal-plan.png | 95273 | 9aa1371343bca490 |
| evidence/screenshots/17-citation-refuted.png | 26594 | 964215b9d72270ed |
| evidence/screenshots/18-citation-supported.png | 22915 | 37f2ab6b4f3265be |
| evidence/screenshots/19-citation-not-in-source.png | 27418 | f2da547697940583 |
| evidence/screenshots/20-court-landing.png | 183841 | 9ad926149d7f1a74 |
| evidence/screenshots/21-court-struck.png | 123960 | 112ab2e214e11394 |
| evidence/screenshots/22-court-live.png | 125227 | 0eb119205c20662e |
| evidence/screenshots/23-court-static-ai.png | 169253 | fae48c17e1c66b21 |
| evidence/screenshots/24-court-struck.png | 175795 | 164d059958c335cc |
| evidence/screenshots/25-court-live.png | 228352 | 9bfc4ca4c6080b19 |
| evidence/screenshots/26-court-batch.png | 173621 | 42ba50428bc3f490 |
| evidence/sessions/2026-11-20T15-50-06Z_self.json | 3939 | 57b12a5b06d7dffc |
| evidence/sessions/2026-11-20T16-19-40Z_self.json | 2709 | 79f399e71fe8294e |
| evidence/sessions/2026-11-20T17-10-45Z_self.json | 2745 | 7686013e556d3461 |
| evidence/sessions/2026-11-20T18-01-06Z_self.json | 2666 | 52cbe74b2168b086 |
| evidence/video_script.md | 3466 | 6efe612e419e08a9 |
| evidence/withdrawn_demo.json | 841 | 2bb1905ebd3c5efe |
| LICENSE | 1068 | 6937896c92006fb4 |
| PRODUCT.md | 10869 | 4417f5b8d4cc6d9e |
| README.md | 14225 | b501273d8b9bf53b |
| REFACTOR_PLAN_CN.md | 30394 | 85736141e8683262 |
| serve.pid | 7 | 40ab831b408ac316 |
| serve.py | 16140 | 6d05a817e95fc6ad |
| SUBMISSION.md | 15471 | 3a0950a3e2885b08 |
| tools/add_cards_v10.py | 8614 | f1651481a62f3042 |
| tools/add_cards_v8.py | 4172 | 0317ab6013bb1a2e |
| tools/add_cards_v9.py | 11288 | fcad815f25a29e2f |
| tools/add_demo_v14.py | 764 | 3c604d6647946781 |
| tools/add_golden_v14.py | 2837 | 55157ab7102e4abd |
| tools/add_golden_v9.py | 3619 | b2d31ed68fc7b1af |
| tools/add_guard_outcome.py | 2149 | 92d4dc0e0177b591 |
| tools/browser_check.py | 11599 | 475b0dbe78d77778 |
| tools/browser_check_live.py | 4013 | 3b23f85f8112c217 |
| tools/build_court_batch_replay.py | 2100 | f7b1b16cfb164648 |
| tools/build_court_replay.py | 2555 | 1732ab76345aac15 |
| tools/build_frontend.py | 4364 | 573fa112f35175de |
| tools/check_label_noise.py | 4942 | b5ab4dedd2fd3407 |
| tools/check_links.py | 5933 | a5c45afdd7289d92 |
| tools/check_manifest.py | 5327 | b357c860892cd8d2 |
| tools/check_retractions.py | 951 | 969ba0c19989814c |
| tools/coverage_headroom.py | 5641 | 93d09d44991f6c61 |
| tools/eval_external.py | 8580 | 413c68859997fe55 |
| tools/eval_external_detail.py | 3405 | 7968cac7ae63f349 |
| tools/eval_oracle.py | 7306 | cc83531c6977eaa8 |
| tools/export_ai_replay.py | 5606 | d7dce7d7dc4aaf34 |
| tools/fetch_benchmarks.py | 904 | 90024c33aa2d58cc |
| tools/fetch_snapshots.py | 859 | e87471623d5aa639 |
| tools/get_model.py | 2853 | c3557e2d1210226d |
| tools/js_ui_verify.js | 12050 | a8016609ce40ae5b |
| tools/js_verify.js | 746 | 00299515b9b52d2e |
| tools/make_court_screenshots.py | 4585 | ac9278587b1d0b6f |
| tools/make_eval_receipt.py | 7155 | bcd65a406683a167 |
| tools/make_guard_set.py | 10415 | 337bc9cf64e78664 |
| tools/make_holdout2.py | 9306 | aac8c04a4e26aa5f |
| tools/make_receipt.py | 6941 | a580903415ec4c9b |
| tools/make_screenshots.py | 6151 | 0350159f7690d265 |
| tools/measure_ai_lift.py | 4576 | 4b382e6305d4ade3 |
| tools/restate_vitd_card.py | 1435 | e50c9a8fd1964586 |
| tools/run_ai_uplift.py | 5757 | 34aa05944a79bc26 |
| tools/run_external_session.py | 7978 | 4f4732733c5916be |
| tools/session_log.py | 7126 | 3777266450b4e149 |
| tools/sync_frontend.py | 1878 | d35474348af483d5 |
| tools/verify_sessions.py | 7103 | a2113afdd6d036a8 |
| USER_TODO.md | 7797 | 4edb27b51c6e0a13 |
| web/app.js | 81124 | 3c3ba3cca8bb95ff |
| web/court.js | 38750 | 7847a042d9228b3d |
| web/court_batch_replay.js | 12351 | 7518b86559b14af3 |
| web/court_replay.js | 31239 | 989e2c890efc8ea8 |
| web/index.html | 226022 | 37f99f9a0f9219d4 |
