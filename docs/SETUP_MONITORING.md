# Setting Up Monitoring for Ani in Production

## Quick Start

Use Docker Compose to run Ani with full monitoring stack:

```bash
# Start all services
docker-compose -f docker-compose-monitoring.yml up -d

# Access services
# - Ani API: http://localhost:5000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
# - Kibana (logs): http://localhost:5601
```

---

## Services Included

### 1. Ani (Main Application)
- Port: 5000
- Metrics endpoint: `/metrics`
- Logs: `/var/log/ani/app.json.log`

### 2. PostgreSQL (Database)
- Port: 5432
- Database: ani_db
- Credentials in docker-compose.yml

### 3. Prometheus (Metrics Storage)
- Port: 9090
- Scrapes Ani metrics every 15 seconds
- Data retention: default

### 4. Grafana (Visualization)
- Port: 3000
- Default: admin / admin
- Pre-configured Prometheus datasource

### 5. Elasticsearch (Centralized Logs)
- Port: 9200
- Stores JSON-formatted logs

### 6. Kibana (Log Visualization)
- Port: 5601
- Query and visualize Elasticsearch logs

---

## Configuration

### Environment Variables

```bash
# Create .env file
GOOGLE_API_KEY1=your_api_key
LOG_LEVEL=INFO
LOG_DIR=/var/log/ani
```

### Grafana Dashboards

1. Login to Grafana (http://localhost:3000)
2. Add Prometheus datasource: http://prometheus:9090
3. Create dashboard with:
   - Request rate (requests/sec)
   - Response time (p50, p95, p99)
   - Error rate (%)
   - Service health status
   - Active connections
   - Cache hit rate

### Alert Rules

Create `alert_rules.yml`:

```yaml
groups:
  - name: ani_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: increase(ani_counter_errors[5m]) > 10
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: HighResponseTime
        expr: ani_gauge_response_time_avg_ms > 1000
        for: 5m
        annotations:
          summary: "Average response time exceeds 1000ms"
      
      - alert: ServiceDown
        expr: up{job="ani"} == 0
        for: 1m
        annotations:
          summary: "Ani service is down"
```

---

## Monitoring Workflows

### 1. Real-time Metrics

```bash
# View metrics in Prometheus
# Navigate to: http://localhost:9090/graph
# Query: ani_counter_chat_requests
```

### 2. Log Aggregation

```bash
# View logs in Kibana
# Navigate to: http://localhost:5601
# Index pattern: logs-*
# Search: level:ERROR
```

### 3. Dashboard Monitoring

```bash
# Create custom dashboard in Grafana
# - Panel 1: Chat requests per minute
# - Panel 2: Error rate
# - Panel 3: Database connection pool
# - Panel 4: Cache effectiveness
```

---

## Logging to External Services

### AWS CloudWatch

```python
import boto3
import logging
from pythonjsonlogger import jsonlogger

watchtower_handler = watchtower.CloudWatchLogHandler(
    log_group='ani-app',
    stream_name='production'
)
watchtower_handler.setFormatter(
    jsonlogger.JsonFormatter()
)
logger.addHandler(watchtower_handler)
```

### Google Cloud Logging

```python
from google.cloud import logging as cloud_logging

client = cloud_logging.Client()
client.setup_logging()
```

### Datadog

```python
from datadog import initialize, api

options = {
    'api_key': os.getenv('DATADOG_API_KEY'),
    'app_key': os.getenv('DATADOG_APP_KEY')
}
initialize(**options)
```

---

## Performance Tuning

### Optimize Log Volume

```ini
# Only log WARNING and above in production
LOG_LEVEL=WARNING
```

### Database Performance

```sql
-- Create indexes for faster queries
CREATE INDEX idx_created_at ON chat_interactions(created_at DESC);
CREATE INDEX idx_user_id ON chat_interactions(user_id);
```

### Prometheus Tuning

```yaml
global:
  scrape_interval: 30s      # Increase interval
  evaluation_interval: 30s
  external_labels:
    cluster: 'production'
```

---

## Backup Strategy

### Daily Log Backups

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf logs_backup_${DATE}.tar.gz logs/
aws s3 cp logs_backup_${DATE}.tar.gz s3://ani-backups/
rm logs_backup_${DATE}.tar.gz
```

### Prometheus Snapshots

```bash
# Backup Prometheus data
docker exec prometheus tar -czf /prometheus/snapshot.tar.gz /prometheus/
```

---

## Troubleshooting

### High Memory Usage

```bash
# Check container memory
docker stats ani

# Reduce Prometheus retention
docker-compose -f docker-compose-monitoring.yml up -d \
  --build --force-recreate
```

### Missing Logs

```bash
# Check log directory
ls -la /var/log/ani/

# Check permissions
chown -R 1000:1000 /var/log/ani/
```

### Prometheus Not Scraping

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check connectivity
docker exec prometheus curl http://ani:5000/metrics
```

---

## Next Steps

1. ✅ Deploy monitoring stack
2. ✅ Configure alerts
3. ✅ Create dashboards
4. ✅ Set up log retention
5. ✅ Document runbooks
6. ✅ Train team on monitoring

---

For detailed logging info, see [MONITORING.md](MONITORING.md).
