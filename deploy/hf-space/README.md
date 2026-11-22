---
title: Claim Autopsy Live
emoji: ⚖️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8080
pinned: false
short_description: Citation court with a hosted Qwen2.5-3B judge.
---

# Claim Autopsy Live

This Space is the hosted model endpoint for the public Claim Autopsy page.

- The browser sends one claim and one source to `/api/trial_stream`.
- Qwen2.5-3B-Instruct (Q4_K_M) is served by `llama-server` on CPU inside the Space.
- The model argues both sides; a deterministic gate verifies every quotation and owns the verdict.
- No API key is stored in the browser, and request bodies are not logged.

Endpoints:

- `GET /api/health`
- `GET /api/status`
- `POST /api/trial_stream` with `{"claim": "...", "source": "..."}`
- `POST /api/trial` with the same body
- `POST /api/trial_multi` with `{"claim": "...", "sources": [{"name": "...", "text": "..."}]}`

The public page is served from GitHub Pages and calls this Space cross-origin.
