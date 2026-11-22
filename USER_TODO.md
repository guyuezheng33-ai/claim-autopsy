# Claim Autopsy — user handoff checklist

Freeze point: **2026-11-22**. This file lists only the steps that need your GitHub / hosting /
screen / reviewer access. The local product and the 57.4-second captioned video are already built
and verified.

**Current state**

- `python -m core.audit final` → **48/48, all_pass=True**
- run receipt → `ec73045a6a4ab396c62c9266270a1951`, **56 artefacts**, exit 0
- `FINAL_MANIFEST.md` → **0 problems** (row count is in the file)
- court fixtures → **33/33**; batch fixtures → **6/6**; browser checks → static **ok**, live **ok**
- judge path → `?judge=1`, five steps, 390px mobile assertion, **Full product →** exit
- video → `evidence/demo_60s.mp4`, 57.4 s, 1280×720, captioned; public URL still needs your upload
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

1.2 Git is already installed at `C:\Program Files\Git\cmd\git.exe` (2.56.0). The current agent shell
does not see it on `PATH`, so in a terminal either reopen the terminal or use the full path:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' --version
```

1.3 The local repository is already initialized on `main` with an existing commit, author
`HUCHAOZHENG <guyuezheng33@gmail.com>`. Do **not** run `git init` again. Verify it is clean:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' status --short
python -m core.audit final
```

`git status --short` should print nothing. Expect **48/48**, including `A8_no_secrets keys=0` and
`A37_run_receipt` with receipt `ec73045a6a4ab396c62c9266270a1951`.

1.4 Create the empty public repo at `https://github.com/new` (name `claim-autopsy`, Public, no
README), then add the remote and push:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' remote add origin https://github.com/<your-username>/claim-autopsy.git
& 'C:\Program Files\Git\cmd\git.exe' push -u origin main
```

The first push opens a browser for GitHub login / Git Credential Manager. Sign in as
`guyuezheng33-ai` if that is your account, approve the credential, and wait for
`branch 'main' set up to track 'origin/main'`.

1.5 Open the repository in a signed-out window. Confirm the README title and screenshots render,
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

## Step 4. Share the encoded 60-second video (10–15 min, optional platform upload)

The captioned screen recording is already built: `evidence/demo_60s.mp4` — 57.4 s, 1280×720,
five judge-path steps, silent with burned-in captions. It ends on the struck-quote receipt.
It is also embedded in the public visual walkthrough: `web/demo.html` on Pages.

For a native Devpost embed, upload to **Vimeo (free)** or **YouTube (unlisted)**. Devpost normally
embeds video only from YouTube or Vimeo. The public `demo.html` URL is a visual-walkthrough fallback
and works without any platform account. Paste the platform link into `SUBMISSION.md` section 14 if
you upload one.

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
| Run receipt | 56 artefacts |
| Final manifest | row count is in the file |

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
