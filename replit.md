# Ani — AI Companion Backend

A production-ready AI companion backend built with Node.js and Express.
Uses Ollama as the primary LLM provider with an optional OpenAI fallback.

## Architecture

- **Backend:** Node.js / Express (port 5000 on Replit, 3000 locally)
- **Frontend:** None (pure REST API)
- **LLM:** Ollama (primary) → OpenAI (optional fallback)
- **Memory:** In-memory Map per userId (swappable via interface)
- **Entry point:** `src/server.js`

## Project Layout

```
src/
  server.js                     # Entry point
  app.js                        # Express app + middleware setup
  config/
    index.js                    # All config loaded from .env
  controllers/
    chat.controller.js          # POST /chat
    persona.controller.js       # POST /persona
    history.controller.js       # GET /history, DELETE /history
  routes/
    index.js                    # Route aggregator + /health
    chat.routes.js
    persona.routes.js
    history.routes.js
  services/
    llm/
      index.js                  # Provider router (Ollama → OpenAI fallback)
      ollama.provider.js        # Ollama POST /api/generate
      openai.provider.js        # OpenAI chat completions
    memory/
      memory.interface.js       # Swappable interface contract
      memory.local.js           # In-memory Map implementation
    persona/
      persona.service.js        # Per-user personality store
  middlewares/
    rateLimiter.js              # Simple in-memory rate limiter
    validate.js                 # requireBody / requireQuery helpers
    errorHandler.js             # Global Express error handler
  utils/
    logger.js                   # Minimal structured logger
    promptBuilder.js            # Structured prompt formatter
```

## API Endpoints

- `POST /chat` — `{ userId, message }` → `{ success, data: { response } }`
- `POST /persona` — `{ userId, personality }` → updates per-user personality
- `GET /history?userId=` — returns conversation history for a user
- `DELETE /history?userId=` — clears conversation history for a user
- `GET /health` — server health check

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | `3000` | Server port (set to 5000 on Replit) |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `MODEL_NAME` | `mistral` | Ollama model to use |
| `USE_FALLBACK` | `false` | Enable OpenAI fallback if Ollama fails |
| `OPENAI_API_KEY` | `` | OpenAI key (only needed if USE_FALLBACK=true) |
| `MEMORY_LIMIT` | `20` | Max messages kept per user |
| `RATE_LIMIT_WINDOW` | `60000` | Rate limit window in ms |
| `RATE_LIMIT_MAX` | `30` | Max requests per window per IP |
| `LLM_TIMEOUT` | `30000` | LLM request timeout in ms |

## Workflow

- **Start application:** `PORT=5000 node src/server.js` → port 5000 (webview)

## Extending

- **Swap memory backend:** Implement `src/services/memory/memory.interface.js` and replace the import in controllers.
- **Add LLM provider:** Create a new provider in `src/services/llm/`, import it in `index.js`.
- **Add routes:** Add controller + route file, register in `src/routes/index.js`.
