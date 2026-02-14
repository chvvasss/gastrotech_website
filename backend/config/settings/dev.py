"""
Django Development Settings for Gastrotech.

This file extends base.py with development-specific settings.
"""

import os

from .base import *  # noqa: F401, F403

# Development-specific settings
DEBUG = True

# =====================
# APPEND_SLASH = False (DEMO/DEV ONLY)
# POST isteklerinde trailing slash olmadan da çalışsın
# Production'da True olmalı, URL'ler düzgün tanımlanmalı
# =====================
APPEND_SLASH = False

# =====================
# ALLOWED_HOSTS - Environment'tan gelenleri EKLER (override etmez)
# docker-compose.yml'den DJANGO_ALLOWED_HOSTS okunur ve buradaki listeye eklenir
# =====================
_env_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".ngrok-free.app",
    ".ngrok-free.dev",  # Tüm ngrok subdomainleri
    "nonrecalcitrant-pluggingly-phillis.ngrok-free.dev",
    "80bb2c15cb12.ngrok-free.app",  # New dynamic domain
]

if _env_hosts:
    # Comma-separated string'i list'e çevir ve mevcuda ekle
    _env_host_list = [h.strip() for h in _env_hosts.split(",") if h.strip()]
    ALLOWED_HOSTS.extend(_env_host_list)
    # Tekrarları temizle
    ALLOWED_HOSTS = list(set(ALLOWED_HOSTS))

# Add browsable API renderer for development
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# Email backend for development (prints to console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable SSL/HTTPS requirements in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True
# Note: CORS_ALLOW_HEADERS already defined in base.py

# =====================
# NGROK DEMO AYARLARI
# CSRF Trusted Origins - Ngrok ve localhost için
# =====================
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    # Ngrok wildcard - tüm ngrok-free.dev subdomainleri
    "https://*.ngrok-free.app",
    "https://*.ngrok-free.dev",
    "https://nonrecalcitrant-pluggingly-phillis.ngrok-free.dev",
    "https://80bb2c15cb12.ngrok-free.app",  # New dynamic domain
]

# CSRF cookie ayarları - Ngrok HTTPS terminates ettiği için
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_USE_SESSIONS = False

# Simplified static files handling for development
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Debug logging
LOGGING["loggers"]["django"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405
