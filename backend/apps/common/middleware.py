"""
Common middleware for Gastrotech.

Includes:
- RequestIDMiddleware: Attach X-Request-ID to requests and responses for tracing
"""

import logging
import threading
import uuid

logger = logging.getLogger(__name__)

# Thread-local storage for request ID
_thread_locals = threading.local()


class RequestIDMiddleware:
    """
    Middleware that attaches a unique request ID to each request.
    
    The request ID is:
    - Read from X-Request-ID header if present (from upstream proxy)
    - Generated as UUID4 if not present
    - Added to the response headers
    - Made available in request.request_id for logging
    
    Usage in views:
        request_id = getattr(request, 'request_id', 'unknown')
        logger.info(f"Processing request {request_id}")
    
    Usage in logging (add to log format):
        'format': '[%(request_id)s] %(levelname)s %(message)s'
    """
    
    HEADER_NAME = "X-Request-ID"
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get or generate request ID
        request_id = request.META.get(f"HTTP_{self.HEADER_NAME.upper().replace('-', '_')}")

        if not request_id:
            request_id = str(uuid.uuid4())

        # Attach to request object
        request.request_id = request_id

        # Add to thread-local for logging
        # This allows the request ID to be included in log messages
        _thread_locals.request_id = request_id

        try:
            # Process request
            response = self.get_response(request)

            # Add to response headers
            response[self.HEADER_NAME] = request_id

            return response
        finally:
            # Clean up thread-local to prevent memory leaks
            if hasattr(_thread_locals, 'request_id'):
                delattr(_thread_locals, 'request_id')


class RequestIDFilter(logging.Filter):
    """
    Logging filter that adds request_id to log records.
    
    Add to logging config:
        'filters': {
            'request_id': {
                '()': 'apps.common.middleware.RequestIDFilter',
            }
        }
    
    Then use in format:
        'format': '[{request_id}] {levelname} {message}'
    """
    
    def filter(self, record):
        # Try to get request_id from thread local or use 'no-request'
        record.request_id = getattr(_thread_locals, 'request_id', 'no-request')
        return True
