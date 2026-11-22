# Hosted live demo for Claim Autopsy.
# Base image already contains the Linux llama-server binary and its shared libs.
# We only add Python (serve.py is stdlib-only) and the 3B GGUF weight.
FROM ghcr.io/ggml-org/llama.cpp:server

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# The model is baked into the image so a cold Space start does not download 2 GB.
RUN mkdir -p /app/models \
 && curl -L --fail --retry 5 --retry-delay 3 -sS \
    -o /app/models/qwen2.5-3b-instruct-q4_k_m.gguf \
    https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf \
 && test -s /app/models/qwen2.5-3b-instruct-q4_k_m.gguf

ENV HOST=0.0.0.0 \
    PORT=8080 \
    PUBLIC_HOSTED=1 \
    LOCAL_LLM_MODEL=/app/models/qwen2.5-3b-instruct-q4_k_m.gguf \
    LOCAL_LLM_BASE_URL=http://127.0.0.1:8099/v1/chat/completions \
    LOCAL_LLM_PORT=8099 \
    LLAMA_THREADS=2 \
    PYTHONUNBUFFERED=1

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/api/health || exit 1

CMD ["/bin/sh", "/app/start.sh"]
