"""
Structured logging configuration for production.

Provides JSON-formatted logs with request IDs, performance metrics,
and security event tracking. Uses console-only handlers by default
to work in Docker containers without file system setup.
"""

import logging
import time
from typing import Any, Dict


class RequestIDFilter(logging.Filter):
    """Add request ID to log records."""

    def filter(self, record):
        # Request ID is set by RequestIDMiddleware
        if not hasattr(record, "request_id"):
            record.request_id = "no-request"
        return True


class PerformanceFilter(logging.Filter):
    """Add performance timing to log records."""

    def filter(self, record):
        if not hasattr(record, "duration_ms"):
            record.duration_ms = 0
        return True


class StructuredFormatter(logging.Formatter):
    """
    JSON-formatted log output for structured logging.
    
    Output format:
    {
        "timestamp": "2024-01-11T12:00:00.000Z",
        "level": "INFO",
        "logger": "django.request",
        "message": "Request completed",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "duration_ms": 45,
        "extra": {...}
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        import json
        from django.utils import timezone

        log_data = {
            "timestamp": timezone.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request ID if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Add performance metrics if available
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info",
                "request_id", "duration_ms",
            ]:
                # Only include serializable values
                try:
                    json.dumps(value)
                    extra_fields[key] = value
                except (TypeError, ValueError):
                    extra_fields[key] = str(value)

        if extra_fields:
            log_data["extra"] = extra_fields

        return json.dumps(log_data)


def get_logging_config(use_json: bool = False) -> Dict[str, Any]:
    """
    Get logging configuration with console-only handlers.
    
    Args:
        use_json: If True, use JSON formatter for structured logging
        
    Returns:
        Logging configuration dict (console-only, Docker-friendly)
    """
    formatter = "json" if use_json else "verbose"
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {
                "()": "config.logging_config.RequestIDFilter",
            },
            "performance": {
                "()": "config.logging_config.PerformanceFilter",
            },
        },
        "formatters": {
            "verbose": {
                "format": "{levelname} {asctime} [{request_id}] {name} {message}",
                "style": "{",
            },
            "simple": {
                "format": "{levelname} {message}",
                "style": "{",
            },
            "json": {
                "()": "config.logging_config.StructuredFormatter",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": formatter,
                "filters": ["request_id", "performance"],
            },
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": "INFO",
            },
            "django.request": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "django.security": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "apps": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "performance": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }


class PerformanceLogger:
    """
    Context manager for logging performance metrics.
    
    Usage:
        with PerformanceLogger("database_query", threshold_ms=100):
            # Your code here
            pass
    """

    def __init__(self, operation: str, threshold_ms: int = 1000):
        self.operation = operation
        self.threshold_ms = threshold_ms
        self.start_time = None
        self.logger = logging.getLogger("performance")

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000

        # Log if exceeds threshold
        if duration_ms > self.threshold_ms:
            self.logger.warning(
                f"Slow operation: {self.operation}",
                extra={
                    "operation": self.operation,
                    "duration_ms": round(duration_ms, 2),
                    "threshold_ms": self.threshold_ms,
                },
            )
        else:
            self.logger.info(
                f"Operation completed: {self.operation}",
                extra={
                    "operation": self.operation,
                    "duration_ms": round(duration_ms, 2),
                },
            )


class SecurityLogger:
    """Helper class for logging security events."""

    def __init__(self):
        self.logger = logging.getLogger("django.security")

    def log_failed_login(self, email: str, ip: str, reason: str = "invalid_credentials"):
        """Log failed login attempt."""
        self.logger.warning(
            f"Failed login attempt for {email}",
            extra={
                "event": "failed_login",
                "email": email,
                "ip": ip,
                "reason": reason,
            },
        )

    def log_suspicious_activity(self, user: str, activity: str, details: dict):
        """Log suspicious activity."""
        self.logger.warning(
            f"Suspicious activity: {activity}",
            extra={
                "event": "suspicious_activity",
                "user": str(user),
                "activity": activity,
                **details,
            },
        )

    def log_permission_denied(self, user: str, resource: str, action: str):
        """Log permission denied event."""
        self.logger.info(
            f"Permission denied for {user}",
            extra={
                "event": "permission_denied",
                "user": str(user),
                "resource": resource,
                "action": action,
            },
        )

    def log_rate_limit_exceeded(self, identifier: str, endpoint: str):
        """Log rate limit exceeded event."""
        self.logger.warning(
            f"Rate limit exceeded for {identifier}",
            extra={
                "event": "rate_limit_exceeded",
                "identifier": identifier,
                "endpoint": endpoint,
            },
        )


# Singleton instances
security_logger = SecurityLogger()
