"""
URL configuration for Gastrotech project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def api_root(request):
    """Root URL handler - returns API info instead of 404."""
    return JsonResponse({
        "service": "Gastrotech API",
        "version": "1.0.0",
        "endpoints": {
            "api": "/api/v1/",
            "health": "/api/v1/health/",
            "docs": "/api/v1/docs/",
        },
    })


urlpatterns = [
    # Root URL - API info
    path("", api_root),
    # Django Admin
    path("admin/", admin.site.urls),
    # API v1
    path("api/v1/", include("apps.api.v1.urls")),
    path("api/v1/common/", include("apps.common.api.urls")),
]

# Serve media files (QR codes, PDFs, etc.)
# In production, nginx proxies /media/ to Django since there is no
# separate nginx container — gunicorn handles media serving directly.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

