# Claim Autopsy — 60-second screen-recording script

No presenter needed. Record the browser window only, 1920×1080, at about 110% zoom.
Six shots, six voiceover lines. Total about 60 seconds.

The static page is a recording. The live court is `python serve.py`. Do not call the static page
live; the badges must say `RECORDED LIVE AI RUN` and `LIVE AI` respectively.

---

### Shot 1 — Opening, static court (0:00–0:08)

**Screen**: Open `web/index.html`. Hold on the court header, the title “Was this claim ever in the
source?”, the line “AI argues. Evidence decides.” and the four example chips. Keep the badge
`RECORDED LIVE AI RUN` visible.

**Voiceover**: “This is Claim Autopsy. It does not ask a model for the truth. AI argues both sides,
and a deterministic judge checks every quotation against the source.”

---

### Shot 2 — Live run and real progress (0:08–0:22)

**Screen**: Open the live page from `python serve.py` at `127.0.0.1:8765`. Click “Open the trial”.
Show the progress panel moving through `Rules triage`, `Evidence packet` and `AI advocates`.
Keep 3–4 seconds of the AI stage with the elapsed counter, then jump-cut to `Judge verified`.
Do not speed up or fake the run; say the CPU time out loud.

**Voiceover**: “On CPU this run takes about twenty seconds. The page shows which stage is running,
with a real elapsed clock, then hands the docket to the judge.”

---

### Shot 3 — A struck argument (0:22–0:34)

**Screen**: Scroll to the prosecution column. Point at the red `STRUCK` card and its reason
`quote_not_found`. Hold so the fabricated quotation and the judge’s rule are both readable.

**Voiceover**: “The prosecution invented a quotation. The judge strikes it, records the reason,
and the verdict does not move. The model never owns the verdict.”

---

### Shot 4 — The judge accepts a grounded argument (0:34–0:44)

**Screen**: Show the green `ACCEPTED` defence card beside the judge’s ruling, with the exact quote
and character offsets. If using the Aspirin case, show the semantic bridge line as well.

**Voiceover**: “A grounded quotation is accepted with its character offsets. When the wording
differs, AI can propose a bridge; the judge re-runs the structural checks before it changes anything.”

---

### Shot 5 — One claim × four sources (0:44–0:54)

**Screen**: Click “Load recorded 4-source batch” and run it. Show the four rows, the
`cross-source conflict` row and the summary counts. Do not open every row.

**Voiceover**: “For multiple sources, rules triage first and AI is spent only where rules cannot
settle. Support and refutation can coexist; the page reports the conflict and does not pick a winner.”

---

### Shot 6 — Receipt and close (0:54–1:00)

**Screen**: Click “Copy JSON receipt” or open the receipt block. Show `run_id`, the source hash, the
accepted quote offsets and the struck reason. End on the line “every accepted argument has an exact
quotation.”

**Voiceover**: “Every docket leaves a receipt: the source hash, the exact span, what was accepted,
what was struck. Evidence, not answers.”

---

Recording notes:

- Use Edge or Chrome, notifications off, cursor parked between actions.
- Export MP4 / H.264 / 1080p, under 60 seconds.
- Upload unlisted, then test the link signed out.
- If the 3B wait is too long for the edit, keep the progress panel visible and jump-cut; never
  present a recorded run as live.
