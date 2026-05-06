# Ani — AI Assistant

A Flask-based context-aware chatbot that answers questions as "Ani", fetching live GitHub profile data and using Google Gemini for responses, with Firebase Firestore as the primary store and PostgreSQL as a fallback.

## Run & Operate

- **Run**: `python run.py` (port 5000)
- **Required secrets**: `GOOGLE_API_KEY1` (Google Gemini API key — get one at https://aistudio.google.com/apikey)
- **Firebase secrets**: `FIREBASE_SERVICE_ACCOUNT_JSON` (JSON contents of service account key)
- **Firebase env vars**: `FIREBASE_PROJECT_ID`, `FIREBASE_DATABASE_URL` (set in shared env)
- **Auto-provided by Replit**: `DATABASE_URL`, `PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGPORT`

## Stack

- Python 3.12
- Flask + Flask-CORS
- google-genai (Gemini 2.5 Flash)
- psycopg2-binary (PostgreSQL via Replit built-in DB)
- firebase-admin (Firestore — primary DB backend)
- thefuzz (fuzzy fallback matching)
- gunicorn (production WSGI server)

## Where things live

- `run.py` — entry point
- `config.py` — all config/env loading
- `app/__init__.py` — Flask app factory + connection health checks
- `app/routes.py` — HTTP endpoints (`/`, `/chat`, `/history`, `/stats`, `/health`)
- `app/services/ai_service.py` — Gemini calls + GitHub context fetching + key rotation
- `app/services/db_service.py` — Firebase/PostgreSQL storage, fuzzy fallback answers, stats
- `app/logger.py` — colored console logging
- `templates/index.html` — chat UI (Jinja2 + vanilla JS)
- `firebase-key.json` — Firebase service account key (not gitignored; also stored as secret)

## Architecture decisions

- DB backend auto-detected: Firebase if configured (preferred), else PostgreSQL if `DATABASE_URL` set
- Gemini API key rotation: supports `GOOGLE_API_KEY1`, `GOOGLE_API_KEY2`, ... or single `GOOGLE_API_KEY`
- GitHub context is cached in-memory with configurable TTL (default 300s) to avoid rate limits
- AI fallback: if Gemini fails, fuzzy-matches user query against stored interactions (threshold: score > 75)
- DB interactions saved in background threads to avoid blocking HTTP responses
- Firebase credentials loaded from `FIREBASE_SERVICE_ACCOUNT_JSON` secret (all envs) with `firebase-key.json` as local fallback

## Product

- Chat UI at `/` — users ask questions about Cid Kageno (Shadow-Garden.inc)
- Ani answers using live GitHub profile, repos, and README as context
- Falls back to cached DB answers if Gemini is unavailable
- History and stats available via `/history` and `/stats`
- Health check at `/health`

## Gotchas

- Firebase is the active backend when `FIREBASE_PROJECT_ID` is set; PostgreSQL is used otherwise
- `DATABASE_URL` is runtime-managed by Replit — do not override it
- Gemini requires at least one `GOOGLE_API_KEY1` secret to function; without it the app falls back to DB only

## Pointers

- [Gemini API keys](https://aistudio.google.com/apikey)
- [Firebase Console](https://console.firebase.google.com/)
