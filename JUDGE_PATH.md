# Claim Autopsy - three-minute judge path

No install is required for the recorded demo. Open this link:

`https://guyuezheng33-ai.github.io/claim-autopsy/web/index.html?judge=1`

The page enters **judge mode**: the free-form form is hidden, step 1 is already selected, and
the five-step rail under **THE 10-SECOND PROOF** is the whole path. Click a step, or click
**Next ->**. The last step changes the button to **Restart ↺**.

The page labels the difference between a fixture, a recorded model run, and a live run.
Do not call the static page live. Only `python serve.py` can call the model live.

## 0:00-0:20 - Step 1: the trap

The page opens on **1 · Trap**. Look at the proof panel, then at the verdict card:

- badge `ADVERSARIAL FIXTURE`;
- **AI proposed**: "The flu vaccine contains live virus and causes influenza." with `quote_not_found`;
- **Source says**: "It is impossible to get influenza from the injected vaccine because the vaccine does not contain live virus.";
- **Judge**: `refuted`; the strike did not change the verdict.

This is an adversarial fixture, not a model run. It proves the judge can reject a plausible
fabrication. The page says so instead of pretending the fixture came from the model.

## 0:20-0:40 - Step 2: a real model mistake

Click **2 · Real mistake**.

You should see:

- badge `RECORDED LIVE AI RUN`;
- model `qwen2.5-1.5b-instruct-q4_k_m.gguf`;
- a struck argument with `side_mismatch`;
- the same source quotation on the judge's side.

This is an actual recorded local run. The model used a true quotation on the wrong side; the
judge struck it. The verdict stayed with the evidence.

## 0:40-1:20 - Step 3: a grounded argument

Click **3 · Accepted quote**.

You should see:

- `refuted` for the atom;
- an accepted argument with the exact quotation and `chars 0-108`;
- the source panel highlights that same span;
- the receipt block with `run_id`, source hash, and the accepted and struck counts.

The accepted argument is not an opinion. It is a character-for-character match.

## 1:20-2:00 - Step 4: one claim, four sources

Click **4 · Conflict**.

You should see:

- four source rows;
- one `cross-source conflict`;
- no winner picked;
- a multi-source receipt.

Rules triage every source first. AI is spent only on sources the rules cannot settle.

## 2:00-3:00 - Step 5: the receipt

Click **5 · Receipt**.

The page returns to the struck trap case, scrolls to **Copy JSON receipt** / **Download Markdown receipt**,
and pulses the action row. Check that the receipt contains:

- the claim and source hash;
- the accepted quote and character offsets;
- the struck quote and its reason code (`quote_not_found`);
- the model name, or `adversarial fixture` when no model ran.

The last step closes the loop: the same fabricated quotation that was struck at 0:00 is now traceable
to a receipt. Click **Restart ↺** to return to step 1.

If you only want the proof panel without judge mode, use the shorter deep link:

`https://guyuezheng33-ai.github.io/claim-autopsy/web/index.html?demo=struck`

## Optional live path

The public page is a recording. For live AI on any text:

```text
python serve.py
# open http://127.0.0.1:8765
```

The local 3B model runs on CPU with no API key. First docket is about 20-35 seconds.
The page shows four real stages and then `LIVE AI - JUDGE VERIFIED`.
