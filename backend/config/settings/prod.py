"""
Django Production Settings for Gastrotech.

This file extends base.py with production-specific settings.
Security hardening and performance optimizations are applied here.

IMPORTANT: All required environment variables are validated at startup.
"""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401, F403

# ==============================================================================
# ENVIRONMENT VALIDATION
# ==============================================================================

def _validate_env_vars():
    """
    Validate required environment variables at startup.
    
    Raises ImproperlyConfigured if any critical variable is missing.
    """
    required_vars = {
        "DJANGO_SECRET_KEY": SECRET_KEY,  # noqa: F405
        "DATABASE_URL": env("DATABASE_URL", default=""),  # noqa: F405
        "REDIS_URL": env("REDIS_URL", default=""),  # noqa: F405
    }
    
    missing = []
    
    for var_name, value in required_vars.items():
        if not value or value in ["", "change-me-in-production", "sqlite:///db.sqlite3"]:
            missing.append(var_name)
    
    if missing:
        raise ImproperlyConfigured(
            f"Production requires the following environment variables: {', '.join(missing)}. "
            "Set them in your environment or .env file."
        )


# Run validation immediately
_validate_env_vars()

# ==============================================================================
# CORE SECURITY
# ==============================================================================

DEBUG = False

# Ensure SECRET_KEY is properly set in production
if SECRET_KEY == "change-me-in-production":  # noqa: F405
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set in production!")

if len(SECRET_KEY) < 50:  # noqa: F405
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be at least 50 characters. "
        "Generate one with: python -c \"from django.core.management.utils import "
        "get_random_secret_key; print(get_random_secret_key())\""
    )

# ==============================================================================
# ALLOWED HOSTS & CSRF
# ==============================================================================

# ALLOWED_HOSTS from env (already set in base.py, but ensure it's not default)
if ALLOWED_HOSTS == ["localhost", "127.0.0.1"]:  # noqa: F405
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS must be explicitly set in production. "
        "Example: DJANGO_ALLOWED_HOSTS=gastrotech.com,www.gastrotech.com"
    )

# CSRF Trusted Origins (required for forms from different origins)
CSRF_TRUSTED_ORIGINS = env.list(  # noqa: F405
    "CSRF_TRUSTED_ORIGINS",
    default=[]
)

if not CSRF_TRUSTED_ORIGINS:
    # Derive from ALLOWED_HOSTS if not explicitly set
    # Filter out invalid entries and ensure proper HTTPS prefix
    CSRF_TRUSTED_ORIGINS = []
    for host in ALLOWED_HOSTS:  # noqa: F405
        # Skip localhost, IPs, and already-prefixed URLs
        if host.startswith(('http://', 'https://')):
            continue
        if host in ('localhost', '127.0.0.1') or host.replace('.', '').isdigit():
            continue
        # Add HTTPS prefix for valid domain names only
        CSRF_TRUSTED_ORIGINS.append(f"https://{host}")

# ==============================================================================
# SECURITY HEADERS
# ==============================================================================

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Cookie security - SameSite attributes
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# ==============================================================================
# HTTPS / SSL SETTINGS
# ==============================================================================

# Toggle SSL redirect via env (default True in prod)
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405

# Cookie security (always secure in prod)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS (only when SSL redirect is enabled)
if SECURE_SSL_REDIRECT:
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ==============================================================================
# PROXY SETTINGS (for load balancers/reverse proxies like Nginx)
# ==============================================================================

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# ==============================================================================
# CORS CONFIGURATION
# ==============================================================================

# Strict CORS in production - no wildcards
CORS_ALLOW_ALL_ORIGINS = False

# CORS_ALLOWED_ORIGINS already set in base.py from env
# Validate it's not default
if CORS_ALLOWED_ORIGINS == ["http://localhost:3000"]:  # noqa: F405
    import warnings
    warnings.warn(
        "CORS_ALLOWED_ORIGINS is using default localhost value. "
        "Set CORS_ALLOWED_ORIGINS env var for production.",
        RuntimeWarning,
    )

# ==============================================================================
# DATABASE
# ==============================================================================

# Validate PostgreSQL is used in production
_db_url = env("DATABASE_URL", default="")  # noqa: F405
if "sqlite" in _db_url.lower():
    raise ImproperlyConfigured(
        "PostgreSQL is required in production. SQLite is not permitted. "
        "Set DATABASE_URL=postgres://user:password@host:5432/dbname"
    )

# Connection optimization
DATABASES["default"]["CONN_MAX_AGE"] = 60  # noqa: F405
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True  # noqa: F405

# ==============================================================================
# SESSIONS
# ==============================================================================

# Cache sessions in Redis for performance
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# ==============================================================================
# STATIC FILES
# ==============================================================================

# Whitenoise with compression and manifest
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ==============================================================================
# LOGGING
# ==============================================================================

# Production logging - use JSON formatting for structured logs
from config.logging_config import get_logging_config

LOGGING = get_logging_config(use_json=True)

# Set log levels for production (less verbose)
LOGGING["loggers"]["django"]["level"] = "WARNING"
LOGGING["loggers"]["apps"]["level"] = "INFO"

# ==============================================================================
# EMAIL
# ==============================================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="")  # noqa: F405
EMAIL_PORT = env.int("EMAIL_PORT", default=587)  # noqa: F405
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)  # noqa: F405
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")  # noqa: F405
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")  # noqa: F405
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@gastrotech.com")  # noqa: F405

# ==============================================================================
# ERROR TRACKING (SENTRY)
# ==============================================================================

SENTRY_DSN = env("SENTRY_DSN", default="")  # noqa: F405
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.1),  # noqa: F405
        send_default_pii=False,
        environment=env("SENTRY_ENVIRONMENT", default="production"),  # noqa: F405
    )

# ==============================================================================
# APP VERSION
# ==============================================================================

# App version for health checks and debugging
APP_VERSION = env("APP_VERSION", default="1.0.0")  # noqa: F405
