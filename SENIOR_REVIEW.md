# Senior Developer Review

## Overall Assessment
The project has a clear modular structure, good observability intentions (logging + monitoring docs), and a practical fallback strategy for AI outages. The API surface is straightforward and test coverage exists for key components.

That said, there are a few **high-priority issues** that should be fixed before production use.

## Critical Findings

### 1) Secret leakage in source control (Critical)
`config.py` contains a full Firebase service-account private key hardcoded in `_FIREBASE_SERVICE_ACCOUNT`, and then uses it as a runtime fallback if `FIREBASE_SERVICE_ACCOUNT_JSON` is absent. This is a severe security risk and should be removed immediately.

**Recommendation**
- Remove hardcoded credentials from `config.py`.
- Rotate/revoke leaked Firebase credentials immediately.
- Load secrets only from environment variables or mounted secret files.

### 2) Sensitive file tracked in repo (Critical)
A `firebase-key.json` file exists in the repository root. Even if intended for local development, this is highly risky if committed.

**Recommendation**
- Ensure `firebase-key.json` is removed from git history if it was committed.
- Add/confirm `.gitignore` rules for secret files.
- Use sample placeholders (e.g., `firebase-key.example.json`) instead.

## High Priority Findings

### 3) Lock re-entry bug risk in cache helpers
`_get_cached()` acquires `_cache_lock` and calls `_is_cache_valid()`, which also acquires `_cache_lock`. This is currently safe only because `RLock` is re-entrant, but adds unnecessary lock nesting and complexity.

**Recommendation**
- Refactor validity checks to avoid nested lock acquisition.
- Keep lock granularity minimal and explicit.

### 4) Over-broad exception handling
Several hot paths catch broad `Exception` and suppress actionable categories (network timeout, auth, quota, invalid response schema).

**Recommendation**
- Catch specific exceptions where possible.
- Include structured error metadata in logs (error class, upstream status code, retryability).

### 5) Background thread fire-and-forget writes
`save_interaction` is called in daemon threads. This reduces latency, but failures are easy to miss and writes may be dropped during shutdown.

**Recommendation**
- Consider a bounded queue + worker with retry/backoff and drain on shutdown.
- Track write failures via metrics.

## Medium Priority Findings

### 6) GitHub context payload size and latency variance
Each model call may include large README content and repo lists. This increases token usage and can impact latency/cost.

**Recommendation**
- Apply stricter truncation and summarization of context.
- Cache pre-summarized context and refresh asynchronously.

### 7) Data/source coupling in route responses
`history` assumes `created_at` always has `.isoformat()` available.

**Recommendation**
- Normalize timestamp at serialization boundary and add defensive conversion.

## What’s good
- Clear separation of route, AI, DB, config services.
- Key-rotation strategy for API resilience.
- Practical fallback mode when model fails.
- Tests exist for config/cache/API route basics.

## Suggested Next Actions (order)
1. Remove hardcoded credentials and rotate Firebase keys.
2. Remove secret files from repository history and lock down secret management.
3. Add CI checks: secret scanning + linting + tests.
4. Refactor async persistence to durable queue model.
5. Tighten exception taxonomy and structured logging.

