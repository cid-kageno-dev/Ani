# Ani — AI Assistant (Template)

A cloneable Flask chatbot template. Clone it, set a handful of env vars, and you have a personalised AI assistant that answers questions about you — using your live GitHub profile, Gemini AI, and a persistent database fallback.

---

## Quick-start (5 minutes)

### 1 — Set your identity

Add these secrets in Replit (**Tools → Secrets**) or copy `.env.example` to `.env`:

| Secret | What it is |
|---|---|
| `ASSISTANT_NAME` | Your AI's name, e.g. `Nova` |
| `OWNER_NAME` | Your full name, e.g. `Jane Smith` |
| `ORG_NAME` | Organisation or team (optional) |
| `GITHUB_USERNAME` | Your GitHub handle |
| `OWNER_EMAIL` | Contact email (optional) |
| `OWNER_WEBSITE` | Portfolio URL (optional) |
| `OWNER_FACEBOOK` | Facebook URL (optional) |

### 2 — Add a Gemini API key

Get a free key at <https://aistudio.google.com/apikey> and add it as:

```
GOOGLE_API_KEY1=your-key-here
```

Add `GOOGLE_API_KEY2`, `GOOGLE_API_KEY3`, … for automatic key rotation on quota exhaustion.

### 3 — Pick a database

**Option A — Firebase (recommended)**
1. Create a project at <https://console.firebase.google.com/>
2. Go to Project Settings → Service Accounts → Generate new private key
3. Paste the entire JSON as the `FIREBASE_SERVICE_ACCOUNT_JSON` secret
4. Set `FIREBASE_PROJECT_ID` to your project ID

**Option B — PostgreSQL**
- On Replit: `DATABASE_URL` is provisioned automatically — nothing to do.
- Elsewhere: set `DATABASE_URL` to your connection string.

**Option C — Both (mirror)**  
Set both Firebase and `RENDER_DATABASE_URL` to mirror every interaction to a Render PostgreSQL database.

### 4 — Run

```
python run.py
```

---

## All configurable env vars

### Identity
| Variable | Default | Description |
|---|---|---|
| `ASSISTANT_NAME` | `Ani` | AI persona name shown in the UI |
| `OWNER_NAME` | `Your Name` | Person the assistant represents |
| `ORG_NAME` | _(blank)_ | Organisation shown in the header |
| `OWNER_EMAIL` | _(blank)_ | Included in AI context |
| `OWNER_WEBSITE` | _(blank)_ | Included in AI context |
| `OWNER_FACEBOOK` | _(blank)_ | Included in AI context |
| `OWNER_TAGLINE` | _(generic)_ | Sidebar description |
| `OWNER_FOOTER_NOTE` | _(generic)_ | Footer text in sidebar |
| `CHAT_SUGGESTIONS` | 4 defaults | Comma-separated quick-ask chips |

### GitHub
| Variable | Default | Description |
|---|---|---|
| `GITHUB_USERNAME` | _(blank)_ | Handle for live profile/repo fetch |
| `GITHUB_CACHE_TTL` | `300` | Cache lifetime in seconds |

### Gemini
| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY1` | — | Required. Add KEY2, KEY3 for rotation |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Model name |
| `GEMINI_TEMP` | `0.55` | Response temperature |
| `GEMINI_MAX_TOKENS` | `512` | Max tokens per response |

### Database
| Variable | Default | Description |
|---|---|---|
| `DATABASE_BACKEND` | `auto` | `auto` / `firebase` / `postgres` |
| `DATABASE_URL` | _(Replit auto)_ | Primary PostgreSQL URL |
| `RENDER_DATABASE_URL` | _(blank)_ | Optional Render mirror URL |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | — | Full service account JSON |
| `FIREBASE_PROJECT_ID` | — | Firebase project ID |
| `FIREBASE_DATABASE_URL` | — | Realtime DB URL |
| `FIREBASE_COLLECTION` | `chat_interactions` | Firestore collection name |

### App
| Variable | Default | Description |
|---|---|---|
| `MAX_MESSAGE_LENGTH` | `1200` | Character limit per message |
| `LOG_LEVEL` | `DEBUG` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `FLASK_DEBUG` | `true` | Set `false` in production |

---

## Stack

- Python 3.12
- Flask + Flask-CORS
- google-genai (Gemini 2.5 Flash streaming)
- firebase-admin (Firestore — primary DB)
- psycopg2-binary (PostgreSQL — fallback / mirror)
- thefuzz (fuzzy DB fallback matching)
- gunicorn (production WSGI)

## Where things live

| File | Purpose |
|---|---|
| `run.py` | Entry point |
| `config/__init__.py` | All env vars and identity config |
| `app/__init__.py` | Flask factory + boot display |
| `app/routes.py` | HTTP endpoints |
| `app/services/ai_service.py` | Gemini calls, key rotation, GitHub fetch |
| `app/services/db_service.py` | Firebase / PostgreSQL / Render storage |
| `app/logger.py` | Coloured console logging |
| `templates/index.html` | Chat UI (Jinja2 + vanilla JS) |
| `gunicorn.conf.py` | Production WSGI config |
| `.env.example` | Template for all env vars |

## Endpoints

| Route | Method | Description |
|---|---|---|
| `/` | GET | Chat UI |
| `/chat` | POST | Single AI response (JSON) |
| `/chat/stream` | POST | Streaming SSE response |
| `/history` | GET | Recent interactions (`?limit=N`) |
| `/stats` | GET | Interaction statistics |
| `/health` | GET | Health check |

## Architecture

- DB backend auto-detected: Firebase preferred when `FIREBASE_PROJECT_ID` is set, else PostgreSQL
- Gemini key rotation: cycles through `GOOGLE_API_KEY1` → `GOOGLE_API_KEY2` → … on quota error
- GitHub context cached in-memory with configurable TTL (default 300 s)
- AI fallback: if Gemini fails, fuzzy-matches query against stored interactions (threshold: score > 75)
- DB saves run in background threads; Render mirror runs in its own parallel thread
- All personal info (name, email, links, suggestions) comes from env vars — zero hardcoding
