# Claim Autopsy — user handoff checklist

Freeze point: **2026-11-21**. This file lists only the steps that need your GitHub / hosting /
screen / reviewer access. The local product is already built and verified.

**Current state**

- `python -m core.audit final` → **48/48, all_pass=True**
- run receipt → `b27a5ff305a1fce700536eedc5d89136`, **46 artefacts**, exit 0
- `FINAL_MANIFEST.md` → **209 files**, 0 problems
- court fixtures → **33/33**; batch fixtures → **6/6**; browser checks → static **ok**, live **ok**
- live 3B → **20–35 s** per docket; the page shows four real stages instead of a blank spinner
- 7B → **explicitly out of scope for this build**

Red lines:

- Never commit a key. `.gitignore` blocks `.env`; A8 asserts `keys=0`.
- Do not edit a bound file after publishing without re-minting the receipt and manifest. The order is:
  `python tools/make_receipt.py final --bootstrap` → `python tools/make_receipt.py final` →
  `python -m core.audit final` → `python tools/check_manifest.py --write`.
- Say “recorded” for the static page and “live” only for `python serve.py`. Do not blur them.

---

## Step 1. Publish a public GitHub repository (30–40 min)

1.1 Already done: `LICENSE` now reads `Copyright (c) 2026 HUCHAOZHENG`. If you later change the
holder or any tracked file, run `python tools/check_manifest.py --write` so the manifest matches
the file you will publish.

1.2 Check Git is installed:

```powershell
git --version
```

If missing, install Git for Windows first (`winget install --id Git.Git -e --source winget`), then
open a new terminal.

1.3 From the project root:

```powershell
git init
git add .
git status
```

`git status` must not contain `__pycache__`, `.venv`, `.env`, `*.pyc`, `serve.pid`, or any model
file. `.gitignore` already blocks most of these; `serve.pid` is a runtime file and is ignored too.

1.4 Before the first commit, run:

```powershell
python -m core.audit final
```

Expect **48/48**, including `A8_no_secrets keys=0` and `A37_run_receipt` with receipt
`b27a5ff305a1fce700536eedc5d89136`.

1.5 Commit and push:

```powershell
git commit -m "Claim Autopsy: citation court with AI advocates and a deterministic judge"
git branch -M main
git remote add origin https://github.com/<your-username>/claim-autopsy.git
git push -u origin main
```

1.6 Open the repository in a signed-out window. Confirm the README title and screenshots render,
and the repository is **Public** (Settings → General → Danger zone).

---

## Step 2. Publish the static demo (10 min)

2.1 GitHub Pages: Settings → Pages → Source “Deploy from a branch” → branch `main`, folder `/ (root)`.

2.2 The URL is:

```text
https://<your-username>.github.io/claim-autopsy/web/index.html
```

Keep the `/web/` segment. Do not move or delete `web/index.html`.

2.3 Wait 1–3 minutes, then open the URL in a signed-out/incognito window and check:

- the court badge reads **`RECORDED LIVE AI RUN`**, never `LIVE AI`, on the static page;
- the legacy panel reads **`RECORDED · NOT LIVE`**;
- the four court examples run (Eiffel, flu, guard, coffee);
- the corpus browser shows **112 cards**;
- a Chinese claim shows the “English only” notice, not a bare `Claims: 0`;
- `A common cold can resolve on its own.` still shows the archived paragraph and its hash;
- a 4-source batch shows one cross-source conflict without picking a winner.

The static page cannot call a model. The live court requires `python serve.py`; say that explicitly
in the submission instead of implying the hosted page is live.

---

## Step 3. Clean-machine reproduction (15 min, strong evidence)

Do this on a different machine, or at least a fresh folder with no existing cache:

```powershell
git clone https://github.com/<your-username>/claim-autopsy.git
cd claim-autopsy
python -m core.audit final
```

Expect **48/48**. Then, if the 3B model is not present:

```powershell
python tools/get_model.py
```

Start the live court:

```powershell
python serve.py
```

Open `http://127.0.0.1:8765`. Wait 20–35 seconds. You should see, in order:

1. `Rules triage`
2. `Evidence packet`
3. `AI advocates`
4. `Judge verifies`

The panel should finish at `Judge verified`, with elapsed time and accepted / struck counts. If
`llama-server` is missing, install the CPU build (`winget install --id ggml.llamacpp -e`), then
restart `serve.py`. Do not use a GPU backend; this build is pinned to `-ngl 0`.

---

## Step 4. Record the 60-second video (45–60 min)

Follow `evidence/video_script.md`. The current script is written for the court, not the old legacy
screen. Record browser-only at 1920×1080, notifications off.

If you record a full 3B wait, keep 3–4 seconds of the progress panel and jump-cut to the completed
docket. Say “about 20 seconds on CPU” rather than speeding up the UI.

Upload as an **unlisted** YouTube video, then open the link signed out. Paste it into
`SUBMISSION.md` section 14.

---

## Step 5. External reviewer sessions (optional, 30–45 min)

Current A40 external-operator count is **0**. This is a testing-evidence gap, not a product-score
gap; it does not change the 94/100 product score by itself.

Rehearse first:

```powershell
python tools/run_external_session.py --rehearse
```

Then run 2–3 sessions with people who are not you:

```powershell
python tools/run_external_session.py --operator external-reviewer --channel screen-share
```

Record what they actually did, including “discarded” or “re_prompted”. Then:

```powershell
python tools/verify_sessions.py
python tools/make_receipt.py final --bootstrap
python tools/make_receipt.py final
python -m core.audit final
```

If you skip this, do not claim external user testing. The submission currently says the sessions
are by the builder.

---

## Step 6. Fill Devpost (20 min)

Use `SUBMISSION.md` section by section. The three fields that need your accounts are:

| Devpost field | Value |
|---|---|
| Repository URL | your public GitHub URL |
| Demo / “Try it out” URL | your Pages URL ending in `/web/index.html` |
| Video URL | your unlisted YouTube URL |

Numbers to paste, exactly:

| Field | Value |
|---|---:|
| Evidence cards | 112 |
| Authoritative sources | 41 |
| Held-out claims | 93/93 |
| AI recall gain | +0.9286 |
| Acceptance gates | 48/48 |
| Court fixtures | 33/33 |
| Batch fixtures | 6/6 |
| Run receipt | 46 artefacts |
| Final manifest | 209 files |

Do not round these into larger claims. Do not describe the static court as live.

---

## Step 7. Final pre-submit check (10 min)

```powershell
python -m core.audit final
python tools/check_manifest.py
```

Expect `Result 48/48 all_pass=True` and `manifest rows verified, 0 problems`.

Then, signed out:

- repository opens and is public;
- `/web/index.html` opens and all examples work;
- video plays;
- Devpost page shows the repository, demo and video links;
- no placeholder text remains in `SUBMISSION.md` section 14.

Submit by **2026-12-09** to keep a day before the **2026-12-10** deadline.
