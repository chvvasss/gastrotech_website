"""
URL configuration for ops admin API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuditLogViewSet
from .import_api import ImportJobViewSet

router = DefaultRouter(trailing_slash=True)
router.register("import-jobs", ImportJobViewSet, basename="import-jobs")
router.register("audit-logs", AuditLogViewSet, basename="audit-logs")

urlpatterns = [
    path("", include(router.urls)),
]
