# Ani — AI Assistant

> A context-aware AI chatbot built to showcase developer projects, handle professional inquiries, and automate portfolio interaction. Powered by Google Gemini 2.5 Flash.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![Gemini](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-8E75B2?style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask)
![Firebase](https://img.shields.io/badge/Firebase-Firestore-FFCA28?style=for-the-badge&logo=firebase)

---

## Key Features

- **Intelligent Persona** — Roleplays as "Ani," an AI assistant created by Cid Kageno (Shadow-Garden.inc).
- **Smart Key Rotation** — Automatically cycles through multiple Gemini API keys (`GOOGLE_API_KEY1`, `GOOGLE_API_KEY2`, …) to handle rate limits and maximise uptime.
- **Live GitHub Sync** — Fetches real-time profile, bio, and repository data from the GitHub API as context for every response.
- **In-memory Caching** — GitHub data is cached for 5 minutes (configurable) to avoid hitting API rate limits.
- **Fail-safe Fallback** — If Gemini is unavailable, Ani fuzzy-matches the user's question against previously stored interactions and returns the closest cached answer.
- **Dual Database Support** — Firebase Firestore is the primary store; Replit PostgreSQL is available as a fallback.
- **Non-blocking Saves** — Interactions are saved to the database in a background thread so HTTP responses are never delayed.

---

## Running on Replit

The project is configured to run automatically on Replit. The "Start application" workflow runs `python run.py`, which starts Flask on port 5000.

### Required secrets (set in the Replit Secrets tab)

| Secret | Description |
|--------|-------------|
| `GOOGLE_API_KEY` | Google Gemini API key — get one at [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| `GOOGLE_API_KEY1`, `GOOGLE_API_KEY2`, … | Optional additional keys for rotation |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Firebase service account JSON (stringified) — see [FIREBASE_SETUP.md](FIREBASE_SETUP.md) |

### Environment variables (already set in `.replit`)

| Variable | Value |
|----------|-------|
| `FIREBASE_PROJECT_ID` | `gen-lang-client-0109922552` |
| `FIREBASE_DATABASE_URL` | Firebase Realtime Database URL |

### Auto-provided by Replit

`DATABASE_URL`, `PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGPORT` — Replit's built-in PostgreSQL, used as the DB fallback when Firebase is unavailable.

---

## Local Development

If you want to run the project outside of Replit:

```bash
# Clone the repository
git clone https://github.com/cid-kageno-dev/Ani.git
cd Ani

# Install dependencies
pip install -r requirements.txt

# Set environment variables (copy and edit the example)
cp .env.example .env
# Add your GOOGLE_API_KEY and Firebase credentials to .env

# Start the dev server
python run.py
```

Server starts at `http://localhost:5000`.

For production use Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

---

## Project Structure

```
.
├── app/
│   ├── services/
│   │   ├── ai_service.py        # Gemini calls, GitHub fetching, key rotation
│   │   ├── db_service.py        # Firebase / PostgreSQL storage + fuzzy fallback
│   │   └── firebase_validator.py # Startup credential validation
│   ├── routes.py                # HTTP endpoints
│   ├── logger.py                # Coloured console logging
│   └── __init__.py              # Flask app factory + startup health checks
├── templates/
│   └── index.html               # Chat UI (Jinja2 + vanilla JS)
├── tests/                       # Pytest suite
├── docs/                        # API, monitoring, Swagger docs
├── scripts/                     # Helper scripts
├── config.py                    # Config loader (config.json + env vars)
├── config.json                  # App / server / database / GitHub settings
├── run.py                       # Entry point (dev server)
├── monitoring.py                # Metrics, health, and alert utilities
├── requirements.txt             # Runtime dependencies
└── requirements-dev.txt         # Dev/test dependencies
```

---

## Configuration

### config.json

Non-secret configuration lives in `config.json`:

```json
{
  "app": { "name": "Ani", "version": "1.0.0", "debug": true },
  "server": { "host": "0.0.0.0", "port": 5000, "threaded": true },
  "database": {
    "backend": "firebase",
    "firebase": {
      "project_id": "gen-lang-client-0109922552",
      "database_url": "...",
      "collection": "chat_interactions"
    }
  },
  "github": { "username": "cid-kageno-dev", "cache_ttl": 300 },
  "logging": { "level": "INFO" }
}
```

### Environment / Secret variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `GOOGLE_API_KEY` | Secret | Primary Gemini API key |
| `GOOGLE_API_KEY1` … `GOOGLE_API_KEYn` | Secret | Additional keys for rotation |
| `GEMINI_MODEL` | Env | Model name (default: `gemini-2.5-flash`) |
| `GEMINI_TEMP` | Env | Temperature 0.0–2.0 (default: `0.55`) |
| `GEMINI_MAX_TOKENS` | Env | Max output tokens (default: `512`) |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Secret | Full service account JSON as a string |
| `FIREBASE_PROJECT_ID` | Env | Firebase project ID |
| `FIREBASE_DATABASE_URL` | Env | Firebase Realtime Database URL |
| `DATABASE_URL` | Env (Replit managed) | PostgreSQL connection string |
| `LOG_LEVEL` | Env | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Chat web UI |
| `POST` | `/api/chat` | Send a message, get Ani's reply |
| `GET` | `/api/history` | Recent chat interactions (DB required) |
| `GET` | `/api/stats` | Aggregate usage statistics |
| `GET` | `/api/health` | Liveness check |

### POST /api/chat

```bash
curl -X POST /api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about your creator"}'
```

```json
{
  "response": "I'm Ani, an AI assistant created by Cid Kageno...",
  "source": "AI Response"
}
```

`source` is `"AI Response"` when Gemini answered, or `"Database"` when the fuzzy-match fallback was used.

### GET /api/history

```bash
curl "/api/history?limit=10"
```

```json
[
  {
    "id": "abc123",
    "user_query": "What projects has Cid built?",
    "ai_response": "Cid has built several projects...",
    "source": "AI Response",
    "created_at": "2026-05-19T01:57:55.000000"
  }
]
```

### GET /api/stats

```json
{
  "total": 42,
  "ai_responses": 39,
  "fallback_responses": 3,
  "first_interaction": "2026-05-17T10:00:00.000000",
  "last_interaction": "2026-05-19T01:57:55.000000"
}
```

Full API details: [docs/API.md](docs/API.md)

---

## How the AI Fallback Works

```
User message
    │
    ▼
Gemini (with live GitHub context)
    │ success → return "AI Response"
    │ fail ↓
Fuzzy match vs. stored interactions (thefuzz)
    │ score > 75 → return cached answer as "Database"
    │ score ≤ 75 ↓
Generic offline message
```

---

## Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific file
pytest tests/test_api_endpoints.py -v

# Unit tests only
pytest -m "not integration"
```

---

## Firebase Setup

See [FIREBASE_SETUP.md](FIREBASE_SETUP.md) for full details on configuring Firebase Firestore across environments.

**Firestore document structure:**
```
chat_interactions (collection)
└── {auto-id} (document)
    ├── user_query   : string
    ├── ai_response  : string
    ├── source       : "AI Response" | "Database"
    └── created_at   : timestamp
```

---

## Troubleshooting

### "No Gemini API keys found — AI responses will be unavailable"
Set `GOOGLE_API_KEY` (or `GOOGLE_API_KEY1`) in the Replit Secrets tab (or your `.env` file locally).

### Firebase shows ✗ on startup
Ensure `FIREBASE_SERVICE_ACCOUNT_JSON` is set as a secret with the full JSON string of your service account key. See [FIREBASE_SETUP.md](FIREBASE_SETUP.md).

### Port 5000 already in use (local only)
```bash
PORT=8080 python run.py
```

### CORS errors in browser
Flask-CORS is already configured and enabled on all routes. If you're hitting CORS issues from an external frontend, check that the `Origin` header matches what Flask-CORS allows.

---

## Roadmap

- [ ] Web UI improvements
- [ ] Voice chat support
- [ ] Multi-language support
- [ ] Rate limiting / abuse protection
- [ ] Analytics dashboard

---

## Author

**Cid Kageno** — [GitHub](https://github.com/cid-kageno-dev) | [Website](https://cid-kageno.top)

Meet **Ani** — your smart portfolio AI assistant.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

**Last Updated:** May 19, 2026
