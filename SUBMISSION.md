# Claim Autopsy — Devpost submission copy

Paste-ready English copy for the Devpost fields. Numbers match the current repository; do not replace them with rounder numbers.

> **Judge shortcut:** open `https://guyuezheng33-ai.github.io/claim-autopsy/web/index.html`, paste any claim and source, then click **Open the trial**. This page calls a hosted Qwen2.5-3B live; `evidence/hosted_live.json` records an 18.9s black-box run. For a stable five-step read, open `.../index.html?judge=1` and click **Next →** five times. A 57.4s captioned screen recording is at `evidence/demo_60s.mp4`.

---

## 1. Project title

**Claim Autopsy — AI argues. Evidence decides.**

## 2. Elevator pitch

A citation court: AI prosecution and defence propose arguments, a deterministic judge checks every quotation, and any argument without an exact source quote is struck in front of you.

## 3. Who it is for and what problem it solves

Students, researchers and editors who write sentences like “the source says…” and cannot afford to check every quotation by hand. AI writing tools make this worse: a model can produce a confident sentence with a plausible but nonexistent citation. Existing fact-checkers give a label and a paragraph of explanation; they rarely show whether the supplied source actually contains the quoted proposition.

Claim Autopsy narrows the question to one a reader can verify:

> Does this source state this claim — support it, refute it, or never say it?

That question has a checkable answer. The product returns a per-atom finding, the exact sentence and character range, the arguments that were accepted or struck, and a citation receipt. It does not decide whether the source itself is right, and it does not pretend to check the open web.

**Why this is not another fact-checker:**

- It does not output a truth label. It outputs a receipt a reader can re-check: quote, character range, strike code, verdict.
- The model is allowed to lose. The visible product moment is a plausible AI argument being struck because the source does not contain it.
- The same quotation, the same judge, only the bridge changes: the 8-case uplift baseline is a controlled test of whether AI contributed anything, not a demo of a confident answer.

## 4. What it does

1. You paste a claim and the source you think supports it — or load a `.txt`/`.md` source, with a character count and a pre-run limit check.
2. The claim is split into independently checkable atoms.
3. The source is split into sentences with character offsets and hashes.
4. A local AI prosecutor and a local AI defence each propose arguments. Every argument must name an atom, an evidence id, a verbatim quotation and a relation.
5. A deterministic judge checks the quotation exists, then checks relation, subject, population, object, endpoint, quantity, strength and polarity. Any doubt means `struck`.
6. The judge issues one of `supported`, `refuted` or `not_in_source` for every atom. `not_in_source` is a finding, not a refusal: the nearest sentence and its coverage are shown.
7. You get a three-column trial and a dossier with a content-addressed run id. The dossier can be copied as JSON or downloaded as Markdown.
8. **Multi-source mode:** one claim against up to 8 candidate sources. Rules triage every source first; AI is spent only on sources the rules cannot settle. Duplicate sources collapse by SHA-256. If one source supports and another refutes, the page reports `cross-source conflict` and does not pick a winner.
9. **Semantic bridge:** when the source uses a true synonym, the model proposes anchor pairs such as `Aspirin → acetylsalicylic acid`. The judge rewrites the claim with those pairs and reruns every check. This is how the AI can change a verdict the rules lose, without letting it rewrite negation or direction.

The visible product moment is a struck argument: a quotation that looks right, does not appear in the source, and is rejected before it can influence the verdict.

## 5. Why the AI is meaningful (not decorative)

| Role | Who | What it does | What it may never do |
|---|---|---|---|
| Prosecution | Qwen2.5-3B-Instruct, local GGUF, llama.cpp CPU | Propose arguments that the source contradicts the claim, with a verbatim quote and optional semantic anchors | Write a verdict, invent a quote, invent evidence |
| Defence | Same model, separate call, parallel | Propose arguments that the source supports the claim | Same limits |
| Judge | `core/court.py`, deterministic Python | Verify every quotation and structural check; apply a grounded term bridge; accept or strike; issue the verdict | Delegate the verdict to the model |

Without the model, the product still runs a rules-only docket. It can still reach a verdict, but it cannot show two adversarial cases, cannot surface a plausible fabricated quotation, and cannot show what a model would have claimed. With the model, the central experience exists. The AI is not a wrapper around a classifier: it produces the arguments the judge cross-examines.

**The honest increment test:** `evidence/ai_uplift.json` holds 8 pairs where the rules docket returns `not_in_source`. With fixed reference anchors, the same judge verifies the same quotation in 8/8. The live local 3B run is recorded separately and is never substituted for the fixed-anchor proof: `summary.model_live=true`, `model_uplift=8`, `anchor_causal=8`, `without_anchors_still_not_in_source=8`, model `qwen2.5-3b-instruct-q4_k_m.gguf`; each case keeps its own latency, accepted/struck ledger and bridge. The control removes anchors from the model's own arguments and the verdict returns to `not_in_source`, so the change is caused by the bridge, not by a looser judge.

Method: one call per side, strict JSON, at most 3 arguments per atom per side, at most 8 atoms, 240-second timeout, parallel execution, no cloud dependency when the local model is installed. Unknown evidence ids, unknown atoms, bad JSON and invented quotes are discarded before the judge sees them. When the source uses a true synonym, the model may return `anchors`; the judge rewrites the claim with those terms and reruns every check. The live path also forces an anchor-only pass and asks one focused question per missing content phrase; a reversed pair is orientation-corrected but still verified. Anchors may not touch negation, relation verbs or numbers, and an ungrounded anchor is struck.

## 6. Representative input and output

Input:

```text
Claim:  Getting a flu vaccine gives you the flu.
Source: It is impossible to get influenza from the injected vaccine because the vaccine does not contain live virus.
```

Output from a recorded local run (`evidence/court_live.json`, model `qwen2.5-1.5b-instruct-q4_k_m.gguf`):

```json
{
  "verdict": "refuted",
  "ai_mode": "ai",
  "summary": {"refuted": 1, "accepted_arguments": 1, "struck_arguments": 1},
  "arguments": [
    {
      "side": "prosecution",
      "relation": "contradicts",
      "status": "accepted",
      "quote": "It is impossible to get influenza from the injected vaccine because the vaccine does not contain live virus.",
      "char_start": 0,
      "char_end": 108
    },
    {
      "side": "defense",
      "relation": "contradicts",
      "status": "struck",
      "strike_codes": ["side_mismatch"],
      "strike_reason": "quotation points the other way"
    }
  ]
}
```

The defence used the same sentence on the wrong side. The judge struck it; the verdict stayed the judge's. `evidence/court_live.json` now stores both local models under `runs` (1.5B and 3B); this example is the 1.5B recording used by the static page, not a claim that 1.5B and 3B behave identically.

A second real case: `The Eiffel Tower is located in Paris.` against `The Eiffel Tower is located in Paris, France.` produces `supported`, with one accepted defence quotation and one struck prosecution argument. Six recorded live cases are in `evidence/court_live.json`: 2 accepted and 2 struck arguments; the deterministic verdict matched the expected fixture in 6/6 cases.

## 7. How it was built

- **Backend:** Python 3.13 standard library. `core/court.py` is the judge and dossier builder. `core/llm.py` owns the model provider, local server lifecycle and strict advocate protocol. `serve.py` is a stdlib HTTP server with nine endpoints; `/api/trial_stream` returns ordered NDJSON phase events (rules → evidence → AI advocates, with heartbeats → judge) so a slow CPU run is observable rather than a blank wait.
- **Local AI:** `llama.cpp` `llama-server` with `Qwen/Qwen2.5-3B-Instruct-GGUF` Q4_K_M, 2.0 GB, CPU-only `-ngl 0`, loopback port 8099. No API key and no outbound request are needed. A 1.5B fast profile and a 7B profile are configured; 3B is the measured default.
- **Front end:** static HTML, CSS and vanilla JS. `web/court.js` renders the dossier and consumes the live phase stream. `web/court_replay.js` holds recorded dossiers. On GitHub Pages the page calls the hosted Qwen2.5-3B endpoint; on localhost it calls same-origin `serve.py`; a `file://` copy stays in labelled recorded mode. The live panel shows four real phases, elapsed time and the final accepted/struck/bridge count.
- **Data:** 33 court fixtures (12 verdict + 13 argument + 5 anchor + 3 input), 6 batch fixtures, 12 citation fixtures, 112 evidence cards from 41 authoritative sources for the legacy corpus audit.
- **Testing:** 48 acceptance gates (not 48 unit tests), 10 pytest unit tests, SHA-256 run receipts binding every code/data/UI artefact, a real Edge browser check of single-source and batch court modes, 33/33 court fixtures and 6/6 batch fixtures, and an 8-case rules-lose / live-3B / anchor-causal baseline.

## 8. Testing, failure cases and limits

1. **Fabricated quotation.** The adversarial fixture invents “The flu vaccine contains live virus and causes influenza.” The judge strikes it with `quote_not_found`; it never enters the verdict. Gate A46 enforces the same path.
2. **Vulkan backend produced garbage.** Qwen emitted repeated garbled tokens (`GGGG…` / `UmbGGGG…`) instead of JSON when layer 0 went to Vulkan. The fix is `-ngl 0` on CPU; `serve.py` sets it. This is a real environment bug, not a hypothetical.
3. **A 3B model is not a reliable opponent.** It sometimes labels its relation incorrectly, returns an empty list on an unrelated source, or proposes only one anchor in the full argument schema. The judge catches these; that is the product working. Forced anchor completion raises the fixed 8-case live set to 8/8 (`evidence/ai_uplift.json`, `model_live=true`), but that is not a guarantee of open-domain recall or eloquence.
4. **No key and no model means rules-only.** The page says `RULES-ONLY DOCKET`; it does not fake AI. The public GitHub Pages page calls the hosted 3B endpoint; a `file://` copy has no API and shows `RECORDED LIVE AI RUN`, never `LIVE`.
5. **One source, English-first.** Heavy paraphrase or a source in another language can return `not_in_source`. This is a finding about the supplied source, not a claim that the statement is false.
6. **Not an authoritative fact-check.** The judge checks whether the source states the claim, not whether the source is correct.

Testing commands:

```bash
python -m core.court --fixtures      # 33/33
python -m core.audit final           # 48 gates
python tools/run_ai_uplift.py --live # 3B live baseline (requires llama-server on 8099)
python tools/browser_check.py        # Edge, court + legacy modes
python tools/browser_check_live.py   # Edge, live progress over /api/trial_stream
python tools/make_receipt.py final --bootstrap
python tools/make_receipt.py final
```

## 9. Challenges

- **Separating argument from judgment.** The first temptation is to let the model produce a verdict. That makes the product indistinguishable from a chatbot and removes the only thing a skeptical reader can verify. The judge had to own every decision, and the AI had to be reduced to a witness whose claims can be struck.
- **Making the judge fair without making it lenient.** The synonym floor for `cure` / `treat` was initially too broad and let `green` / `blue` through. It is now predicate-scoped: synonyms may pass only when every structural check passes and the predicates are in the same class. The 33 fixtures pin both directions.
- **Running AI without a key.** The environment had no API key. A local model was found, but the Vulkan path produced garbage. Pure CPU fixed it. This is why the demo can show live AI without an external account.
- **Honest recorded vs live.** The public page has two surfaces: a hosted live form that calls Qwen2.5-3B on any pasted citation, and a five-step rail that replays a labelled real run. A `file://` copy never claims live. The badge is driven by `/api/status` and the receipt model name, not by page copy.

## 10. Accomplishments

- The judge is genuinely independent: a model that says `supported` cannot make the verdict `supported` unless the quotation passes every check.
- The product has a zero-model fallback that is still useful and still honest.
- A real local model runs the main path on CPU, with no key and no network.
- The public page can call a hosted 3B live on arbitrary text; the five-step rail stays a labelled recording. A `file://` copy is recorded and says so.
- 33/33 court fixtures, 6/6 batch fixtures, 8/8 fixed-anchor uplift cases, 8/8 live 3B uplift cases, 8/8 anchor-causal control, 48 gates, full-artefact SHA-256 receipt.

## 11. What we learned

The interesting part of AI fact-checking is not generating an answer; it is making the answer **cross-examinable**. A small model is enough to produce useful adversarial arguments, but only if the product is designed so the model cannot be the judge. The judge is the product.

## 12. What's next

- Multi-source dossiers and cross-source conflicts shipped; the next step is N claims × N sources rather than one claim × N sources.
- Better paraphrase recall on the measured 3B path. 7B is explicitly out of scope for this build; a larger model is not assumed to improve the product score.
- A permanent hosted endpoint runs the same 3B CPU model behind a scale-to-zero container; the next step is a measured cold-start budget on free CPU.

## 13. Built with

Python, `llama.cpp`, Qwen2.5-3B-Instruct-GGUF, HTML, CSS, JavaScript, SHA-256 content addressing, Edge/Playwright for browser tests.

## 14. Try it

- Repository: `https://github.com/guyuezheng33-ai/claim-autopsy`
- Public hosted live page: `https://guyuezheng33-ai.github.io/claim-autopsy/web/index.html`
- Five-step judge mode: `https://guyuezheng33-ai.github.io/claim-autopsy/web/index.html?judge=1`
- Shorter proof-only link: `https://guyuezheng33-ai.github.io/claim-autopsy/web/index.html?demo=struck`
- Public visual walkthrough: `https://guyuezheng33-ai.github.io/claim-autopsy/web/demo.html` — embeds the 57.4s captioned MP4 and the five steps.
- Video file: [`evidence/demo_60s.mp4`](evidence/demo_60s.mp4) — 57.4s, 1280×720, captioned, silent; five steps end on the struck-quote receipt.
- Devpost video field: use the public visual-walkthrough URL above. For a native YouTube/Vimeo embed, upload `evidence/demo_60s.mp4` and paste the platform URL.
- Hosted black-box receipt: [`evidence/hosted_live.json`](evidence/hosted_live.json) — 204 CORS preflight, 18.9s trial, run `8b65d66160855ed5`, model `qwen2.5-3b-instruct-q4_k_m.gguf`.
- Re-run the hosted check: `python tools/check_hosted_live.py`

The hosted page does not hide the free-form form. The judge-mode link hides it for a stable five-step rail: trap, real model mistake, accepted quote, four-source conflict, receipt. In judge mode the top-right link becomes **Test your own claim** and returns to the live form. The page labels the fixture, the recorded 1.5B run and the hosted 3B run separately.

These are the only fields that require the author's accounts. No URL is fabricated.
Devpost normally embeds video only from YouTube or Vimeo; a stable video URL is still required
before the final submission.

### Screenshots

Seven 1440×900 screenshots are committed under `evidence/screenshots/`:

- [`01-judge-path.png`](evidence/screenshots/01-judge-path.png) — the 5-step rail plus the struck quotation
- [`02-real-model-mistake.png`](evidence/screenshots/02-real-model-mistake.png) — recorded 1.5B `side_mismatch`
- [`03-accepted-quote.png`](evidence/screenshots/03-accepted-quote.png) — accepted quote `chars 0-108` and source highlight
- [`04-four-source-conflict.png`](evidence/screenshots/04-four-source-conflict.png) — 4-source conflict, no winner
- [`05-receipt.png`](evidence/screenshots/05-receipt.png) — receipt actions and run id
- [`06-supported.png`](evidence/screenshots/06-supported.png) — supported verdict
- [`07-not-in-source.png`](evidence/screenshots/07-not-in-source.png) — `not_in_source` with nearest sentence

Local:

```bash
python tools/get_model.py
python serve.py
# http://127.0.0.1:8765
```

No API key is required for the local path. The first run downloads a 2.0 GB model once. If the
judge prefers not to run Python, the public GitHub Pages page calls the hosted 3B endpoint; a
`file://` copy stays in labelled recorded mode. `?judge=1` is the five-step rail.

Numbers used in the Devpost form:

| Field | Value |
|---|---:|
| Evidence cards | 112 |
| Authoritative sources | 41 |
| Held-out claims | 93/93 |
| AI recall gain | +0.9286 |
| Acceptance gates | 48/48 |
| Court fixtures | 33/33 |
| Batch fixtures | 6/6 |
| Run receipt | 66 artefacts |
| Final manifest | 0 problems; 194 files |

The public GitHub Pages page calls the hosted 3B endpoint for any pasted citation; the five-step
rail is a labelled recording. Do not describe the five-step rail as a live model call.

## 15. Team

One person: product and architecture, court kernel and judge, local model integration, frontend, fixtures and acceptance tests. External reviewer sessions and the video are submission materials, not product claims.

## 16. Pre-existing vs work done during the event

No other team's project or code was copied. The corpus/citation audit was written earlier in this same build and is kept as a legacy mode. The court kernel, deterministic judge, AI firewall, local Qwen 3B integration, semantic bridge, multi-source batch, recorded live dossiers and the 48-gate acceptance were added during this refactor. The repository is the honest record of both layers.

## 17. AI assistance disclosure

LLM coding assistance was used for refactoring and test scaffolding. Every behavioural claim in this submission is backed by a local command, a fixture, a browser run or a SHA-256 receipt. No evidence number, quotation or benchmark result was generated by a model.

## 18. Submission checklist

- [x] Public repository URL and license visible
- [x] Hosted demo URL, or explicit “run locally” instruction
- [x] 60-second captioned screen recording: `evidence/demo_60s.mp4` (57.4s)
- [x] Public visual walkthrough: `web/demo.html` embeds the MP4 with no external player
- [ ] Optional native YouTube unlisted / Vimeo embed URL pasted into the Devpost video field
- [x] Screenshots: judge path, struck, real model mistake, supported, not-in-source, conflict, receipt
- [ ] Devpost team fields and eligibility
- [x] No API keys, private data or reviewer-only links
