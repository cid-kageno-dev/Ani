"""Monitoring and metrics collection for production."""

import os
import logging
from datetime import datetime
from collections import defaultdict
import json


class MetricsCollector:
    """Collect and store application metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.logger = logging.getLogger(__name__)
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.gauges = {}
        self.timers = {}
    
    def record_metric(self, name, value, tags=None):
        """Record a metric value.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional dictionary of tags
        """
        timestamp = datetime.utcnow().isoformat()
        metric_data = {
            'timestamp': timestamp,
            'value': value,
            'tags': tags or {}
        }
        self.metrics[name].append(metric_data)
        
        # Keep only last 1000 metrics per name
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]
    
    def increment_counter(self, name, value=1):
        """Increment a counter.
        
        Args:
            name: Counter name
            value: Amount to increment (default: 1)
        """
        self.counters[name] += value
    
    def set_gauge(self, name, value):
        """Set a gauge value.
        
        Args:
            name: Gauge name
            value: Gauge value
        """
        self.gauges[name] = {
            'timestamp': datetime.utcnow().isoformat(),
            'value': value
        }
    
    def get_summary(self):
        """Get metrics summary.
        
        Returns:
            Dictionary containing metrics summary
        """
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'counters': dict(self.counters),
            'gauges': self.gauges,
            'metrics_count': sum(len(v) for v in self.metrics.values())
        }
    
    def export_metrics(self, format='json'):
        """Export metrics in specified format.
        
        Args:
            format: Export format ('json', 'prometheus')
            
        Returns:
            Metrics in specified format
        """
        if format == 'json':
            return json.dumps({
                'timestamp': datetime.utcnow().isoformat(),
                'counters': dict(self.counters),
                'gauges': self.gauges,
            }, indent=2)
        
        elif format == 'prometheus':
            output = []
            for name, value in self.counters.items():
                output.append(f"ani_counter_{name} {value}")
            for name, data in self.gauges.items():
                output.append(f"ani_gauge_{name} {data['value']}")
            return '\n'.join(output)
        
        return None


class HealthMonitor:
    """Monitor application health."""
    
    def __init__(self, app, logger=None):
        """Initialize health monitor.
        
        Args:
            app: Flask application
            logger: Logger instance (optional)
        """
        self.app = app
        self.logger = logger or logging.getLogger(__name__)
        self.health_status = {
            'status': 'initializing',
            'ai_ready': False,
            'db_ready': False,
            'cache_ready': True,
            'timestamp': None,
            'uptime_seconds': 0,
        }
        self.start_time = datetime.utcnow()
    
    def check_ai_service(self):
        """Check if AI service is ready.
        
        Returns:
            True if AI service is available
        """
        try:
            from config import Config
            ready = bool(Config.GOOGLE_API_KEYS)
            self.health_status['ai_ready'] = ready
            return ready
        except Exception as e:
            self.logger.error(f"AI service check failed: {e}")
            self.health_status['ai_ready'] = False
            return False
    
    def check_database(self):
        """Check if database is ready.
        
        Returns:
            True if database is available
        """
        try:
            from config import Config
            if Config.DATABASE_BACKEND == 'firebase':
                # Firebase check would go here
                ready = True
            elif Config.DATABASE_BACKEND == 'postgresql':
                # PostgreSQL check would go here
                ready = bool(Config.DATABASE_URL)
            else:
                ready = False
            
            self.health_status['db_ready'] = ready
            return ready
        except Exception as e:
            self.logger.error(f"Database check failed: {e}")
            self.health_status['db_ready'] = False
            return False
    
    def get_health(self):
        """Get current health status.
        
        Returns:
            Dictionary containing health information
        """
        self.check_ai_service()
        self.check_database()
        
        # Calculate uptime
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        self.health_status['uptime_seconds'] = uptime
        
        # Determine overall status
        if self.health_status['ai_ready'] and self.health_status['db_ready']:
            self.health_status['status'] = 'healthy'
        elif self.health_status['ai_ready'] or self.health_status['db_ready']:
            self.health_status['status'] = 'degraded'
        else:
            self.health_status['status'] = 'unhealthy'
        
        self.health_status['timestamp'] = datetime.utcnow().isoformat()
        return self.health_status


class AlertManager:
    """Manage alerts for critical events."""
    
    def __init__(self, logger=None):
        """Initialize alert manager.
        
        Args:
            logger: Logger instance (optional)
        """
        self.logger = logger or logging.getLogger(__name__)
        self.alerts = []
        self.alert_channels = []
    
    def add_alert_channel(self, channel):
        """Add an alert channel (email, slack, etc).
        
        Args:
            channel: Alert channel instance
        """
        self.alert_channels.append(channel)
    
    def trigger_alert(self, level, title, message, metadata=None):
        """Trigger an alert.
        
        Args:
            level: Alert level (critical, warning, info)
            title: Alert title
            message: Alert message
            metadata: Additional metadata (optional)
        """
        alert = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'title': title,
            'message': message,
            'metadata': metadata or {}
        }
        
        self.alerts.append(alert)
        
        # Keep only last 1000 alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
        
        # Log alert
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"[{level.upper()}] {title}: {message}")
        
        # Send to channels
        for channel in self.alert_channels:
            try:
                channel.send(alert)
            except Exception as e:
                self.logger.error(f"Failed to send alert via {channel}: {e}")
    
    def get_recent_alerts(self, limit=50):
        """Get recent alerts.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of recent alerts
        """
        return self.alerts[-limit:]


def init_monitoring(app, logger=None):
    """Initialize all monitoring components.
    
    Args:
        app: Flask application
        logger: Logger instance (optional)
        
    Returns:
        Tuple of (metrics_collector, health_monitor, alert_manager)
    """
    logger = logger or logging.getLogger(__name__)
    
    metrics = MetricsCollector()
    health = HealthMonitor(app, logger)
    alerts = AlertManager(logger)
    
    logger.info("Monitoring initialized")
    
    return metrics, health, alerts
