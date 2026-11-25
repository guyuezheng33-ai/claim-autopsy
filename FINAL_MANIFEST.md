# Final manifest — what "final" means, and how to prove it later

Freeze point: **2026-11-22** (project root `claim-autopsy/`). This file records the exact byte state
that passed the acceptance suite, so a later change is detectable instead of being a matter of memory.

**Gate result at this freeze point** (generated from `evidence/acceptance_final.json`, never typed by
hand, so the summary below cannot drift from the run it describes):

```
total=48  passed=48  all_pass=True  run_tag=final  llm_mode="Local Qwen2.5-3B found, server not running"
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
A37  PASS the acceptance run carries a receipt (37308f4add2a09709a2e5fef8aa12e04) that binds 66 artefacts by SHA-256,...
A38  PASS the built page ran in edge; the court docket plus 10 corpus demos and 3 citation demos were clicked, each r...
A39  PASS the external table carries a receipt (8d381b4a0b0627cd90bac5257c27f869): two runs with exit codes and outpu...
A3   PASS comma input -> 3 atoms; enumeration input -> 3 atoms; compound subject -> 1 atom(s), first noun kept=True
A40  PASS 6 recorded session(s), 1 of them replayable against the current kernel and corpus, 0 by an external operato...
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
the public repository URL, the hosted demo URL, the public YouTube/Vimeo URL for the already-encoded
`evidence/demo_60s.mp4`, and the Devpost form. `USER_TODO.md` holds those steps in order. `LICENSE` carries the placeholder holder
"Claim Autopsy authors" — change it to your legal name before publishing if you prefer.

`evidence/history/` is deliberately excluded from the table below: it holds superseded
run credentials kept for traceability, not part of the deliverable. This manifest is the only
project file not listed in its own table — it cannot hash itself.

| File | Bytes | SHA256 (first 16) |
| .dockerignore | 463 | 82c87b1792faebf9 |
| .gitattributes | 246 | d786b12647e3d229 |
| .gitignore | 127 | 63be6eda6b057a24 |
| ARCHITECTURE.md | 103494 | 58c799af1bb644ec |
| COMPETITION_SCORECARD_CN.md | 13341 | 5d53e9bac74c4cd9 |
| DATA_DICTIONARY.md | 4036 | cfdff5cf201053cb |
| DATA_PLAN.md | 23831 | 38bb51e3baed1104 |
| Dockerfile | 307 | 1d774a1f5f6ab839 |
| JUDGE_PATH.md | 4535 | 9ebd52fb825e7c9f |
| LICENSE | 1089 | 193fa3fab2956aa6 |
| PRODUCT.md | 11213 | 97df89ab4a6a17d3 |
| README.md | 18409 | 11d523c4f539ff57 |
| REFACTOR_PLAN_CN.md | 30989 | a34e55143e1fb0eb |
| SUBMISSION.md | 19559 | 845bc2da171d2a21 |
| USER_TODO.md | 12967 | 4cfe4739060d8241 |
| core/__init__.py | 89 | 0797e0173f8c3939 |
| core/adjudicate.py | 9736 | 910e59c341d71ed5 |
| core/audit.py | 134593 | 815bcec5e5fd2998 |
| core/citation.py | 11046 | ee5e5a3799a20ea4 |
| core/consistency.py | 9906 | dbfaed8293f581ab |
| core/court.py | 29458 | 05eb1ba08455e562 |
| core/court_batch.py | 10541 | 9a5a8f6c725c8969 |
| core/court_live.py | 6906 | d4f5647f3c9c93ec |
| core/decompose.py | 10398 | 6888d52d70ebbc92 |
| core/evidence.py | 30129 | 8897247eb4dcb7db |
| core/language.py | 3157 | 816391571b4824c3 |
| core/llm.py | 29808 | 6400423009474b4b |
| core/negation.py | 2409 | 66d32f992a548b0a |
| core/pipeline.py | 13156 | 78ec484310f2446e |
| core/plan.py | 5110 | 7db27f2658214384 |
| core/prompt.py | 2581 | c18b3375df8e464a |
| core/recall.py | 4572 | 919a1369cfb32bc7 |
| core/semantic.py | 2027 | 320fe9fa0f4af8b3 |
| core/snapshots.py | 7467 | 10ebb6756a44d41d |
| data/_claims_backup.json | 68868 | f25bc0be0c109866 |
| data/ai_recall_replay.json | 25703 | 40d5d8f86916a105 |
| data/ai_uplift_cases.json | 2900 | 7d59df1cfd79677f |
| data/citation_cases.json | 2953 | fb4d7913d0fa6123 |
| data/claims.json | 75184 | 0c96925411fed34a |
| data/court_batch_cases.json | 3748 | bc1606cd9085a2fc |
| data/court_batch_replay.json | 19187 | cccd8429a1562466 |
| data/court_cases.json | 14731 | 903fbf3a58565299 |
| data/court_replay.json | 31216 | 49032301a7352641 |
| data/error_review.json | 4065 | c8911f33b4db1202 |
| data/external/README.md | 1409 | da74d3616e714f5c |
| data/external/SOURCES.md | 7683 | cf4385dea1fd5e62 |
| data/external/cards_evidence_review.json | 4504 | 0edf5ad950d0d3ba |
| data/external/pages/.gitignore | 78 | 780664a5ab2d78cd |
| data/external/pages/pages_index.json | 26660 | fff99d4a089da23d |
| data/external/samples/averitec.jsonl | 250867 | f15c13f487ab869b |
| data/external/samples/fever.jsonl | 111030 | 26cf2fcd5f8f7e23 |
| data/external/samples/healthver.jsonl | 211414 | 0cb693a846ce94db |
| data/external/samples/pubhealth.jsonl | 897612 | b92d60453c352bdf |
| data/external/samples/sample_manifest.json | 6161 | e07e1337ad3d28f6 |
| data/external/samples/samples_index.json | 2247 | c32077dba578ef2a |
| data/external/samples/vitaminc.jsonl | 119846 | b56940a16a60a2e0 |
| data/external/samples2/averitec.jsonl | 27287 | de939147480a78a9 |
| data/external/samples2/fever.jsonl | 33851 | 3100b986224a4691 |
| data/external/samples2/freeze.json | 1497 | 9e9f51c09286fc4a |
| data/external/samples2/healthver.jsonl | 25398 | 277958631a5e18e1 |
| data/external/samples2/pubhealth.jsonl | 26227 | 1d7192412e7145f1 |
| data/external/samples2/samples_index.json | 1543 | b9beec5840691c2b |
| data/external/samples2/vitaminc.jsonl | 28656 | f7988cc0c806abdb |
| data/external/synthetic/claim_b1.attestation.json | 1144 | fb2192fc5d8af0cd |
| data/external/synthetic/claim_b1.jsonl | 157721 | 665684584706cd2d |
| data/external/synthetic/claim_b2.jsonl | 156959 | 760767bfca11e8d8 |
| data/external/synthetic/synth_checks.json | 2120 | 3754da6bfd3c58b4 |
| data/golden_set.json | 20395 | babc18d96641ac99 |
| data/guard_set.json | 13994 | e1f87a536476bd5c |
| data/paraphrase_deep.json | 3101 | c3b310a1add2b0ac |
| deploy/cloudrun/Dockerfile | 1555 | b1cb5b6bae48b39e |
| deploy/cloudrun/start.sh | 1331 | c986893e5d0fa2d2 |
| deploy/hf-space/.gitattributes | 168 | 4a37c7eeeb2f076f |
| deploy/hf-space/Dockerfile | 1391 | 90dabfb056fd2613 |
| deploy/hf-space/README.md | 946 | c0fd14b241e158ee |
| deploy/hf-space/start.sh | 1332 | a92615146085da06 |
| eval/bench_court.csv | 86 | d58961d98a4121c2 |
| evidence/DATA_STATUS.md | 28296 | 39200846e0129189 |
| evidence/_cards_evidence_backup.jsonl | 98892 | e19d83bf947e708a |
| evidence/acceptance_final.json | 15509 | bee5510a50264b9d |
| evidence/ai_lift.json | 12123 | 6c3d3d77a0ac80d3 |
| evidence/ai_uplift.json | 14508 | b153e186bf354249 |
| evidence/cards_evidence.jsonl | 110368 | e48986cd0aabaa48 |
| evidence/corpus_v10_expansion.json | 4508 | 51936372d3653713 |
| evidence/court_live.json | 177238 | 2c0e6d63c2920e61 |
| evidence/coverage_headroom.json | 10510 | e3a03eaa486f2396 |
| evidence/demo_60s.mp4 | 1488985 | a3e18beffe4d29b7 |
| evidence/eval_receipt.json | 6465 | 93c884d324acf739 |
| evidence/external_dev_detail.json | 308648 | b6fff9d8545acd73 |
| evidence/external_eval_holdback.json | 7909 | 3e28d0465a407849 |
| evidence/external_eval_v2.json | 7902 | ad0d19c189557c15 |
| evidence/external_eval_v3.json | 7904 | 6401a3a1e1b8ca2f |
| evidence/external_eval_v4.json | 8805 | 6c20141135970da2 |
| evidence/holdback_ledger.json | 998 | b183e15b298a151d |
| evidence/hosted_live.json | 2905 | 37dee0cdfdb28622 |
| evidence/label_conflicts.json | 53977 | 9c776ba54d443594 |
| evidence/link_check.json | 12476 | 1d05cf321aa418f1 |
| evidence/oracle_eval.json | 48940 | a297b4780629f86c |
| evidence/paragraphs.jsonl | 2002060 | 084ada8b29201374 |
| evidence/retractions.jsonl | 13672 | ddacb0349a16890d |
| evidence/run_receipt.json | 7702 | 29f425846cf21ec3 |
| evidence/screenshots/01-ai-contrast.png | 99016 | d1e1543f70d8a7db |
| evidence/screenshots/01-judge-path.png | 195194 | 08df4d656bc55cbb |
| evidence/screenshots/02-real-model-mistake.png | 89405 | f91cd662172b45f6 |
| evidence/screenshots/02-result-demo1.png | 84045 | 8a21d5e6be8c8b0a |
| evidence/screenshots/03-accepted-quote.png | 140467 | 4712e17859c0dcb2 |
| evidence/screenshots/03-conflict-demo4.png | 110226 | 970e22dc872279fa |
| evidence/screenshots/04-four-source-conflict.png | 99798 | 948310c3a101f1fe |
| evidence/screenshots/04-refusal-demo3.png | 140129 | 6e60050ab2b741d0 |
| evidence/screenshots/05-audit-demo6.png | 133306 | 5238ba5afc9241f5 |
| evidence/screenshots/05-receipt.png | 81846 | ace644d50c3fc0f1 |
| evidence/screenshots/06-coverage-demo7.png | 124881 | af9c34a71d585a1f |
| evidence/screenshots/06-supported.png | 86362 | 482102a19b142b07 |
| evidence/screenshots/07-corpus-browser.png | 52764 | 3acd137f172e54fb |
| evidence/screenshots/07-not-in-source.png | 72604 | 9b53a8a710eaa1bd |
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
| evidence/sessions/2026-11-21T15-58-15Z_self.json | 1693 | 4e3139c8a9a650a9 |
| evidence/sessions/2026-11-22T03-45-59Z_self.json | 2211 | 9cb7d0d22de59917 |
| evidence/video_script.md | 3919 | 3f2f73342a3b71a5 |
| evidence/withdrawn_demo.json | 869 | 3e14d67df6fc654d |
| pyproject.toml | 642 | 639be2c3a33078b4 |
| requirements.txt | 170 | 350463f5f1361c2c |
| scope.json | 834 | adf9f87b21d6cd92 |
| serve.py | 20380 | c80e9675af3820ef |
| soldieros/scope.json | 1619 | 730d6d60928880ee |
| tests/__init__.py | 0 | e3b0c44298fc1c14 |
| tests/test_core_invariants.py | 3816 | 5e00d6cc5053656d |
| tools/add_cards_v10.py | 8774 | bb79546d968c0a02 |
| tools/add_cards_v8.py | 4247 | 30f4e0a327206fb7 |
| tools/add_cards_v9.py | 11431 | b342d65377342ac1 |
| tools/add_demo_v14.py | 781 | 6e5ce1b522a67996 |
| tools/add_golden_v14.py | 2883 | 35ffdece910f3bc0 |
| tools/add_golden_v9.py | 3680 | a58cce034f7a3d3d |
| tools/add_guard_outcome.py | 2197 | d89169c299eb126c |
| tools/bench_court.py | 1933 | e34ce818ee0b0fe7 |
| tools/browser_check.py | 17046 | 74af46275051475c |
| tools/browser_check_live.py | 4112 | d11efc2dbb7618b0 |
| tools/build_court_batch_replay.py | 2154 | 7ba3a9f760ea0a28 |
| tools/build_court_replay.py | 2622 | 95415271c6c51eb3 |
| tools/build_frontend.py | 4479 | 7ea739687409a62d |
| tools/check_hosted_live.py | 6534 | 9e26fd6200f85e90 |
| tools/check_label_noise.py | 5069 | a28b138b2a2c381f |
| tools/check_links.py | 6084 | 66019380e615d19c |
| tools/check_manifest.py | 5914 | 16b065699d35381c |
| tools/check_retractions.py | 978 | 2e9a406f94a491ca |
| tools/coverage_headroom.py | 5772 | 254fb5f874dc02fa |
| tools/eval_external.py | 8752 | 09b6bf185fd7c714 |
| tools/eval_external_detail.py | 3486 | cca7c9e34b7eab91 |
| tools/eval_oracle.py | 7480 | 42acf464ff721553 |
| tools/export_ai_replay.py | 5735 | 7284260eecbaf2d5 |
| tools/fetch_benchmarks.py | 932 | bfeb532ccac460c4 |
| tools/fetch_snapshots.py | 886 | 3bec90e9154c4a51 |
| tools/get_model.py | 2934 | 3df1df2db93967c2 |
| tools/js_ui_verify.js | 12327 | 6b75ab192f279c82 |
| tools/js_verify.js | 746 | 00299515b9b52d2e |
| tools/make_court_screenshots.py | 4680 | 75d1b44b3bea874a |
| tools/make_eval_receipt.py | 7318 | c5018f2abc7fb775 |
| tools/make_guard_set.py | 10580 | 2829844a43877aa0 |
| tools/make_holdout2.py | 9517 | b2af8a7f53438e93 |
| tools/make_receipt.py | 7891 | a48856617213373e |
| tools/make_screenshots.py | 6267 | d9e7f77ff26e33ab |
| tools/measure_ai_lift.py | 4687 | 8eb35b0c73e7741b |
| tools/restate_vitd_card.py | 1465 | d76288481191203a |
| tools/run_ai_uplift.py | 5901 | 9ca2057d0bf8c3fb |
| tools/run_external_session.py | 8164 | b6e31ec2a6b4ed7d |
| tools/session_log.py | 7287 | 740af53575e8c6c0 |
| tools/stage_hf_space.py | 2799 | cbf12bbdd8dcb6aa |
| tools/sync_frontend.py | 1878 | d35474348af483d5 |
| tools/verify_sessions.py | 7275 | f20043e5a0f456a7 |
| web/app.js | 82235 | 01e2b434c1f9f9d3 |
| web/court.js | 49006 | 7eb324c9add0ff62 |
| web/court_batch_replay.js | 12351 | 7518b86559b14af3 |
| web/court_replay.js | 31239 | 989e2c890efc8ea8 |
| web/demo.html | 4767 | 3485f76e00426da8 |
| web/index.html | 235706 | e7df8c6cb9622bb7 |
