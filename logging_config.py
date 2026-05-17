"""Logging configuration for production use."""

import os
import logging
import logging.handlers
from pythonjsonlogger import jsonlogger
from datetime import datetime


def setup_logging(log_level=None):
    """Set up comprehensive logging for production.
    
    Supports:
    - Console logging (colored for development)
    - File rotation (daily or size-based)
    - JSON formatting for structured logging
    - Performance metrics
    - Error tracking
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = log_level or os.getenv('LOG_LEVEL', 'INFO')
    log_dir = os.getenv('LOG_DIR', 'logs')
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console Handler (development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # JSON File Handler (structured logging for production)
    json_file = os.path.join(log_dir, 'app.json.log')
    json_handler = logging.handlers.RotatingFileHandler(
        json_file,
        maxBytes=10485760,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    json_handler.setLevel(logging.INFO)
    json_formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        timestamp=True
    )
    json_handler.setFormatter(json_formatter)
    root_logger.addHandler(json_handler)
    
    # Error File Handler (daily rotation)
    error_file = os.path.join(log_dir, f"errors-{datetime.now().strftime('%Y-%m-%d')}.log")
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=5242880,  # 5MB
        backupCount=20,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)
    
    # Performance/Debug File Handler
    debug_file = os.path.join(log_dir, f"debug-{datetime.now().strftime('%Y-%m-%d')}.log")
    debug_handler = logging.handlers.RotatingFileHandler(
        debug_file,
        maxBytes=5242880,  # 5MB
        backupCount=10,
        encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    debug_handler.setFormatter(debug_formatter)
    root_logger.addHandler(debug_handler)
    
    return root_logger


def get_logger(name):
    """Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class PerformanceLogger:
    """Context manager for logging function performance."""
    
    def __init__(self, logger, func_name, threshold_ms=1000):
        """Initialize performance logger.
        
        Args:
            logger: Logger instance
            func_name: Function name being logged
            threshold_ms: Alert if execution exceeds this time (ms)
        """
        self.logger = logger
        self.func_name = func_name
        self.threshold_ms = threshold_ms
        self.start_time = None
    
    def __enter__(self):
        """Start timing."""
        import time
        self.start_time = time.time()
        self.logger.debug(f"Starting {self.func_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log execution time."""
        import time
        elapsed_ms = (time.time() - self.start_time) * 1000
        
        if exc_type:
            self.logger.error(
                f"{self.func_name} failed after {elapsed_ms:.2f}ms: {exc_val}"
            )
        elif elapsed_ms > self.threshold_ms:
            self.logger.warning(
                f"{self.func_name} took {elapsed_ms:.2f}ms (threshold: {self.threshold_ms}ms)"
            )
        else:
            self.logger.debug(
                f"{self.func_name} completed in {elapsed_ms:.2f}ms"
            )


class RequestLogger:
    """Middleware for logging HTTP requests/responses."""
    
    def __init__(self, app, logger=None):
        """Initialize request logger.
        
        Args:
            app: Flask application
            logger: Logger instance (optional)
        """
        self.app = app
        self.logger = logger or get_logger(__name__)
        self.app.before_request(self.log_request)
        self.app.after_request(self.log_response)
    
    def log_request(self):
        """Log incoming requests."""
        from flask import request
        import time
        
        request.start_time = time.time()
        
        self.logger.info(
            f"Incoming request",
            extra={
                "method": request.method,
                "path": request.path,
                "remote_addr": request.remote_addr,
                "user_agent": request.user_agent.string if request.user_agent else None,
            }
        )
    
    def log_response(self, response):
        """Log outgoing responses."""
        from flask import request
        import time
        
        elapsed_ms = (time.time() - request.start_time) * 1000 if hasattr(request, 'start_time') else 0
        
        log_level = logging.INFO
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        
        self.logger.log(
            log_level,
            f"Request completed",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
            }
        )
        
        return response
