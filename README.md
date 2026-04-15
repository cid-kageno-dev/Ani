# Ani — AI Companion Backend

A production-ready AI companion backend built with **Node.js** and **Express**.
Supports multiple LLM providers — Ollama (local), Google Gemini (with automatic API key rotation), and OpenAI — with per-user memory, personality, and a clean modular architecture.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
  - [Option A — Local (Node.js)](#option-a--local-nodejs)
  - [Option B — Docker](#option-b--docker)
- [Configuration](#configuration)
- [LLM Providers](#llm-providers)
  - [Ollama (default)](#ollama-default)
  - [Google Gemini + Key Rotation](#google-gemini--key-rotation)
  - [OpenAI](#openai)
- [API Reference](#api-reference)
  - [POST /chat](#post-chat)
  - [POST /persona](#post-persona)
  - [GET /history](#get-history)
  - [DELETE /history](#delete-history)
  - [GET /health](#get-health)
- [Extending the Backend](#extending-the-backend)
- [Architecture Notes](#architecture-notes)

---

## Features

- **Multi-provider LLM** — switch between Ollama, Gemini, and OpenAI via one env var
- **Gemini key rotation** — automatically rotates through multiple API keys on rate-limit errors
- **Per-user memory** — configurable conversation history per user, swappable to Redis/Mongo
- **Per-user personality** — custom system prompts per user, with a sensible default
- **Structured prompt builder** — consistent `System / Conversation / User / Assistant` format
- **Rate limiting** — in-memory sliding-window limiter, no dependencies
- **Colorized timed logging** — `INFO / WARN / ERROR / HTTP` with response times
- **Global error handling** — classifies Axios network/timeout errors into clean HTTP responses
- **Docker-ready** — multi-stage `Dockerfile` with minimal production image

---

## Project Structure

```
.
├── src/
│   ├── server.js                     # Entry point, graceful shutdown
│   ├── app.js                        # Express app, middleware pipeline, request timing
│   ├── config/
│   │   └── index.js                  # All configuration loaded from .env
│   ├── controllers/
│   │   ├── chat.controller.js        # POST /chat
│   │   ├── persona.controller.js     # POST /persona
│   │   └── history.controller.js     # GET + DELETE /history
│   ├── routes/
│   │   ├── index.js                  # Route aggregator + GET /health
│   │   ├── chat.routes.js
│   │   ├── persona.routes.js
│   │   └── history.routes.js
│   ├── services/
│   │   ├── llm/
│   │   │   ├── index.js              # Provider factory + optional fallback
│   │   │   ├── ollama.provider.js    # Ollama /api/generate via Axios
│   │   │   ├── gemini.provider.js    # Gemini REST API with key rotation
│   │   │   └── openai.provider.js    # OpenAI chat completions via Axios
│   │   ├── memory/
│   │   │   ├── memory.interface.js   # Swappable interface contract
│   │   │   └── memory.local.js       # In-memory Map (default)
│   │   └── persona/
│   │       └── persona.service.js    # Per-user personality store
│   ├── middlewares/
│   │   ├── rateLimiter.js            # In-memory sliding-window rate limiter
│   │   ├── validate.js               # requireBody / requireQuery helpers
│   │   └── errorHandler.js           # Global error handler with Axios classification
│   └── utils/
│       ├── keyRotator.js             # Round-robin key rotator with exhaustion tracking
│       ├── logger.js                 # Colorized structured logger
│       └── promptBuilder.js          # Prompt formatter
├── Dockerfile
├── .dockerignore
├── .env.example
├── package.json
└── README.md
```

---

## Quick Start

### Option A — Local (Node.js)

**1. Install dependencies**

```bash
npm install
```

**2. Configure environment**

```bash
cp .env.example .env
```

Edit `.env` — at minimum set your provider and credentials (see [Configuration](#configuration)).

**3. Start the server**

```bash
npm start
```

The server runs on `http://localhost:3000` by default.

---

### Option B — Docker

**Build the image**

```bash
docker build -t ani-backend .
```

**Run the container**

```bash
docker run -p 3000:3000 --env-file .env ani-backend
```

---

## Configuration

Copy `.env.example` to `.env` and edit the values. All options with their defaults:

```env
# ─────────────────────────────────────────────
#  Ani — AI Companion Backend  |  .env
# ─────────────────────────────────────────────

# Server
PORT=3000

# ── LLM Provider ──────────────────────────────
# Choose: ollama | gemini | openai
LLM_PROVIDER=ollama

# Fall back to OpenAI if primary provider fails
USE_FALLBACK=false

# ── Ollama ────────────────────────────────────
OLLAMA_URL=http://localhost:11434
MODEL_NAME=mistral

# ── Google Gemini ─────────────────────────────
# Add as many keys as needed — rotated automatically on rate-limit errors
GOOGLE_API_KEY1=AIzaSyD-YourFirstKey...
GOOGLE_API_KEY2=AIzaSyD-YourSecondKey...
GOOGLE_API_KEY3=AIzaSyD-YourThirdKey...
GEMINI_MODEL=gemini-2.0-flash

# ── OpenAI (fallback) ─────────────────────────
OPENAI_API_KEY=
OPENAI_MODEL=gpt-3.5-turbo

# ── Memory ────────────────────────────────────
MEMORY_LIMIT=20

# ── Rate Limiter ──────────────────────────────
RATE_LIMIT_WINDOW=60000
RATE_LIMIT_MAX=30

# ── LLM Request ───────────────────────────────
LLM_TIMEOUT=30000
```

| Variable | Default | Description |
|---|---|---|
| `PORT` | `3000` | HTTP port |
| `LLM_PROVIDER` | `ollama` | Active provider: `ollama`, `gemini`, `openai` |
| `USE_FALLBACK` | `false` | Fall back to OpenAI if primary provider fails |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server base URL |
| `MODEL_NAME` | `mistral` | Ollama model name |
| `GOOGLE_API_KEY1..N` | — | Gemini API keys, rotated on `429` / `403` |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model name |
| `OPENAI_API_KEY` | — | OpenAI secret key |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | OpenAI model name |
| `MEMORY_LIMIT` | `20` | Max messages stored per user |
| `RATE_LIMIT_WINDOW` | `60000` | Rate limiter window in ms |
| `RATE_LIMIT_MAX` | `30` | Max requests per IP per window |
| `LLM_TIMEOUT` | `30000` | LLM request timeout in ms |

---

## LLM Providers

### Ollama (default)

Runs fully locally. No API keys required.

**Install Ollama**

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh
```

**Pull a model**

```bash
ollama pull mistral
# or: llama3, phi3, gemma, codellama, ...
```

**Start Ollama**

```bash
ollama serve
```

**Activate in `.env`**

```env
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
MODEL_NAME=mistral
```

---

### Google Gemini + Key Rotation

Uses the Gemini REST API directly via Axios. Supports automatic rotation across multiple API keys to bypass rate limits.

**How key rotation works:**
Each request uses the current key. If a `429 Too Many Requests` or `403 Forbidden` is returned, the key is marked exhausted and the next available key is tried — transparently, within the same request. Once a request succeeds, the exhaustion set is cleared. If all keys are exhausted, the cycle resets.

**Activate in `.env`**

```env
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash
GOOGLE_API_KEY1=AIzaSyD-YourFirstKey...
GOOGLE_API_KEY2=AIzaSyD-YourSecondKey...
GOOGLE_API_KEY3=AIzaSyD-YourThirdKey...
```

Add as many keys as needed. The system detects them sequentially (`KEY1`, `KEY2`, ...).

---

### OpenAI

Can be used as the primary provider or as an automatic fallback when the primary fails.
Supports the same key rotation system as Gemini — add as many keys as you need.

**As primary with key rotation:**

```env
LLM_PROVIDER=openai
OPENAI_API_KEY1=sk-YourFirstKey...
OPENAI_API_KEY2=sk-YourSecondKey...
OPENAI_API_KEY3=sk-YourThirdKey...
OPENAI_MODEL=gpt-3.5-turbo
```

**As fallback with key rotation:**

```env
LLM_PROVIDER=ollama   # or gemini
USE_FALLBACK=true
OPENAI_API_KEY1=sk-YourFirstKey...
OPENAI_API_KEY2=sk-YourSecondKey...
```

A single `OPENAI_API_KEY` (without a number) is also accepted for backwards compatibility.

---

## API Reference

All responses use a consistent envelope:

```json
{ "success": true,  "data":  { ... } }
{ "success": false, "error": "..." }
```

---

### POST /chat

Send a message to Ani and receive a response. Memory is updated automatically.

**Request body**

| Field | Type | Required | Description |
|---|---|---|---|
| `userId` | string | yes | Unique identifier for the user session |
| `message` | string | yes | The user's message |

```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{"userId": "alice", "message": "Hello, who are you?"}'
```

**Response**

```json
{
  "success": true,
  "data": {
    "response": "Hi! I'm Ani, your AI companion. How can I help you today?"
  }
}
```

---

### POST /persona

Set a custom personality for a user. Injected as the system prompt on every request for that user.

**Request body**

| Field | Type | Required | Description |
|---|---|---|---|
| `userId` | string | yes | Target user |
| `personality` | string | yes | Personality description |

```bash
curl -X POST http://localhost:3000/persona \
  -H "Content-Type: application/json" \
  -d '{"userId": "alice", "personality": "Ani is a sharp, tactical AI that speaks in short, precise sentences."}'
```

**Response**

```json
{
  "success": true,
  "data": {
    "userId": "alice",
    "personality": "Ani is a sharp, tactical AI that speaks in short, precise sentences."
  }
}
```

---

### GET /history

Retrieve full conversation history for a user.

| Param | Type | Required |
|---|---|---|
| `userId` | query string | yes |

```bash
curl "http://localhost:3000/history?userId=alice"
```

**Response**

```json
{
  "success": true,
  "data": {
    "userId": "alice",
    "history": [
      { "role": "user",      "content": "Hello, who are you?" },
      { "role": "assistant", "content": "Hi! I'm Ani..." }
    ]
  }
}
```

---

### DELETE /history

Clear all conversation history for a user.

| Param | Type | Required |
|---|---|---|
| `userId` | query string | yes |

```bash
curl -X DELETE "http://localhost:3000/history?userId=alice"
```

**Response**

```json
{
  "success": true,
  "data": { "userId": "alice", "cleared": true }
}
```

---

### GET /health

Check that the server is running.

```bash
curl http://localhost:3000/health
```

**Response**

```json
{
  "success": true,
  "data": { "status": "ok", "uptime": 42.3 }
}
```

---

## Extending the Backend

### Swap the memory backend

Implement the contract in `src/services/memory/memory.interface.js` (`get`, `append`, `clear`), then replace the import in the controllers:

```js
// Before
const memory = require("../services/memory/memory.local");

// After (your Redis / Mongo implementation)
const memory = require("../services/memory/memory.redis");
```

No other code changes needed.

### Add a new LLM provider

1. Create `src/services/llm/myprovider.provider.js` and export `async generate(prompt)`.
2. Register it in `src/services/llm/index.js`:

```js
const registry = {
  ollama:     () => require("./ollama.provider"),
  gemini:     () => require("./gemini.provider"),
  openai:     () => require("./openai.provider"),
  myprovider: () => require("./myprovider.provider"), // add here
};
```

3. Set `LLM_PROVIDER=myprovider` in `.env`.

---

## Architecture Notes

- **No database dependency** — memory is in-process by default; the interface makes it trivial to plug in any store.
- **No frontend** — pure REST API, designed to be consumed by any client.
- **No TypeScript** — plain JavaScript throughout for simplicity.
- **Prompt format** — every request builds a structured prompt:

```
System:
{personality}

Conversation:
User: ...
Assistant: ...

User: {current message}
Assistant:
```
