# Ani API Documentation

## Overview

Ani exposes a small REST API for chat, history, stats, and health. All endpoints are served from the same Flask server that hosts the chat UI.

**Base URL (Replit):** `https://<your-repl>.replit.app`  
**Base URL (local):** `http://localhost:5000`

---

## Endpoints

### 1. Health Check

```http
GET /api/health
```

Returns a simple liveness response. Use this to confirm the server is up.

**Response `200 OK`:**
```json
{
  "status": "ok"
}
```

**Example:**
```bash
curl https://<your-repl>.replit.app/api/health
```

---

### 2. Chat with Ani

```http
POST /api/chat
Content-Type: application/json
```

Send a message and receive a response from Ani. Ani first tries to answer via Google Gemini (using live GitHub context). If Gemini is unavailable, it falls back to fuzzy-matching against previously stored interactions in the database.

**Request body:**
```json
{
  "message": "Tell me about your creator"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | The user's question or message |

**Response `200 OK`:**
```json
{
  "response": "I'm Ani, an AI assistant created by Cid Kageno...",
  "source": "AI Response"
}
```

| Field | Values | Description |
|-------|--------|-------------|
| `response` | string | Ani's reply |
| `source` | `"AI Response"` \| `"Database"` | Whether the reply came from Gemini or the cached DB fallback |

**Error responses:**

| Status | Body | Cause |
|--------|------|-------|
| `400` | `{"error": "Message is required"}` | Empty or missing `message` field |

**Examples:**
```bash
# cURL
curl -X POST https://<your-repl>.replit.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What projects has Cid built?"}'

# Python
import requests
r = requests.post(
    "https://<your-repl>.replit.app/api/chat",
    json={"message": "What is your tech stack?"}
)
print(r.json()["response"])

# JavaScript
const r = await fetch("/api/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: "Tell me about Ani" })
});
const { response, source } = await r.json();
console.log(source, response);
```

---

### 3. Chat History

```http
GET /api/history
```

Returns recent chat interactions saved to the database. Requires Firebase or PostgreSQL to be configured. Results are served from an in-memory cache (5-minute TTL) to avoid redundant DB queries.

**Query parameters:**

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `limit` | integer | 20 | 100 | Number of interactions to return |

**Response `200 OK`:**

An array of interaction objects, ordered newest-first.

```json
[
  {
    "id": "abc123",
    "user_query": "What projects has Cid built?",
    "ai_response": "Cid has built several projects including...",
    "source": "AI Response",
    "created_at": "2026-05-19T01:57:55.000000"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string \| integer | Firestore document ID or PostgreSQL row ID |
| `user_query` | string | Original user message |
| `ai_response` | string | Ani's reply |
| `source` | string | `"AI Response"` or `"Database"` |
| `created_at` | ISO 8601 string | When the interaction was stored |

Returns an empty array `[]` if no database is configured or no interactions exist yet.

**Example:**
```bash
curl "https://<your-repl>.replit.app/api/history?limit=5"
```

---

### 4. Usage Stats

```http
GET /api/stats
```

Returns aggregate statistics about all stored interactions.

**Response `200 OK`:**
```json
{
  "total": 42,
  "ai_responses": 39,
  "fallback_responses": 3,
  "first_interaction": "2026-05-17T10:00:00.000000",
  "last_interaction": "2026-05-19T01:57:55.000000"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total interactions stored |
| `ai_responses` | integer | How many were answered by Gemini |
| `fallback_responses` | integer | How many were answered from the DB cache |
| `first_interaction` | ISO 8601 \| `null` | Timestamp of the oldest stored interaction |
| `last_interaction` | ISO 8601 \| `null` | Timestamp of the newest stored interaction |

All values are `0` / `null` if no database is configured.

**Example:**
```bash
curl https://<your-repl>.replit.app/api/stats
```

---

## Actual vs. Documented Endpoints

Only the endpoints listed above exist in the current codebase. The following were referenced in older documentation but are **not implemented**:

| Endpoint | Status |
|----------|--------|
| `GET /api/github` | Not implemented |
| `GET /api/cache/status` | Not implemented |
| `POST /api/cache/clear` | Not implemented |
| `GET /metrics` | Not implemented |
| `GET /alerts` | Not implemented |
| `GET /api/docs` | Not implemented |
| `GET /apispec.json` | Not implemented |

If you need any of these, they can be added to `app/routes.py`.

---

## How the AI fallback works

1. Ani calls Gemini with the user's message plus live GitHub context (profile, README, recent repos).
2. If Gemini fails or all API keys are exhausted, Ani runs a **fuzzy match** (via `thefuzz`) against every stored interaction in the database.
3. If the best fuzzy match scores > 75, the stored answer is returned as `"source": "Database"`.
4. If no match is good enough, a generic offline message is returned.

All interactions are saved to the database asynchronously (background thread) so they don't slow down the HTTP response.

---

## Notes

- No authentication is required on any endpoint.
- CORS is enabled on all routes via `flask-cors`.
- The chat endpoint caps `message` at whatever the Gemini model's input limit allows; there is no server-side truncation currently.
- The history endpoint clamps `limit` between 1 and 100 regardless of the value you provide.
