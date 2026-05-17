# Monitoring & Logging Guide for Ani

## Overview

Ani includes comprehensive monitoring and logging capabilities for production environments. This guide covers:

- **Logging Configuration** - File and console logging with rotation
- **Metrics Collection** - Performance and usage metrics
- **Health Monitoring** - Service health checks
- **Alert Management** - Critical event alerting
- **Performance Tracking** - Request/response timing

---

## Logging Setup

### Basic Configuration

```python
from logging_config import setup_logging, get_logger

# Initialize logging
setup_logging(log_level='INFO')

# Get logger instance
logger = get_logger(__name__)

# Use logger
logger.info("Application started")
logger.warning("Cache miss")
logger.error("Database connection failed")
```

### Environment Variables

```ini
# logging_config.py respects these variables:
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs                # Directory for log files
```

### Log Files Generated

```
logs/
├── app.json.log             # Structured JSON logs (10MB rotation)
├── errors-2026-05-17.log    # Error logs only (daily rotation)
└── debug-2026-05-17.log     # Debug logs (daily rotation)
```

### JSON Logging

For production, use structured JSON logging:

```json
{
  "timestamp": "2026-05-17T12:34:56.789Z",
  "level": "INFO",
  "name": "ani.api",
  "message": "Chat request processed",
  "method": "POST",
  "path": "/api/chat",
  "status_code": 200,
  "elapsed_ms": 245.3
}
```

---

## Request/Response Logging

### Automatic Logging

```python
from logging_config import RequestLogger, get_logger
from flask import Flask

app = Flask(__name__)
logger = get_logger(__name__)

# Enable automatic request/response logging
RequestLogger(app, logger)

# All requests are now logged automatically
```

### Logged Information

- Request method (GET, POST, etc.)
- Request path and query parameters
- Client IP address
- Response status code
- Execution time
- Error details

---

## Performance Monitoring

### Using PerformanceLogger

```python
from logging_config import PerformanceLogger, get_logger
import time

logger = get_logger(__name__)

# Monitor function execution time
with PerformanceLogger(logger, 'expensive_operation', threshold_ms=1000):
    # Your code here
    time.sleep(0.5)
    # If execution exceeds 1000ms, warning is logged
```

### Output

```
2026-05-17 12:34:56 - ani.api - DEBUG - Starting expensive_operation
2026-05-17 12:34:56 - ani.api - DEBUG - expensive_operation completed in 500.23ms
```

---

## Metrics Collection

### Recording Metrics

```python
from monitoring import MetricsCollector

metrics = MetricsCollector()

# Record metric value
metrics.record_metric('response_time', 245.3, tags={'endpoint': '/api/chat'})

# Increment counter
metrics.increment_counter('chat_requests')
metrics.increment_counter('errors', 5)  # Increment by 5

# Set gauge (current value)
metrics.set_gauge('active_connections', 42)
metrics.set_gauge('cache_size_mb', 156.7)
```

### Exporting Metrics

```python
# JSON format
json_metrics = metrics.export_metrics('json')
print(json_metrics)

# Prometheus format
prometheus_metrics = metrics.export_metrics('prometheus')
print(prometheus_metrics)

# Summary
summary = metrics.get_summary()
print(summary)
```

### API Endpoint

```bash
# Get metrics in JSON
curl http://localhost:5000/metrics

# Get metrics in Prometheus format
curl http://localhost:5000/metrics?format=prometheus
```

---

## Health Monitoring

### Checking Service Health

```python
from monitoring import HealthMonitor
from flask import Flask

app = Flask(__name__)
health = HealthMonitor(app)

# Get full health status
status = health.get_health()
print(status)
```

### Health Status Response

```json
{
  "status": "healthy",
  "ai_ready": true,
  "db_ready": true,
  "cache_ready": true,
  "uptime_seconds": 3600,
  "timestamp": "2026-05-17T12:34:56Z"
}
```

### Status Codes

- **healthy** - All services operational
- **degraded** - Some services unavailable
- **unhealthy** - Major services down

### Health Check Endpoint

```bash
# Check health (returns 200 if healthy, 503 if not)
curl http://localhost:5000/health

# Kubernetes readiness probe
livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 10
```

---

## Alert Management

### Triggering Alerts

```python
from monitoring import AlertManager, init_monitoring

alerts = AlertManager()

# Trigger different alert levels
alerts.trigger_alert(
    level='critical',
    title='Database Connection Lost',
    message='Cannot connect to PostgreSQL',
    metadata={'host': 'db.example.com', 'port': 5432}
)

alerts.trigger_alert(
    level='warning',
    title='High Response Times',
    message='Average response time exceeds 1000ms',
    metadata={'avg_ms': 1234, 'threshold_ms': 1000}
)

alerts.trigger_alert(
    level='info',
    title='Cache Cleared',
    message='GitHub cache was cleared',
    metadata={'reason': 'manual'}
)
```

### Alert Levels

- **critical** - Immediate action required
- **warning** - Investigate soon
- **info** - Informational

### Custom Alert Channels

```python
class EmailAlertChannel:
    def send(self, alert):
        # Send alert via email
        send_email(
            to='admin@example.com',
            subject=f"[{alert['level'].upper()}] {alert['title']}",
            body=alert['message']
        )

class SlackAlertChannel:
    def send(self, alert):
        # Send alert to Slack
        webhook_url = os.getenv('SLACK_WEBHOOK')
        requests.post(webhook_url, json={
            'text': f"*{alert['level'].upper()}* - {alert['title']}",
            'blocks': [{
                'type': 'section',
                'text': {'type': 'mrkdwn', 'text': alert['message']}
            }]
        })

alerts = AlertManager()
alerts.add_alert_channel(EmailAlertChannel())
alerts.add_alert_channel(SlackAlertChannel())

# Now alerts are sent to email and Slack
alerts.trigger_alert('critical', 'Error', 'Database down')
```

### Viewing Alerts

```bash
# Get recent 50 alerts
curl http://localhost:5000/alerts

# Get last 100 alerts
curl http://localhost:5000/alerts?limit=100
```

---

## Integration with Flask

### Complete Setup

```python
from flask import Flask
from logging_config import setup_logging, get_logger, RequestLogger
from monitoring import init_monitoring
import os

def create_app():
    app = Flask(__name__)
    
    # Setup logging
    setup_logging(os.getenv('LOG_LEVEL', 'INFO'))
    logger = get_logger(__name__)
    
    # Initialize monitoring
    metrics, health, alerts = init_monitoring(app, logger)
    
    # Enable request logging
    RequestLogger(app, logger)
    
    # Store in app for access in routes
    app.metrics = metrics
    app.health = health
    app.alerts = alerts
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=False)
```

### Using in Routes

```python
from flask import current_app, request
from logging_config import get_logger, PerformanceLogger

logger = get_logger(__name__)

@app.route('/api/chat', methods=['POST'])
def chat():
    with PerformanceLogger(logger, 'chat_endpoint', threshold_ms=500):
        current_app.metrics.increment_counter('chat_requests')
        
        try:
            # Your logic here
            result = process_chat(data)
            current_app.metrics.record_metric('response_time', 245.3)
            return result
        except Exception as e:
            current_app.alerts.trigger_alert(
                'error',
                'Chat Processing Failed',
                str(e)
            )
            raise
```

---

## Log Rotation

### Configuration

Log files are automatically rotated:

- **app.json.log** - Rotates at 10MB, keeps 10 backups
- **errors-*.log** - Rotates daily, keeps 20 backups
- **debug-*.log** - Rotates daily, keeps 10 backups

### Manual Cleanup

```bash
# Remove old log files (older than 30 days)
find logs/ -name "*.log" -mtime +30 -delete

# Archive old logs
tar -czf logs_archive_$(date +%Y%m%d).tar.gz logs/
rm -rf logs/*
```

---

## Production Deployment

### Environment Variables

```ini
# .env (Production)
LOG_LEVEL=WARNING           # Only WARNING and above
LOG_DIR=/var/log/ani        # Persistent log directory
FLASK_DEBUG=false           # Disable debug mode
```

### Docker Setup

```dockerfile
# In Dockerfile
RUN mkdir -p /var/log/ani
VOLUME ["/var/log/ani"]

ENV LOG_DIR=/var/log/ani
ENV LOG_LEVEL=INFO
```

### Docker Compose

```yaml
services:
  ani:
    volumes:
      - ./logs:/var/log/ani
    environment:
      - LOG_LEVEL=INFO
      - LOG_DIR=/var/log/ani
```

### Systemd Service

```ini
[Service]
Environment="LOG_LEVEL=INFO"
Environment="LOG_DIR=/var/log/ani"
StandardOutput=journal
StandardError=journal
```

---

## Monitoring Tools Integration

### Prometheus

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ani'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics?format=prometheus'
    scrape_interval: 15s
```

### Grafana Dashboard

Create dashboard with panels:
- Request rate (requests/second)
- Response time (avg, p95, p99)
- Error rate
- Service health status
- Active connections

### ELK Stack

```python
# Send logs to Elasticsearch
from pythonjsonlogger import jsonlogger
import logging.handlers

handler = logging.handlers.SysLogHandler(address=('logstash.example.com', 5000))
handler.setFormatter(jsonlogger.JsonFormatter())
logger.addHandler(handler)
```

---

## Troubleshooting

### No Logs Being Generated

```python
# Check logging is initialized
from logging_config import setup_logging
setup_logging('DEBUG')

# Check log directory exists
import os
log_dir = os.getenv('LOG_DIR', 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
```

### High Disk Usage

```bash
# Check log file sizes
du -sh logs/*

# Reduce rotation size in logging_config.py
maxBytes=5242880  # 5MB instead of 10MB

# Clean up old logs
find logs/ -name "*.log*" -mtime +7 -delete
```

### Performance Impact

Logging has minimal overhead. If concerned:

```python
# Use INFO level instead of DEBUG in production
setup_logging('INFO')

# Disable JSON logging if not needed
# (keeps only console and error files)
```

---

## Best Practices

✅ **Do**:
- Log at appropriate levels (INFO for events, WARNING for issues)
- Include context in logs (user ID, request path, etc.)
- Monitor metrics regularly
- Set up alerts for critical errors
- Rotate logs to prevent disk overflow
- Use structured JSON logging in production

❌ **Don't**:
- Log sensitive information (passwords, tokens)
- Log at DEBUG level in production
- Ignore critical alerts
- Keep unlimited log history
- Log on every line (use sampling for high-volume events)

---

**For more information, see:**
- [README.md](../README.md) - API documentation
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development guide
