#!/bin/sh
# Hosted live entrypoint: start llama-server on loopback, wait for health,
# warm one tiny completion, then hand the port to the claim-autopsy API.
set -eu

MODEL="${LOCAL_LLM_MODEL:-/app/models/qwen2.5-3b-instruct-q4_k_m.gguf}"
LLM_PORT="${LOCAL_LLM_PORT:-8099}"
THREADS="${LLAMA_THREADS:-2}"

if [ ! -s "$MODEL" ]; then
  echo "FATAL: model missing at $MODEL" >&2
  exit 1
fi

/app/llama-server \
  -m "$MODEL" \
  -c 4096 \
  --host 127.0.0.1 \
  --port "$LLM_PORT" \
  -t "$THREADS" \
  -ngl 0 \
  --no-warmup &
LLAMA_PID=$!

cleanup() {
  kill "$LLAMA_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

i=0
until curl -fsS "http://127.0.0.1:${LLM_PORT}/health" >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -ge 180 ]; then
    echo "FATAL: llama-server did not become healthy in 180s" >&2
    exit 1
  fi
  sleep 1
done
echo "llama-server ready on 127.0.0.1:${LLM_PORT}"

# One-token warmup removes the worst first-request latency without paying for
# a full synthetic trial. Failure here is non-fatal: serve.py will report it.
curl -m 120 -fsS "http://127.0.0.1:${LLM_PORT}/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -d '{"model":"local","messages":[{"role":"user","content":"ok"}],"max_tokens":1,"temperature":0}' \
  >/dev/null 2>&1 || echo "warmup skipped"

exec python3 /app/serve.py
