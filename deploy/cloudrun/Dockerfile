# Cloud Run hosted live demo for Claim Autopsy.
# Base image already contains the Linux llama-server binary and its shared libs.
# We add Python (serve.py is stdlib-only) and bake the 3B GGUF weight so a cold
# container start does not download 2 GB at request time.
FROM ghcr.io/ggml-org/llama.cpp:server

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY serve.py /app/serve.py
COPY core /app/core
COPY web /app/web
COPY data /app/data
COPY evidence /app/evidence
COPY deploy/cloudrun/start.sh /app/start.sh

# The model is baked into the image so a cold instance does not fetch 2 GB.
RUN mkdir -p /app/models \
 && curl -L --fail --retry 5 --retry-delay 3 -sS \
    -o /app/models/qwen2.5-3b-instruct-q4_k_m.gguf \
    https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf \
 && test -s /app/models/qwen2.5-3b-instruct-q4_k_m.gguf

# The base image keeps its shared llama.cpp libraries under /app; export the
# path so llama-server can resolve libllama-common.so at container start.
# Cloud Run injects PORT; HOST stays 0.0.0.0 so the proxy can reach the process.
ENV LD_LIBRARY_PATH=/app \
    HOST=0.0.0.0 \
    PORT=8080 \
    PUBLIC_HOSTED=1 \
    LOCAL_LLM_MODEL=/app/models/qwen2.5-3b-instruct-q4_k_m.gguf \
    LOCAL_LLM_BASE_URL=http://127.0.0.1:8099/v1/chat/completions \
    LOCAL_LLM_PORT=8099 \
    LLAMA_THREADS=2 \
    PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["/bin/sh", "/app/start.sh"]
