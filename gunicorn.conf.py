import multiprocessing
import os

# ── Binding ───────────────────────────────────────────────────────────────
bind    = f"0.0.0.0:{os.getenv('PORT', '5000')}"

# ── Workers ───────────────────────────────────────────────────────────────
# 2–4 sync workers per CPU core is a sensible default.
# Streaming (SSE) requires threads so each worker can handle concurrent streams.
workers     = int(os.getenv("GUNICORN_WORKERS", max(2, multiprocessing.cpu_count())))
worker_class = "sync"
threads     = int(os.getenv("GUNICORN_THREADS", 4))

# ── Timeouts ──────────────────────────────────────────────────────────────
# 120 s to accommodate long Gemini + GitHub fetches.
timeout    = int(os.getenv("GUNICORN_TIMEOUT", 120))
keepalive  = 5

# ── Request limits (prevent memory bloat) ─────────────────────────────────
max_requests        = 1000
max_requests_jitter = 100

# ── Logging ───────────────────────────────────────────────────────────────
accesslog = "-"
errorlog  = "-"
loglevel  = os.getenv("LOG_LEVEL", "info").lower()

# ── Process naming ────────────────────────────────────────────────────────
proc_name = "ani"
