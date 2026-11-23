# Claim Autopsy — three-minute judge path and live test

## Primary: hosted live, no install

Open the public page:

`https://guyuezheng33-ai.github.io/claim-autopsy/web/index.html`

Paste any claim and the source you want to check, then click **Open the trial**. The page calls a
hosted endpoint that runs **Qwen2.5-3B-Instruct Q4_K_M** on CPU. The badge reads
`HOSTED LIVE · 3B` only after `/api/status` confirms `ai_available=true`. A cold model can take
up to a minute to load; the page shows `HOSTED · WAKING 3B` and retries instead of pretending to
be live.

A verified black-box run is in `evidence/hosted_live.json`:

- public page: `https://guyuezheng33-ai.github.io/claim-autopsy/web/index.html`
- endpoint: `https://bali-drive-install-hiking.trycloudflare.com`
- CORS preflight: `204`, `Access-Control-Allow-Origin: *`
- trial: `18.9s`, model `qwen2.5-3b-instruct-q4_k_m.gguf`, run `8b65d66160855ed5`, verdict `supported`
- receipt: 1 atom, 1 accepted argument, 1 struck argument, 1 semantic bridge

Run the same check yourself:

```bash
python tools/check_hosted_live.py
```

Use `--base https://your-space.hf.space` after a Hugging Face Space replaces the tunnel.
The checker never trusts the page badge: it calls `/api/status`, sends an `Origin` header,
performs a real CORS preflight, runs a live trial, and reads the receipt model name.

## Five-step rail (stable recording)

`https://guyuezheng33-ai.github.io/claim-autopsy/web/index.html?judge=1`

The page enters judge mode and starts on step 1. Click a step or **Next →**. Step 5 changes the
button to **Restart ↺**. In judge mode, the top-right link becomes **Test your own claim** and
returns to the live form.

### 0:00–0:20 · Step 1 — the trap

- badge `ADVERSARIAL FIXTURE`;
- **AI proposed**: “The flu vaccine contains live virus and causes influenza.” with `quote_not_found`;
- **Source says**: “It is impossible to get influenza from the injected vaccine because the vaccine does not contain live virus.”;
- **Judge**: `refuted`; the strike did not change the verdict.

This is a fixture, not a model run. It proves the judge rejects a plausible fabrication and says so.

### 0:20–0:40 · Step 2 — a real model mistake

- badge `RECORDED LIVE AI RUN`;
- model `qwen2.5-1.5b-instruct-q4_k_m.gguf`;
- a struck argument with `side_mismatch`;
- the same source quotation on the judge's side.

This is an actual recorded 1.5B run, not a synthetic claim. The model used a true quotation on the
wrong side; the judge struck it.

### 0:40–1:20 · Step 3 — a grounded argument

- `refuted` for the atom;
- accepted argument with `chars 0–108`;
- the source panel highlights the same span;
- a receipt with `run_id`, source hash, accepted and struck counts.

### 1:20–2:00 · Step 4 — one claim, four sources

- four source rows;
- one `cross-source conflict`;
- no winner picked;
- a multi-source receipt.

Rules triage every source first. AI is spent only on sources the rules cannot settle.

### 2:00–3:00 · Step 5 — the receipt

The page returns to the struck trap case and scrolls to **Copy JSON receipt** /
**Download Markdown receipt**. The receipt contains the claim and source hash, the accepted
quote and character offsets, the struck quote with `quote_not_found`, and the model name or
`adversarial fixture`.

## If the hosted endpoint is down

Run the same page locally with the 3B model:

```text
python tools/get_model.py --size 3b   # one-time, 2.0 GB
python serve.py                       # starts llama.cpp + the HTTP server
# open http://127.0.0.1:8765/
```

The local path uses the same `/api/status`, `/api/trial_stream` and `/api/trial` contract. If no
model is available, the page says `RULES-ONLY DOCKET`; it never fakes AI.

## Honesty labels

| What you see | What it is |
|---|---|
| `HOSTED LIVE · 3B` | Public page confirmed a live 3B endpoint through `/api/status` |
| `LIVE AI · JUDGE VERIFIED` | This trial called the live model; the receipt names the 3B model |
| `RECORDED LIVE AI RUN` | A frozen dossier from a real earlier run; no model called now |
| `ADVERSARIAL FIXTURE` | Hand-written trap; no model called |
| `HOSTED API OFFLINE` | The page could not reach the endpoint; it does not fall back silently |

The recorded rail and the hosted trial are separate. The rail is stable for a three-minute read;
the form is the part that must be live.

## Video

`https://guyuezheng33-ai.github.io/claim-autopsy/web/demo.html` embeds the 57.4-second captioned
MP4 (`evidence/demo_60s.mp4`).
