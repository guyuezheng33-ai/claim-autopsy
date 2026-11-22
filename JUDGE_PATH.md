# Claim Autopsy - three-minute judge path

No install is required for the recorded demo. Open this link and follow the clicks:

`https://guyuezheng33-ai.github.io/claim-autopsy/web/index.html?demo=struck`

The page labels the difference between a fixture, a recorded model run, and a live run.
Do not call the static page live. Only `python serve.py` can call the model live.

## 0:00-0:20 - The trap

Click **Show the fabricated quote**.

You should see:

- badge `ADVERSARIAL FIXTURE`;
- **AI proposed**: "The flu vaccine contains live virus and causes influenza." with `quote_not_found`;
- **Source says**: "It is impossible to get influenza from the injected vaccine because the vaccine does not contain live virus.";
- **Judge**: `refuted`; the strike did not change the verdict.

This is an adversarial fixture, not a model run. It proves the judge can reject a plausible
fabrication. The page says so instead of pretending the fixture came from the model.

## 0:20-0:40 - A real model mistake

Click **Show a real model mistake**.

You should see:

- badge `RECORDED LIVE AI RUN`;
- model `qwen2.5-1.5b-instruct-q4_k_m.gguf`;
- a struck argument with `side_mismatch`;
- the same source quotation on the judge's side.

This is an actual recorded local run. The model used a true quotation on the wrong side; the
judge struck it. The verdict stayed with the evidence.

## 0:40-1:20 - A grounded argument

Click **Flu vaccine - refuted**.

You should see:

- `refuted` for the atom;
- an accepted argument with the exact quotation and `chars 0-108`;
- the source panel highlights that same span;
- the receipt block with `run_id`, source hash, and the accepted and struck counts.

The accepted argument is not an opinion. It is a character-for-character match.

## 1:20-2:00 - One claim, four sources

Click **Batch sources**, then **Load recorded 4-source batch**.

You should see:

- four source rows;
- one `cross-source conflict`;
- no winner picked;
- a multi-source receipt link.

Rules triage every source first. AI is spent only on sources the rules cannot settle.

## 2:00-3:00 - The receipt

Scroll to the receipt actions and click **Copy JSON receipt** or **Download Markdown receipt**.

Check that the receipt contains:

- the claim and source hash;
- the accepted quote and character offsets;
- the struck quote and its reason code;
- the model name, or `adversarial fixture` when no model ran.

## Optional live path

The public page is a recording. For live AI on any text:

```text
python serve.py
# open http://127.0.0.1:8765
```

The local 3B model runs on CPU with no API key. First docket is about 20-35 seconds.
The page shows four real stages and then `LIVE AI - JUDGE VERIFIED`.
