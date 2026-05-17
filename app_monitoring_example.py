"""Example of how to integrate monitoring into the Flask app.

This file demonstrates how to use the monitoring and logging modules
in your Ani Flask application.
"""

from flask import Flask, request, jsonify
from logging_config import setup_logging, get_logger, PerformanceLogger, RequestLogger
from monitoring import init_monitoring
import os


def create_app():
    """Create and configure Flask app with monitoring."""
    app = Flask(__name__)
    
    # Setup logging
    setup_logging(os.getenv('LOG_LEVEL', 'INFO'))
    logger = get_logger(__name__)
    
    # Initialize monitoring
    metrics, health, alerts = init_monitoring(app, logger)
    
    # Add request/response logging
    RequestLogger(app, logger)
    
    # Store monitoring objects in app context
    app.metrics = metrics
    app.health = health
    app.alerts = alerts
    
    logger.info("Flask app created with monitoring")
    
    # Example endpoint with performance monitoring
    @app.route('/api/chat', methods=['POST'])
    def chat():
        """Chat endpoint with performance monitoring."""
        logger = get_logger(__name__)
        
        with PerformanceLogger(logger, 'chat_endpoint', threshold_ms=500):
            data = request.get_json()
            
            if not data or 'message' not in data:
                logger.warning("Chat request missing message field")
                app.metrics.increment_counter('chat_errors')
                return {'error': 'message field required'}, 400
            
            message = data['message'].strip()
            
            if not message:
                logger.warning("Chat request with empty message")
                app.metrics.increment_counter('chat_empty_messages')
                return {'error': 'message cannot be empty'}, 400
            
            # Record metric
            app.metrics.increment_counter('chat_requests')
            app.metrics.record_metric('message_length', len(message))
            
            # Your AI logic here
            logger.info(f"Processing chat message from {request.remote_addr}")
            
            return {
                'user_query': message,
                'ai_response': 'I am Ani, your AI assistant!',
                'source': 'AI Response',
            }
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        health_status = app.health.get_health()
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
    
    # Metrics endpoint
    @app.route('/metrics', methods=['GET'])
    def metrics_endpoint():
        """Expose metrics."""
        format_type = request.args.get('format', 'json')
        
        if format_type == 'prometheus':
            return app.metrics.export_metrics('prometheus'), 200, {'Content-Type': 'text/plain'}
        
        return jsonify(app.metrics.export_metrics('json')), 200
    
    # Alerts endpoint
    @app.route('/alerts', methods=['GET'])
    def alerts_endpoint():
        """Get recent alerts."""
        limit = request.args.get('limit', 50, type=int)
        return jsonify(app.alerts.get_recent_alerts(limit)), 200
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=False, host='0.0.0.0', port=5000)
