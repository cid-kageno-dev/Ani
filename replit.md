# Ani — AI Assistant

A Flask-based context-aware chatbot that answers questions as "Ani", fetching live GitHub profile data and using Google Gemini for responses, with Firebase Firestore as the primary store and Replit PostgreSQL as a fallback.

## Run & Operate

- **Run**: `python run.py` (port 5000) — the "Start application" workflow does this automatically
- **Gemini key**: Add `GOOGLE_API_KEY` (or `GOOGLE_API_KEY1`, `GOOGLE_API_KEY2`, …) in the Secrets tab — get one at https://aistudio.google.com/app/apikey
- **Firebase**: `FIREBASE_SERVICE_ACCOUNT_JSON` secret (stringified service account JSON), `FIREBASE_PROJECT_ID` and `FIREBASE_DATABASE_URL` are already set as shared env vars
- **Auto-provided by Replit**: `DATABASE_URL`, `PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGPORT` (built-in PostgreSQL)

## Stack

- Python 3.12
- Flask 3.x + Flask-CORS
- google-genai (Gemini 2.5 Flash)
- psycopg2-binary (PostgreSQL via Replit built-in DB)
- firebase-admin (Firestore — primary DB backend)
- thefuzz (fuzzy match fallback)
- python-json-logger (structured logging)
- gunicorn (production WSGI server)

## Where things live

```
run.py                          entry point
config.py                       all config / env loading
config.json                     non-secret app settings
app/__init__.py                 Flask app factory + startup health checks
app/routes.py                   HTTP endpoints: / | /api/chat | /api/history | /api/stats | /api/health
app/services/ai_service.py      Gemini calls + GitHub context fetching + key rotation
app/services/db_service.py      Firebase / PostgreSQL storage, in-memory cache, fuzzy fallback
app/services/firebase_validator.py  startup credential validation
app/logger.py                   coloured console logging
templates/index.html            chat UI (Jinja2 + vanilla JS)
firebase-key.json               Firebase service account key (local dev fallback)
monitoring.py                   standalone metrics / health / alert utilities (not wired to routes yet)
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Chat web UI |
| POST | `/api/chat` | Chat with Ani — returns `{response, source}` |
| GET | `/api/history?limit=N` | Recent interactions (N capped at 100) |
| GET | `/api/stats` | Aggregate usage stats |
| GET | `/api/health` | Returns `{"status": "ok"}` |

## Architecture decisions

- **DB backend auto-detection**: Firebase when `FIREBASE_PROJECT_ID` is set (preferred); PostgreSQL when `DATABASE_URL` is set; graceful no-op if neither.
- **Gemini key rotation**: reads `GOOGLE_API_KEY1`, `GOOGLE_API_KEY2`, … (or single `GOOGLE_API_KEY`); rotates automatically on error.
- **GitHub context cache**: in-memory, configurable TTL (default 300 s) — avoids GitHub API rate limits.
- **AI fallback**: if Gemini fails, fuzzy-matches user query against all stored interactions (threshold score > 75).
- **Non-blocking saves**: DB writes happen in daemon background threads so HTTP responses are never delayed.
- **In-memory DB cache**: interactions and stats are cached for 5 minutes to reduce Firestore/PG reads.
- **Firebase credentials**: loaded from `FIREBASE_SERVICE_ACCOUNT_JSON` secret (priority), then `firebase-key.json` local file, then application-default credentials.

## Gotchas

- `DATABASE_URL` is runtime-managed by Replit — do not set or override it in secrets or env vars.
- Gemini requires at least one API key secret (`GOOGLE_API_KEY` or `GOOGLE_API_KEY1`) to function. Without it the app starts fine but all chat requests fall back to the DB.
- Firebase is chosen as the active backend when `FIREBASE_PROJECT_ID` is set; the app logs the active backend on every startup.
- `firebase-key.json` contains a service account private key — it is present in the repo but should be rotated or replaced for production use.
- `monitoring.py` contains useful utilities (MetricsCollector, HealthMonitor, AlertManager) but its endpoints are not yet registered in `app/routes.py`.

## User preferences

- Keep docs accurate and in sync with the actual code — no phantom endpoints or wrong response shapes.
