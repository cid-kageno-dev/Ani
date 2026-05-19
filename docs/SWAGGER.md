# API Reference

## Overview

Ani's API is a small, focused REST interface. There is no Swagger/OpenAPI UI built into the app at this time. All endpoint details are documented in [API.md](API.md).

---

## Available Endpoints (summary)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Chat web UI |
| `POST` | `/api/chat` | Send a message, get Ani's reply |
| `GET` | `/api/history` | Recent chat interactions |
| `GET` | `/api/stats` | Aggregate usage statistics |
| `GET` | `/api/health` | Liveness check |

See [API.md](API.md) for full request/response details and examples.

---

## Testing the API Manually

You can test any endpoint with `curl`, Postman, Insomnia, or any HTTP client.

### Health check
```bash
curl https://<your-repl>.replit.app/api/health
```

### Chat
```bash
curl -X POST https://<your-repl>.replit.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What has Cid built?"}'
```

### History
```bash
curl "https://<your-repl>.replit.app/api/history?limit=10"
```

### Stats
```bash
curl https://<your-repl>.replit.app/api/stats
```

---

## Adding OpenAPI / Swagger Support

If you want interactive API docs, you can add them by installing `flask-swagger-ui` and `flasgger`:

```bash
pip install flasgger
```

Then in `app/__init__.py`:

```python
from flasgger import Swagger
swagger = Swagger(app)
```

And annotate each route in `app/routes.py` with docstring YAML. Once added, the UI is available at `/apidocs`.
