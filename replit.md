# Ani - AI Assistant

A context-aware AI chatbot that showcases developer projects, handles professional inquiries, and automates portfolio interactions. Developed by Cid Kageno, maintained by Shadow-Garden.inc.

## Architecture

- **Backend:** Python / Flask (port 5000, `0.0.0.0`)
- **Frontend:** Jinja2 HTML template (`templates/index.html`)
- **AI:** Google Gemini (`gemini-2.5-flash`) via `google-generativeai`
- **Database:** PostgreSQL (Replit built-in) via `psycopg2`
- **Entry point:** `run.py` → `app/__init__.py` (factory pattern)

## Project Layout

```
run.py                      # App entry point
config.py                   # API key rotation config
app/
  __init__.py               # Flask app factory (sets template_folder to root /templates)
  routes.py                 # Routes: GET /, POST /chat, GET /history
  services/
    ai_service.py           # Gemini AI + GitHub data fetching + key rotation
    db_service.py           # PostgreSQL: save_interaction, get_fallback_answer, get_recent_interactions
    sheet_service.py        # Legacy Google Sheets service (kept for reference)
    github_service.py       # GitHub data helpers
templates/
  index.html                # Chat UI (dark theme, vanilla JS)
requirements.txt
```

## Database Schema

**Table: `chat_interactions`**
| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | Auto-increment |
| user_query | TEXT | User's message |
| ai_response | TEXT | Ani's response |
| source | VARCHAR(50) | "AI Response" or "Database" |
| created_at | TIMESTAMP | Defaults to NOW() |

## API Endpoints

- `GET /` — Serves the chat UI
- `POST /chat` — Accepts `{"message": "..."}`, returns `{"response": "...", "source": "..."}`
- `GET /history?limit=20` — Returns recent chat interactions from the database

## Key Features

- **API Key Rotation:** Cycles through `GOOGLE_API_KEY1`, `GOOGLE_API_KEY2`, etc.
- **GitHub Live Data:** Fetches real-time repo and profile data (5-minute cache)
- **DB Fallback:** When Gemini is unavailable, fuzzy-matches past interactions from PostgreSQL
- **Background Saving:** All interactions are saved to the DB in a background thread (non-blocking)

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `GOOGLE_API_KEY1` | Primary Gemini API key (add more as KEY2, KEY3, etc.) |
| `DATABASE_URL` | PostgreSQL connection string (auto-set by Replit) |
| `SHEET_NAME` | (Optional) Legacy Google Sheets name |
| `GOOGLE_SHEET_CREDS` | (Optional) Path to Google Sheets credentials JSON |

## Workflow

- **Start application:** `python run.py` → port 5000 (webview)
