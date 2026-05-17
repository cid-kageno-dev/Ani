# Ani API Documentation

## Overview

Ani provides a RESTful API for interacting with the AI assistant, accessing GitHub data, and managing cache. Full interactive documentation is available at `/api/docs` (Swagger UI).

**Base URL:** `http://localhost:5000`

---

## Authentication

Currently, Ani doesn't require authentication. In production, add authentication headers:

```bash
# With API Key
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/chat
```

---

## Endpoints

### 1. Health Check

**Get current system health**

```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "ai_ready": true,
  "db_ready": true,
  "uptime_seconds": 3600
}
```

**Status Codes:**
- `200` - Healthy
- `503` - Service unavailable

---

### 2. Chat with Ani

**Send a message and get AI response**

```http
POST /api/chat
Content-Type: application/json

{
  "message": "Tell me about your creator"
}
```

**Response (200 OK):**
```json
{
  "user_query": "Tell me about your creator",
  "ai_response": "I'm Ani, an AI assistant created by Cid Kageno. I'm built to showcase developer projects, handle inquiries, and make interactions more engaging...",
  "source": "AI Response",
  "timestamp": "2026-05-17T12:34:56Z"
}
```

**Request Errors:**

| Status | Error | Solution |
|--------|-------|----------|
| 400 | Missing "message" field | Include `"message"` in JSON body |
| 400 | Empty message | Provide non-empty message |
| 500 | AI service unavailable | Check API keys are configured |

**Examples:**

```bash
# cURL
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your purpose?"}'

# Python
import requests
response = requests.post(
    'http://localhost:5000/api/chat',
    json={'message': 'Hello Ani!'}
)
print(response.json())

# JavaScript
fetch('http://localhost:5000/api/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({message: 'Hi there!'})
})
.then(r => r.json())
.then(data => console.log(data.ai_response))
```

---

### 3. GitHub Information

**Get GitHub profile and repositories**

```http
GET /api/github
```

**Response (200 OK):**
```json
{
  "username": "cid-kageno-dev",
  "bio": "Developer & AI Enthusiast",
  "repositories": 12,
  "followers": 45,
  "following": 23,
  "public_repos": [
    {
      "name": "Ani",
      "description": "Smart AI Assistant",
      "url": "https://github.com/cid-kageno-dev/Ani",
      "stars": 3,
      "language": "Python",
      "updated_at": "2026-05-17T11:22:33Z"
    },
    {
      "name": "project-two",
      "description": "Another cool project",
      "url": "https://github.com/cid-kageno-dev/project-two",
      "stars": 5,
      "language": "JavaScript",
      "updated_at": "2026-05-10T08:15:22Z"
    }
  ],
  "cached": false,
  "cache_expires_in": 300,
  "timestamp": "2026-05-17T12:34:56Z"
}
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `force_refresh` | boolean | false | Bypass cache and fetch fresh data |

**Examples:**

```bash
# Get cached GitHub data
curl http://localhost:5000/api/github

# Force refresh (ignore cache)
curl "http://localhost:5000/api/github?force_refresh=true"
```

**Response Errors:**

| Status | Error | Solution |
|--------|-------|----------|
| 404 | User not found | Check GITHUB_USERNAME in config |
| 429 | Rate limited | Wait for cache to expire |
| 500 | API error | GitHub API might be down |

---

### 4. Cache Status

**Check current cache status**

```http
GET /api/cache/status
```

**Response (200 OK):**
```json
{
  "github": {
    "cached": true,
    "expires_in": 245,
    "cached_at": "2026-05-17T12:30:00Z"
  },
  "total_entries": 1,
  "timestamp": "2026-05-17T12:34:56Z"
}
```

---

### 5. Clear Cache

**Clear all cached data**

```http
POST /api/cache/clear
```

**Response (200 OK):**
```json
{
  "message": "All cache cleared",
  "cleared_entries": 1,
  "timestamp": "2026-05-17T12:34:56Z"
}
```

**Clear Specific Cache:**

```http
POST /api/cache/clear/github
```

**Response:**
```json
{
  "message": "GitHub cache cleared",
  "timestamp": "2026-05-17T12:34:56Z"
}
```

---

### 6. Chat History

**Get past interactions** (requires database configured)

```http
GET /api/history?limit=10&offset=0
```

**Query Parameters:**

| Parameter | Type | Default | Max |
|-----------|------|---------|-----|
| `limit` | integer | 10 | 100 |
| `offset` | integer | 0 | - |

**Response (200 OK):**
```json
{
  "total": 45,
  "limit": 10,
  "offset": 0,
  "interactions": [
    {
      "id": "msg_123",
      "user_query": "Tell me about your features",
      "ai_response": "I have several key features...",
      "source": "AI Response",
      "created_at": "2026-05-17T12:34:56Z"
    }
  ]
}
```

**Errors:**

| Status | Error | Solution |
|--------|-------|----------|
| 503 | Database not configured | Set up Firebase or PostgreSQL |
| 400 | Invalid limit/offset | Check parameter values |

---

### 7. Metrics

**Get application metrics**

```http
GET /metrics?format=json
```

**Query Parameters:**

| Parameter | Values | Description |
|-----------|--------|-------------|
| `format` | json, prometheus | Output format |

**Response (JSON):**
```json
{
  "timestamp": "2026-05-17T12:34:56Z",
  "counters": {
    "chat_requests": 152,
    "github_requests": 28,
    "errors": 3
  },
  "gauges": {
    "active_connections": 5,
    "cache_size_mb": 2.3
  }
}
```

**Response (Prometheus):**
```
ani_counter_chat_requests 152
ani_counter_github_requests 28
ani_gauge_active_connections 5
ani_gauge_cache_size_mb 2.3
```

---

### 8. Alerts

**Get recent alerts**

```http
GET /alerts?limit=50
```

**Query Parameters:**

| Parameter | Type | Default | Max |
|-----------|------|---------|-----|
| `limit` | integer | 50 | 500 |

**Response:**
```json
[
  {
    "timestamp": "2026-05-17T12:30:15Z",
    "level": "warning",
    "title": "High Response Time",
    "message": "Average response time exceeds 1000ms",
    "metadata": {
      "avg_ms": 1234,
      "threshold_ms": 1000
    }
  }
]
```

---

## Response Format

### Success Response

All successful responses follow this format:

```json
{
  "data": { /* ... */ },
  "status": "success",
  "timestamp": "2026-05-17T12:34:56Z"
}
```

### Error Response

```json
{
  "error": "Error message",
  "status": "error",
  "code": "ERROR_CODE",
  "timestamp": "2026-05-17T12:34:56Z",
  "details": { /* ... */ }
}
```

---

## Rate Limiting

Currently no rate limiting is enforced. With multiple API keys configured:

- Requests automatically rotate through available keys
- Rate limit resets every 60 seconds per key
- System maintains ~99.9% uptime

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `INVALID_REQUEST` | 400 | Missing or invalid parameters |
| `UNAUTHORIZED` | 401 | Authentication required |
| `NOT_FOUND` | 404 | Resource not found |
| `METHOD_NOT_ALLOWED` | 405 | Wrong HTTP method |
| `SERVICE_UNAVAILABLE` | 503 | Service is down or being maintained |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

---

## SDK Examples

### Python

```python
import requests

class AniClient:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
    
    def chat(self, message):
        response = requests.post(
            f'{self.base_url}/api/chat',
            json={'message': message}
        )
        return response.json()
    
    def get_github(self, force_refresh=False):
        response = requests.get(
            f'{self.base_url}/api/github',
            params={'force_refresh': force_refresh}
        )
        return response.json()
    
    def health(self):
        response = requests.get(f'{self.base_url}/health')
        return response.json()

# Usage
client = AniClient()
response = client.chat('Hello Ani!')
print(response['ai_response'])
```

### JavaScript

```javascript
class AniClient {
  constructor(baseUrl = 'http://localhost:5000') {
    this.baseUrl = baseUrl;
  }
  
  async chat(message) {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message})
    });
    return response.json();
  }
  
  async getGitHub(forceRefresh = false) {
    const response = await fetch(
      `${this.baseUrl}/api/github?force_refresh=${forceRefresh}`
    );
    return response.json();
  }
  
  async health() {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }
}

// Usage
const client = new AniClient();
const response = await client.chat('Hi!');
console.log(response.ai_response);
```

---

## Webhooks (Future)

Upcoming features:
- Event webhooks for chat interactions
- GitHub sync notifications
- Error alerts
- Metrics webhooks

---

## OpenAPI Specification

The API follows OpenAPI 2.0 (Swagger) specification. View the specification:

```bash
curl http://localhost:5000/apispec.json
```

Generate client SDK:

```bash
# Python
openapitools generate -g python -i http://localhost:5000/apispec.json -o ani-python-client

# JavaScript/TypeScript
openapi-generator generate -g typescript-fetch -i http://localhost:5000/apispec.json -o ani-js-client
```

---

## Changelog

### v1.0.0 (2026-05-17)
- Initial release
- Chat endpoint
- GitHub integration
- Cache management
- Health checks
- Metrics and alerts

---

For more help, see [README.md](../README.md) or [MONITORING.md](MONITORING.md).
