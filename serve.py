"""Local API server (standard library, zero dependencies).

It lets the front end move from pure offline rules to a real AI semantic path.
- With LLM_API_KEY: /api/analyze runs AI semantic scoring plus the deterministic gate.
- Without it: still runnable, but /api/status reports degraded honestly.
- Binds loopback by default (`HOST` / `PORT` from the environment), with a static-file allowlist; no arbitrary path reads.
"""
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from core import llm
from core.citation import audit as citation_audit
from core.court import build_evidence, make_dossier, rule_split
from core.court_batch import run_batch
from core.pipeline import analyze, analyze_many

ROOT = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(ROOT, "web", "index.html")
WEB_DIR = os.path.join(ROOT, "web")
STATIC = {
    "/court.js": ("court.js", "application/javascript; charset=utf-8"),
    "/court_replay.js": ("court_replay.js", "application/javascript; charset=utf-8"),
}
CORPUS = os.path.join(ROOT, "data", "claims.json")
ACCEPT = os.path.join(ROOT, "evidence", "acceptance_final.json")
PORT = int(os.environ.get("PORT", "8765"))
# A local demo binds the loopback interface; a container host needs the
# process reachable from outside, so HOST is explicit and defaults to loopback.
HOST = os.environ.get("HOST", "127.0.0.1")

# One shared counter per client, 60 requests a minute. A demo endpoint that
# accepts arbitrary text should not be an unbounded compute tap.
WINDOW = 60.0
BURST = 60
_hits = {}


def _allow(ip):
    now = time.time()
    stamps = [t for t in _hits.get(ip, []) if now - t < WINDOW]
    if len(stamps) >= BURST:
        _hits[ip] = stamps
        return False
    stamps.append(now)
    _hits[ip] = stamps
    return True


def _split_batch(payload):
    texts = payload.get("texts")
    if isinstance(texts, list):
        return [str(t) for t in texts]
    text = payload.get("text")
    if isinstance(text, str):
        return [line for line in text.splitlines()]
    return []



class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass  # never log request bodies

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(data)

    def _stream_start(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

    def _stream_event(self, event):
        line = (json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8")
        self.wfile.write(("%x\r\n" % len(line)).encode("ascii") + line + b"\r\n")
        self.wfile.flush()

    def _stream_end(self):
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            try:
                with open(WEB, "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except OSError:
                self._send(500, json.dumps({"error": "web_missing"}, ensure_ascii=False))
        elif path in STATIC:
            name, ctype = STATIC[path]
            try:
                with open(os.path.join(WEB_DIR, name), "rb") as f:
                    self._send(200, f.read(), ctype)
            except OSError:
                self._send(404, json.dumps({"error": "static_missing"}))
        elif path == "/api/status":
            self._send(200, json.dumps({
                "mode": llm.mode_label(),
                "ai_available": llm.available(),
                "note": "AI is advisory only; the deterministic gate owns the three-state verdict.",
            }, ensure_ascii=False))
        elif path == "/api/health":
            gates = {"passed": None, "total": None}
            try:
                with open(ACCEPT, "r", encoding="utf-8") as f:
                    acc = json.load(f)
                results = acc.get("results", {})
                gates = {"passed": sum(1 for v in results.values() if v.get("pass")),
                         "total": len(results), "all_pass": acc.get("all_pass")}
            except (OSError, ValueError):
                pass
            self._send(200, json.dumps({
                "status": "ok", "mode": llm.mode_label(), "gates": gates,
                "endpoints": ["/api/status", "/api/health", "/api/corpus",
                              "/api/analyze", "/api/batch", "/api/citation",
                              "/api/trial", "/api/trial_stream", "/api/trial_multi"],
            }, ensure_ascii=False))
        elif path == "/api/corpus":
            try:
                with open(CORPUS, "rb") as f:
                    self._send(200, f.read())
            except OSError:
                self._send(500, json.dumps({"error": "corpus_missing"}))
        else:
            self._send(404, json.dumps({"error": "not_found"}))

    def do_POST(self):
        path = self.path.split("?")[0]
        if path not in ("/api/analyze", "/api/batch", "/api/citation", "/api/trial",
                        "/api/trial_stream", "/api/trial_multi"):
            self._send(404, json.dumps({"error": "not_found"}))
            return
        ip = self.client_address[0]
        if not _allow(ip):
            self._send(429, json.dumps({"error": "rate_limited", "limit": BURST,
                                        "window_seconds": int(WINDOW)}))
            return
        try:
            n = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(n).decode("utf-8"))
            if path == "/api/analyze":
                text = str(payload.get("text", "")).strip()
                if not text:
                    self._send(400, json.dumps({"error": "empty_text"}))
                    return
                self._send(200, json.dumps(analyze(text, use_llm=True), ensure_ascii=False))
                return
            if path == "/api/citation":
                claim = str(payload.get("claim", "")).strip()
                source = str(payload.get("source", "")).strip()
                if not claim or not source:
                    self._send(400, json.dumps({"error": "empty_claim_or_source"}))
                    return
                res = citation_audit(claim, source, payload.get("source_name") or "provided source")
                if res.get("error"):
                    self._send(400, json.dumps(res, ensure_ascii=False))
                    return
                self._send(200, json.dumps(res, ensure_ascii=False))
                return
            if path == "/api/trial_multi":
                claim = str(payload.get("claim", "")).strip()
                sources = payload.get("sources")
                if not claim or not isinstance(sources, list) or not sources:
                    self._send(400, json.dumps({"error": "empty_claim_or_sources"}))
                    return
                live = bool(payload.get("live", True)) and llm.available()
                res = run_batch(claim, sources, live=live,
                                ai_limit=payload.get("ai_limit", 3),
                                model=llm.active_model() if live else None)
                if res.get("error"):
                    self._send(400, json.dumps(res, ensure_ascii=False))
                    return
                res["ai_requested"] = bool(payload.get("live", True))
                res["ai_available"] = llm.available()
                self._send(200, json.dumps(res, ensure_ascii=False))
                return
            if path == "/api/trial_stream":
                claim = str(payload.get("claim", "")).strip()
                source = str(payload.get("source", "")).strip()
                if not claim or not source:
                    self._send(400, json.dumps({"error": "empty_claim_or_source"}))
                    return
                started = time.time()
                live = bool(payload.get("live", True)) and llm.available()
                source_name = payload.get("source_name") or "provided source"
                self._stream_start()
                try:
                    self._stream_event({
                        "type": "phase", "phase": "rules",
                        "detail": "Splitting the claim and checking negation, scope and numbers.",
                        "elapsed": round(time.time() - started, 1),
                    })
                    atoms = rule_split(claim)[:8] or [claim]
                    self._stream_event({
                        "type": "phase", "phase": "evidence",
                        "detail": "Hashing the source and indexing candidate sentences.",
                        "elapsed": round(time.time() - started, 1),
                    })
                    packet = build_evidence(source, source_name)
                    ai_args = None
                    meta = {"available": False, "reason": "rules_only"}
                    if live:
                        self._stream_event({
                            "type": "phase", "phase": "ai",
                            "detail": "Local 3B prosecution and defence draft grounded arguments.",
                            "elapsed": round(time.time() - started, 1),
                        })
                        box = {}

                        def work():
                            try:
                                box["args"], box["meta"] = llm.collect_ai_arguments(atoms, packet)
                            except Exception as exc:  # noqa: BLE001
                                box["kind"] = type(exc).__name__

                        worker = threading.Thread(target=work, daemon=True)
                        worker.start()
                        while worker.is_alive():
                            worker.join(2.0)
                            if worker.is_alive():
                                self._stream_event({
                                    "type": "tick", "phase": "ai",
                                    "elapsed": round(time.time() - started, 1),
                                })
                        worker.join()
                        ai_args = box.get("args")
                        meta = box.get("meta") or {
                            "available": llm.available(),
                            "error": box.get("kind", "ai_failed"),
                        }
                    else:
                        self._stream_event({
                            "type": "phase", "phase": "ai", "status": "skipped",
                            "detail": "No local model available; keeping the rules-only docket.",
                            "elapsed": round(time.time() - started, 1),
                        })
                    self._stream_event({
                        "type": "phase", "phase": "judge",
                        "detail": "Checking every quote character by character and re-running the bridge.",
                        "elapsed": round(time.time() - started, 1),
                    })
                    res = make_dossier(
                        claim, source, source_name,
                        ai_arguments=ai_args,
                        mode="ai" if live else "rules",
                        model=llm.active_model() if live else None,
                        trace=[{"step": "advocates", "meta": meta}],
                    )
                    res["ai_requested"] = bool(payload.get("live", True))
                    res["ai_available"] = llm.available()
                    res["ai_meta"] = meta
                    self._stream_event({
                        "type": "result", "elapsed": round(time.time() - started, 1),
                        "payload": res,
                    })
                except (BrokenPipeError, ConnectionResetError):
                    return
                except Exception as exc:  # noqa: BLE001
                    try:
                        self._stream_event({
                            "type": "error", "error": "trial_failed",
                            "kind": type(exc).__name__,
                            "elapsed": round(time.time() - started, 1),
                        })
                    except (BrokenPipeError, ConnectionResetError):
                        return
                    return
                try:
                    self._stream_end()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            if path == "/api/trial":
                claim = str(payload.get("claim", "")).strip()
                source = str(payload.get("source", "")).strip()
                if not claim or not source:
                    self._send(400, json.dumps({"error": "empty_claim_or_source"}))
                    return
                live = bool(payload.get("live", True)) and llm.available()
                ai_args, meta = None, {"available": False, "reason": "rules_only"}
                if live:
                    atoms = rule_split(claim)[:8] or [claim]
                    packet = build_evidence(source, payload.get("source_name") or "provided source")
                    ai_args, meta = llm.collect_ai_arguments(atoms, packet)
                res = make_dossier(
                    claim, source,
                    payload.get("source_name") or "provided source",
                    ai_arguments=ai_args,
                    mode="ai" if live else "rules",
                    model=llm.active_model() if live else None,
                    trace=[{"step": "advocates", "meta": meta}],
                )
                if res.get("error"):
                    self._send(400, json.dumps(res, ensure_ascii=False))
                    return
                res["ai_requested"] = bool(payload.get("live", True))
                res["ai_available"] = llm.available()
                res["ai_meta"] = meta
                self._send(200, json.dumps(res, ensure_ascii=False))
                return
            texts = _split_batch(payload)
            if not [t for t in texts if t.strip()]:
                self._send(400, json.dumps({"error": "empty_batch"}))
                return
            self._send(200, json.dumps(analyze_many(texts, use_llm=True), ensure_ascii=False))
        except Exception as exc:
            # generic error only; never leak exception text or credentials
            self._send(500, json.dumps({"error": "analyze_failed", "kind": type(exc).__name__}))


if __name__ == "__main__":
    ready = llm.ensure_local_server()
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print("Claim Autopsy running at http://%s:%d" % (HOST, PORT))
    print("Mode: %s" % llm.mode_label())
    if ready:
        print("Local AI: %s via llama.cpp on CPU (no API key, no outbound request)." % llm.mode_label())
    else:
        print("Tip: run `python tools/get_model.py` for local AI, or set LLM_API_KEY.")
    srv.serve_forever()
