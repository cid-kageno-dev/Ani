# Ani — AI Companion Backend

A production-ready AI companion backend built with Node.js and Express.
Supports Ollama, Google Gemini (with key rotation), and OpenAI as LLM providers.

## Architecture

- **Backend:** Node.js / Express (port 5000 on Replit, 3000 locally)
- **Frontend:** None (pure REST API)
- **LLM:** Configurable — Ollama (default) | Gemini (key rotation) | OpenAI (fallback)
- **Memory:** In-memory Map per userId (swappable via interface)
- **Entry point:** `src/server.js`

## Project Layout

```
src/
  server.js                     # Entry point + graceful shutdown
  app.js                        # Express app, middleware pipeline, request timing
  config/
    index.js                    # All config from .env (includes Google key rotation loader)
  controllers/
    chat.controller.js          # POST /chat
    persona.controller.js       # POST /persona
    history.controller.js       # GET /history, DELETE /history
  routes/
    index.js                    # Route aggregator + GET /health
    chat.routes.js
    persona.routes.js
    history.routes.js
  services/
    llm/
      index.js                  # Provider factory (primary → optional OpenAI fallback)
      ollama.provider.js        # Ollama /api/generate via Axios
      gemini.provider.js        # Gemini REST API with KeyRotator
      openai.provider.js        # OpenAI chat completions via Axios
    memory/
      memory.interface.js       # Interface contract for swappable memory backends
      memory.local.js           # In-memory Map implementation
    persona/
      persona.service.js        # Per-user personality store (default provided)
  middlewares/
    rateLimiter.js              # In-memory rate limiter (window + max hits)
    validate.js                 # requireBody / requireQuery field validators
    errorHandler.js             # Global error handler with Axios error classification
  utils/
    keyRotator.js               # Round-robin key rotator with exhaustion tracking
    logger.js                   # Colorized, timed structured logger (INFO/WARN/ERROR/HTTP)
    promptBuilder.js            # System → Conversation → User → Assistant: formatter
```

## API Endpoints

- `POST /chat`             — `{ userId, message }` → `{ success, data: { response } }`
- `POST /persona`          — `{ userId, personality }` → updates per-user personality
- `GET /history?userId=`   — returns full conversation history for a user
- `DELETE /history?userId=`— clears conversation history for a user
- `GET /health`            — `{ success, data: { status, uptime } }`

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | `3000` | Server port (set to 5000 on Replit) |
| `LLM_PROVIDER` | `ollama` | Active provider: `ollama`, `gemini`, `openai` |
| `USE_FALLBACK` | `false` | Fall back to OpenAI if primary fails |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server base URL |
| `MODEL_NAME` | `mistral` | Ollama model |
| `GOOGLE_API_KEY1..N` | — | Gemini API keys (auto-rotated on 429/403) |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model name |
| `OPENAI_API_KEY` | — | OpenAI key (only needed if fallback enabled) |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | OpenAI model |
| `MEMORY_LIMIT` | `20` | Max messages per user session |
| `RATE_LIMIT_WINDOW` | `60000` | Rate limiter window in ms |
| `RATE_LIMIT_MAX` | `30` | Max requests per IP per window |
| `LLM_TIMEOUT` | `30000` | LLM request timeout in ms |

## Workflow

- **Start application:** `PORT=5000 node src/server.js` → port 5000 (webview)

## Key Design Decisions

- **Key rotation:** `KeyRotator` marks exhausted keys per request cycle and resets after success, enabling seamless rotation across multiple Gemini API keys.
- **Provider factory:** `src/services/llm/index.js` resolves providers by name from a registry — add new providers by creating a file and registering it.
- **Swappable memory:** Implement `MemoryInterface` and replace the import in controllers to use Redis, MongoDB, or any other store without touching business logic.
