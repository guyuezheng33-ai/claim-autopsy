# Claim Autopsy - 60-second screen-recording script

No presenter needed. Record the browser window only, 1920x1080, at about 110% zoom.
Six shots, six voiceover lines. Total about 60 seconds.

The static page is a recording. The live court is `python serve.py`. Do not call the static page
live; the badges must say `RECORDED LIVE AI RUN`, `ADVERSARIAL FIXTURE`, and `LIVE AI` respectively.

Start from the zero-install link, not the repository:

`https://guyuezheng33-ai.github.io/claim-autopsy/web/index.html?demo=struck`

---

### Shot 1 - The trap, no install (0:00-0:10)

**Screen**: Open the link above. The page is already on the adversarial case. Click **Show the
fabricated quote**. Hold on the trap banner: the red struck quotation with `quote_not_found`, the
green source sentence, and the judge's `refuted` line. Keep the badge `ADVERSARIAL FIXTURE` visible.

**Voiceover**: "No install. A model can invent a quotation. This judge checks every character
against the source, strikes this one as `quote_not_found`, and the verdict stays with the evidence."

---

### Shot 2 - The same judge on a real model mistake (0:10-0:20)

**Screen**: Click **Show a real model mistake**. Show the badge `RECORDED LIVE AI RUN`, the 1.5B
model name, the struck card with `side_mismatch`, and the same source quotation on the judge's side.

**Voiceover**: "This one is a real recorded model run, not a fixture. The model used a true
quotation on the wrong side; the judge struck it. The badge tells you which is recorded and which
is a test."

---

### Shot 3 - Live run and real progress (0:20-0:34)

**Screen**: Open the live page from `python serve.py` at `127.0.0.1:8765`. Click **Open the trial**.
Show the progress panel moving through `Rules triage`, `Evidence packet` and `AI advocates`.
Keep 3-4 seconds of the AI stage with the elapsed counter, then jump-cut to `Judge verified`.
Do not speed up or fake the run; say the CPU time out loud.

**Voiceover**: "On CPU this takes about twenty seconds. The page shows which stage is running,
with a real clock, then hands the docket to the judge. The model argues; it never writes the verdict."

---

### Shot 4 - The judge accepts a grounded argument (0:34-0:46)

**Screen**: Show an accepted argument beside the judge's ruling. Open the `Flu vaccine - refuted`
case. Hold on the exact quote, `chars 0-108`, and the highlighted source span.

**Voiceover**: "A grounded quotation is accepted with its character offsets, and the exact span is
highlighted in the source. When the wording differs, AI can propose a bridge; the judge re-runs
the structural checks before anything changes."

---

### Shot 5 - One claim x four sources (0:46-0:54)

**Screen**: Click **Load recorded 4-source batch**. Show the four rows, the `cross-source conflict`
row and the summary counts. Do not open every row.

**Voiceover**: "For multiple sources, rules triage first and AI is spent only where rules cannot
settle. Support and refutation can coexist; the page reports the conflict and does not pick a winner."

---

### Shot 6 - Receipt and close (0:54-1:00)

**Screen**: Click **Copy JSON receipt** or open the receipt block. Show `run_id`, the source hash,
the accepted quote offsets and the struck reason. End on "every accepted argument has an exact
quotation."

**Voiceover**: "Every docket leaves a receipt: the source hash, the exact span, what was accepted,
what was struck. Evidence, not answers."

---

Recording notes:

- Open with the deep link; it removes the setup step and lands on the proof.
- Use Edge or Chrome, notifications off, cursor parked between actions.
- Export MP4 / H.264 / 1080p, under 60 seconds.
- Upload to YouTube unlisted or Vimeo; do not use a short-lived signed CDN link.
- The static page is recorded; only `serve.py` is live. Keep that distinction visible.
