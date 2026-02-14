"""
API v1 views.

This module contains shared views for the API v1 endpoints.
"""

import logging

from django.conf import settings
from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring and orchestration.

    This endpoint checks the status of the database and Redis connections
    and returns a JSON response indicating the health of each service.

    GET /api/v1/health/
    Returns: {"status": "ok", "db": true/false, "redis": true/false, "version": "1.0.0", "api": "v1"}
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="Health Check",
        description=(
            "Check the health of the API and its dependencies (database, Redis). "
            "Returns app version from APP_VERSION environment variable."
        ),
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "ok"},
                    "db": {"type": "boolean", "example": True},
                    "redis": {"type": "boolean", "example": True},
                    "version": {"type": "string", "example": "1.0.0"},
                    "api": {"type": "string", "example": "v1"},
                },
            },
        },
        tags=["Health"],
        auth=[],  # Public endpoint - no authentication required
    )
    def get(self, request):
        """Check health of all services."""
        # Get app version from settings (set in prod.py from APP_VERSION env)
        app_version = getattr(settings, "APP_VERSION", "dev")
        
        health_status = {
            "status": "ok",
            "db": self._check_database(),
            "redis": self._check_redis(),
            "version": app_version,
            "api": "v1",
        }

        # Set overall status based on service health
        if not health_status["db"] or not health_status["redis"]:
            health_status["status"] = "degraded"

        return Response(health_status, status=status.HTTP_200_OK)

    def _check_database(self) -> bool:
        """Check database connectivity."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def _check_redis(self) -> bool:
        """Check Redis connectivity."""
        try:
            from django.core.cache import cache

            cache.set("health_check", "ok", timeout=10)
            result = cache.get("health_check")
            return result == "ok"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
