# Ani — AI Companion Backend

A clean, production-ready AI companion backend built with Node.js and Express.
Uses a local LLM via **Ollama** as the primary provider, with an optional OpenAI fallback.

---

## Features

- Local LLM via Ollama (no cloud required by default)
- Per-user conversation memory (in-memory, swappable)
- Per-user personality engine
- Modular LLM provider abstraction (Ollama / OpenAI)
- Rate limiting, request validation, global error handling
- Clean REST API with consistent JSON responses

---

## Project Structure

```
src/
├── app.js                        # Express app setup
├── server.js                     # Entry point
├── config/
│   └── index.js                  # All config from .env
├── controllers/
│   ├── chat.controller.js
│   ├── persona.controller.js
│   └── history.controller.js
├── routes/
│   ├── index.js
│   ├── chat.routes.js
│   ├── persona.routes.js
│   └── history.routes.js
├── services/
│   ├── llm/
│   │   ├── index.js              # Provider router
│   │   ├── ollama.provider.js
│   │   └── openai.provider.js
│   ├── memory/
│   │   ├── memory.interface.js   # Swappable interface
│   │   └── memory.local.js       # In-memory Map implementation
│   └── persona/
│       └── persona.service.js
├── middlewares/
│   ├── rateLimiter.js
│   ├── validate.js
│   └── errorHandler.js
└── utils/
    ├── logger.js
    └── promptBuilder.js
```

---

## Setup

### 1. Install Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Then pull a model
ollama pull mistral
```

### 2. Start Ollama

```bash
ollama serve
```

Ollama runs on `http://localhost:11434` by default.

### 3. Install dependencies

```bash
npm install
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` as needed:

```env
PORT=3000
OLLAMA_URL=http://localhost:11434
MODEL_NAME=mistral
USE_FALLBACK=false
OPENAI_API_KEY=
MEMORY_LIMIT=20
RATE_LIMIT_WINDOW=60000
RATE_LIMIT_MAX=30
LLM_TIMEOUT=30000
```

### 5. Start the server

```bash
npm start
```

---

## API Reference

All responses follow this structure:

```json
{ "success": true, "data": { ... } }
{ "success": false, "error": "..." }
```

---

### POST /chat

Send a message and receive a response from Ani.

**Body:**
```json
{ "userId": "alice", "message": "Hello, who are you?" }
```

**Response:**
```json
{ "success": true, "data": { "response": "Hi! I'm Ani, your AI companion..." } }
```

**curl:**
```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{"userId": "alice", "message": "Hello, who are you?"}'
```

---

### POST /persona

Set a custom personality for a user.

**Body:**
```json
{ "userId": "alice", "personality": "Ani is a witty, sarcastic assistant who speaks in riddles." }
```

**curl:**
```bash
curl -X POST http://localhost:3000/persona \
  -H "Content-Type: application/json" \
  -d '{"userId": "alice", "personality": "Ani is a witty, sarcastic assistant who speaks in riddles."}'
```

---

### GET /history?userId=

Retrieve conversation history for a user.

**curl:**
```bash
curl "http://localhost:3000/history?userId=alice"
```

---

### DELETE /history?userId=

Clear conversation history for a user.

**curl:**
```bash
curl -X DELETE "http://localhost:3000/history?userId=alice"
```

---

### GET /health

Check server health.

**curl:**
```bash
curl http://localhost:3000/health
```

---

## Switching LLM Provider

Set `USE_FALLBACK=true` in `.env` to enable OpenAI as the fallback when Ollama fails.
Set `OPENAI_API_KEY` to your key.

To switch models, change `MODEL_NAME` in `.env` (e.g., `llama3`, `phi3`, `gemma`).

---

## Extending Memory

To swap to Redis or MongoDB, implement the interface in `src/services/memory/memory.interface.js`
and replace the import in the controllers with your new implementation. No other code changes needed.
