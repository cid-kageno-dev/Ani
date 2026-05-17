# Swagger/OpenAPI Documentation

## Accessing API Documentation

### Interactive UI

```
http://localhost:5000/api/docs
```

Browse and test all API endpoints directly in the browser.

---

## API Specification

Get the raw OpenAPI spec:

```
http://localhost:5000/apispec.json
```

---
## Available Endpoints

All endpoints are documented with:
- Description
- Request/response schemas
- Example values
- Error codes
- Parameters

### Try It Out

1. Open http://localhost:5000/api/docs
2. Click on any endpoint
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"

---

## Generating Client Libraries

Use OpenAPI Generator to create client SDKs:

### Python

```bash
openapi-generator generate \
  -g python \
  -i http://localhost:5000/apispec.json \
  -o ./ani-python-client
```

### JavaScript/TypeScript

```bash
openapi-generator generate \
  -g typescript-fetch \
  -i http://localhost:5000/apispec.json \
  -o ./ani-js-client
```

### Go

```bash
openapi-generator generate \
  -g go \
  -i http://localhost:5000/apispec.json \
  -o ./ani-go-client
```

### Java

```bash
openapi-generator generate \
  -g java \
  -i http://localhost:5000/apispec.json \
  -o ./ani-java-client
```

---

## Testing with Swagger Editor

1. Open https://editor.swagger.io/
2. Select "File" → "Import URL"
3. Enter: `http://localhost:5000/apispec.json`
4. Browse and test endpoints

---

For endpoint details, see [API.md](API.md).
