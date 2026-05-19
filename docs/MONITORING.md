# Monitoring & Logging

## Overview

Ani includes structured logging out of the box and ships a standalone monitoring module (`monitoring.py`) with metrics, health, and alert utilities ready to be wired up.

---

## Logging

### How it works

Logging is configured in `app/logger.py` and initialised via `config.py`. Every module gets a named logger:

```python
from app.logger import get_logger
log = get_logger("ani.mymodule")

log.info("Something happened")
log.warning("Watch out")
log.error("Something broke")
```

### Log level

Controlled by the `LOG_LEVEL` environment variable or `config.json`:

```json
{ "logging": { "level": "INFO" } }
```

Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Default is `INFO`.

On Replit, logs appear in the workflow console. In production, use `LOG_LEVEL=WARNING` to reduce noise.

### Startup output

On every boot the app prints a connection status table:

```
  CONNECTION STATUS
────────────────────────────────────────────────────
  ✓  Gemini AI    gemini-2.5-flash
  ✓  Firebase     collection 'chat_interactions'
  ✓  PostgreSQL   helium/heliumdb
  ✓  DB Schema    active backend: firebase
────────────────────────────────────────────────────
```

### Chat logging

Every interaction is logged to the console with a visual separator:

```
────────────────────────────────────────────────────
USER  ▶  What projects has Cid built?
·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·
ANI   ◀  [AI Response] (843ms)
          Cid has built several projects...
────────────────────────────────────────────────────
```

---

## Monitoring Utilities (`monitoring.py`)

`monitoring.py` is a standalone module — it is not currently wired to Flask routes. It provides three classes you can import and use:

### MetricsCollector

```python
from monitoring import MetricsCollector

metrics = MetricsCollector()

metrics.increment_counter("chat_requests")
metrics.set_gauge("active_connections", 5)
metrics.record_metric("response_time_ms", 243.5, tags={"endpoint": "/api/chat"})

# Export
json_output = metrics.export_metrics("json")
prom_output = metrics.export_metrics("prometheus")
summary     = metrics.get_summary()
```

### HealthMonitor

```python
from monitoring import HealthMonitor
from flask import Flask

app = Flask(__name__)
health = HealthMonitor(app)

status = health.get_health()
# {"status": "healthy", "ai_ready": True, "db_ready": True, ...}
```

### AlertManager

```python
from monitoring import AlertManager

alerts = AlertManager()

alerts.trigger_alert(
    level="critical",
    title="Database connection lost",
    message="Cannot reach Firestore",
    metadata={"project": "gen-lang-client-0109922552"}
)

alerts.trigger_alert(level="warning", title="Slow response", message="843ms avg")
alerts.trigger_alert(level="info",    title="Cache cleared",  message="Manual clear")
```

Alert levels: `critical`, `warning`, `info`.

### Wiring to Flask routes

To expose metrics and alerts as HTTP endpoints, add to `app/routes.py`:

```python
from monitoring import init_monitoring

metrics, health, alerts = init_monitoring(app, log)

@main.route("/metrics")
def get_metrics():
    fmt = request.args.get("format", "json")
    return metrics.export_metrics(fmt), 200, {"Content-Type": "text/plain" if fmt == "prometheus" else "application/json"}

@main.route("/alerts")
def get_alerts():
    limit = request.args.get("limit", 50, type=int)
    return jsonify(alerts.get_recent(limit))
```

---

## Health Check Endpoint

The `/api/health` endpoint is already registered and returns:

```json
{ "status": "ok" }
```

Use this for uptime monitoring, load balancer probes, or Kubernetes liveness checks:

```yaml
livenessProbe:
  httpGet:
    path: /api/health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 10
```

---

## Prometheus Integration

If you wire `monitoring.py` to a `/metrics` route (see above), you can scrape it with Prometheus:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: ani
    static_configs:
      - targets: ["localhost:5000"]
    metrics_path: /metrics
    params:
      format: [prometheus]
    scrape_interval: 15s
```

The project ships a ready-to-use `prometheus.yml` in the root directory.

---

## Docker-based Monitoring Stack

For full Prometheus + Grafana + Elasticsearch + Kibana monitoring, use:

```bash
docker-compose -f docker-compose-monitoring.yml up -d
```

Services started:

| Service | Port | URL |
|---------|------|-----|
| Ani | 5000 | http://localhost:5000 |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 (admin/admin) |
| Elasticsearch | 9200 | http://localhost:9200 |
| Kibana | 5601 | http://localhost:5601 |

---

## Best Practices

- Use `INFO` in development, `WARNING` in production.
- Never log secrets, API keys, or PII.
- The in-memory interaction and stats cache (5-minute TTL) already reduces DB load significantly; monitor cache hit rates if you add metrics.
- For Replit deployments, workflow console logs are the primary log surface — no file rotation needed.
