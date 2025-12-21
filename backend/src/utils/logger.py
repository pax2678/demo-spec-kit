import logging
import sys
from datetime import datetime
from typing import Dict, Any
import json
import os


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class DashboardLogger:
    """Centralized logging configuration for the dashboard application."""
    
    def __init__(self):
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_format = os.getenv("LOG_FORMAT", "json")  # json or text
        self.environment = os.getenv("ENVIRONMENT", "development")
    
    def setup_logging(self) -> logging.Logger:
        """Setup and configure logging."""
        # Remove existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.log_level))
        
        # Set formatter
        if self.log_format == "json":
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger.setLevel(getattr(logging, self.log_level))
        root_logger.addHandler(console_handler)
        
        # Configure specific loggers
        self._configure_loggers()
        
        # Create dashboard logger
        dashboard_logger = logging.getLogger("dashboard")
        dashboard_logger.info(f"Logging configured - Level: {self.log_level}, Format: {self.log_format}")
        
        return dashboard_logger
    
    def _configure_loggers(self):
        """Configure specific logger levels."""
        # Reduce noise from third-party libraries
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        
        # Dashboard-specific loggers
        logging.getLogger("dashboard.auth").setLevel(getattr(logging, self.log_level))
        logging.getLogger("dashboard.metrics").setLevel(getattr(logging, self.log_level))
        logging.getLogger("dashboard.api").setLevel(getattr(logging, self.log_level))
        
        # Production logging adjustments
        if self.environment == "production":
            logging.getLogger("fastapi").setLevel(logging.WARNING)
            logging.getLogger("uvicorn").setLevel(logging.WARNING)
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger instance with the given name."""
        return logging.getLogger(f"dashboard.{name}")


class RequestLogger:
    """Request-specific logger with correlation ID support."""
    
    def __init__(self, logger: logging.Logger, request_id: str = None, user_id: str = None):
        self.logger = logger
        self.request_id = request_id
        self.user_id = user_id
    
    def _add_context(self, extra: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add request context to log record."""
        context = extra or {}
        if self.request_id:
            context['request_id'] = self.request_id
        if self.user_id:
            context['user_id'] = self.user_id
        return context
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self.logger.debug(message, extra=self._add_context(kwargs))
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self.logger.info(message, extra=self._add_context(kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.logger.warning(message, extra=self._add_context(kwargs))
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self.logger.error(message, extra=self._add_context(kwargs))
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        self.logger.critical(message, extra=self._add_context(kwargs))


# Global logger instance
dashboard_logger_config = DashboardLogger()
logger = dashboard_logger_config.setup_logging()

# Convenience functions
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return DashboardLogger.get_logger(name)

def get_request_logger(name: str, request_id: str = None, user_id: str = None) -> RequestLogger:
    """Get a request-specific logger."""
    base_logger = get_logger(name)
    return RequestLogger(base_logger, request_id, user_id)