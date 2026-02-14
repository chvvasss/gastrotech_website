"""
Custom logging utilities for Gastrotech.

Includes:
- JsonFormatter: JSON-formatted log output for production
- PerformanceLogger: Context manager for timing operations
- SecurityLogger: Specialized logging for security events
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging in production.

    Output format:
    {
        "timestamp": "2024-01-15T10:30:00.000Z",
        "level": "INFO",
        "request_id": "abc123",
        "message": "...",
        "module": "views",
        "extra": {...}
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "request_id": getattr(record, "request_id", "no-request"),
            "message": record.getMessage(),
            "module": record.module,
            "logger": record.name,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "request_id", "message",
            ):
                extra_fields[key] = value

        if extra_fields:
            log_data["extra"] = extra_fields

        return json.dumps(log_data, default=str)


class PerformanceLogger:
    """
    Context manager for logging operation performance.

    Usage:
        with PerformanceLogger("database_query", threshold_ms=100):
            result = db.query(...)

    Logs warning if operation exceeds threshold.
    """

    def __init__(
        self,
        operation: str,
        threshold_ms: int = 1000,
        logger: Optional[logging.Logger] = None,
        **extra,
    ):
        self.operation = operation
        self.threshold_ms = threshold_ms
        self.logger = logger or logging.getLogger(__name__)
        self.extra = extra
        self.start_time: Optional[float] = None

    def __enter__(self) -> "PerformanceLogger":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.start_time is None:
            return

        duration_ms = (time.perf_counter() - self.start_time) * 1000

        log_data = {
            "operation": self.operation,
            "duration_ms": round(duration_ms, 2),
            **self.extra,
        }

        if duration_ms > self.threshold_ms:
            self.logger.warning(
                f"Slow operation: {self.operation} took {duration_ms:.2f}ms "
                f"(threshold: {self.threshold_ms}ms)",
                extra=log_data,
            )
        else:
            self.logger.debug(
                f"Operation: {self.operation} completed in {duration_ms:.2f}ms",
                extra=log_data,
            )


class SecurityLogger:
    """
    Specialized logger for security-related events.

    Usage:
        security_log = SecurityLogger()
        security_log.failed_login(username="user@example.com", ip="1.2.3.4")
        security_log.rate_limit_exceeded(endpoint="/api/login", ip="1.2.3.4")
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("security")

    def failed_login(self, username: str, ip: str, reason: str = "invalid_credentials"):
        """Log failed login attempt."""
        self.logger.warning(
            f"Failed login attempt for {username} from {ip}: {reason}",
            extra={
                "event": "failed_login",
                "username": username,
                "ip": ip,
                "reason": reason,
            },
        )

    def successful_login(self, username: str, ip: str):
        """Log successful login."""
        self.logger.info(
            f"Successful login for {username} from {ip}",
            extra={
                "event": "successful_login",
                "username": username,
                "ip": ip,
            },
        )

    def rate_limit_exceeded(self, endpoint: str, ip: str, limit: str):
        """Log rate limit exceeded."""
        self.logger.warning(
            f"Rate limit exceeded for {endpoint} from {ip}: {limit}",
            extra={
                "event": "rate_limit_exceeded",
                "endpoint": endpoint,
                "ip": ip,
                "limit": limit,
            },
        )

    def suspicious_activity(self, description: str, ip: str, **details):
        """Log suspicious activity."""
        self.logger.warning(
            f"Suspicious activity from {ip}: {description}",
            extra={
                "event": "suspicious_activity",
                "ip": ip,
                "description": description,
                **details,
            },
        )

    def upload_rejected(self, filename: str, reason: str, ip: str):
        """Log rejected file upload."""
        self.logger.warning(
            f"Upload rejected: {filename} - {reason} (from {ip})",
            extra={
                "event": "upload_rejected",
                "filename": filename,
                "reason": reason,
                "ip": ip,
            },
        )
