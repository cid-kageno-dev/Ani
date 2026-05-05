# Ani — AI Assistant

A Flask-based context-aware chatbot that answers questions as "Ani", fetching live GitHub profile data and using Google Gemini for responses, with PostgreSQL fallback storage and fuzzy-match cached answers.

## Run & Operate

- **Run**: `python run.py` (port 5000)
- **Required secrets**: `GOOGLE_API_KEY` (Google Gemini API key)
- **Auto-provided**: `DATABASE_URL`, `PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGPORT`

## Stack

- Python 3.12
- Flask + Flask-CORS
- google-genai (Gemini 2.5 Flash)
- psycopg2-binary (PostgreSQL via Replit DB)
- firebase-admin (optional Firebase/Firestore backend)
- thefuzz (fuzzy fallback matching)
- gunicorn (for production deployment)

## Where things live

- `run.py` — entry point
- `config.py` — all config/env loading
- `app/__init__.py` — Flask app factory
- `app/routes.py` — HTTP endpoints (`/`, `/chat`, `/history`, `/stats`, `/health`)
- `app/services/ai_service.py` — Gemini calls + GitHub context fetching
- `app/services/db_service.py` — PostgreSQL/Firebase storage, fallback answers, stats
- `app/logger.py` — colored console logging
- `templates/index.html` — chat UI (Jinja2 + vanilla JS)

## Architecture decisions

- DB backend auto-detected: Firebase if configured, else Postgres if `DATABASE_URL` set
- Gemini API key rotation: supports `GOOGLE_API_KEY1`, `GOOGLE_API_KEY2`, ... or single `GOOGLE_API_KEY`
- GitHub context is cached in-memory with configurable TTL (default 300s) to avoid rate limits
- AI fallback: if Gemini fails, fuzzy-matches user query against stored interactions (threshold: score > 75)
- DB interactions saved in background threads to avoid blocking HTTP responses

## Product

- Chat UI served at `/` — users can ask questions about Cid Kageno
- Ani answers using live GitHub profile, repos, and README as context
- Falls back to cached DB answers if Gemini is unavailable
- History and stats available via `/history` and `/stats`

## User preferences

_Populate as you build_

## Gotchas

- `google.generativeai` package shows a FutureWarning (deprecated); works fine for now but should be migrated to `google.genai` eventually
- Firebase is optional — app works fully with just Postgres (Replit's built-in DB)
- `DATABASE_URL` is runtime-managed by Replit — do not override it

## Pointers

- [Gemini API keys](https://aistudio.google.com/apikey)
- [google-generativeai migration guide](https://github.com/google-gemini/deprecated-generative-ai-python/blob/main/README.md)
