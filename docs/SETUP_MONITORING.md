# Setting Up the Full Monitoring Stack

This guide covers running Ani with a complete observability stack (Prometheus, Grafana, Elasticsearch, Kibana) via Docker Compose. This is intended for **self-hosted or production** setups, not Replit.

For basic logging on Replit, see [MONITORING.md](MONITORING.md).

---

## Prerequisites

- Docker and Docker Compose installed
- At least 4 GB RAM available (Elasticsearch is memory-hungry)

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/cid-kageno-dev/Ani.git
cd Ani

# Set your API key
echo 'GOOGLE_API_KEY1=your_key_here' > .env

# Start all services
docker-compose -f docker-compose-monitoring.yml up -d

# Check service health
docker-compose -f docker-compose-monitoring.yml ps
```

---

## Services

| Service | Port | Purpose |
|---------|------|---------|
| **Ani** | 5000 | Main application |
| **PostgreSQL** | 5432 | Chat interaction storage (fallback) |
| **Prometheus** | 9090 | Metrics collection and storage |
| **Grafana** | 3000 | Metrics visualisation dashboards |
| **Elasticsearch** | 9200 | Centralised log storage |
| **Kibana** | 5601 | Log search and visualisation |

---

## Configuration

### Environment variables

Create a `.env` file in the project root:

```ini
GOOGLE_API_KEY1=AIzaSy...
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
FIREBASE_PROJECT_ID=gen-lang-client-0109922552
FIREBASE_DATABASE_URL=https://...
LOG_LEVEL=INFO
```

### Prometheus

`prometheus.yml` is already configured to scrape Ani at `/metrics` every 15 seconds. After wiring the `/metrics` route (see [MONITORING.md](MONITORING.md)), no further Prometheus config is needed.

To add alerting rules, create `alert_rules.yml`:

```yaml
groups:
  - name: ani_alerts
    rules:
      - alert: HighErrorRate
        expr: increase(ani_counter_errors[5m]) > 10
        for: 5m
        annotations:
          summary: "High error rate in Ani"

      - alert: ServiceDown
        expr: up{job="ani"} == 0
        for: 1m
        annotations:
          summary: "Ani is not responding"
```

### Grafana

1. Open http://localhost:3000 (login: `admin` / `admin`).
2. Add a Prometheus data source: `http://prometheus:9090`.
3. Create a dashboard with panels for:
   - Chat requests per minute
   - AI vs. fallback response ratio
   - Average response time
   - Error rate
   - DB cache hit rate

### Kibana

1. Open http://localhost:5601.
2. Create an index pattern matching `logs-*`.
3. Use the Discover view to search logs:
   - `level:ERROR` — errors only
   - `name:ani.chat` — chat interactions
   - `name:ani.ai` — Gemini calls

---

## Useful Commands

```bash
# View logs for all services
docker-compose -f docker-compose-monitoring.yml logs -f

# View Ani logs only
docker-compose -f docker-compose-monitoring.yml logs -f ani

# Restart Ani without restarting the whole stack
docker-compose -f docker-compose-monitoring.yml restart ani

# Stop everything
docker-compose -f docker-compose-monitoring.yml down

# Stop and remove volumes (resets all data)
docker-compose -f docker-compose-monitoring.yml down -v
```

---

## Troubleshooting

### Prometheus shows Ani as "down"
- Ensure the `/metrics` route is wired in `app/routes.py` (see [MONITORING.md](MONITORING.md)).
- Check Ani is reachable: `docker exec prometheus curl http://ani:5000/metrics`.

### Kibana shows no logs
- Confirm Ani is writing JSON-structured logs to the volume path Logstash reads from.
- Check log directory permissions: `chown -R 1000:1000 /var/log/ani/`.

### Elasticsearch out of memory
```bash
# Increase Docker's memory limit, or reduce ES heap:
docker-compose -f docker-compose-monitoring.yml up -d \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" elasticsearch
```

### Grafana "No data"
- Verify the Prometheus data source URL is `http://prometheus:9090` (use the container name, not localhost).
- Confirm Prometheus is successfully scraping: http://localhost:9090/targets.

---

For more on the monitoring module, see [MONITORING.md](MONITORING.md).
