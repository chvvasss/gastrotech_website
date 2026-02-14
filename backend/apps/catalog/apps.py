"""
Catalog app configuration.
"""

from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """Configuration for the catalog app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalog"
    verbose_name = "Product Catalog"
    
    def ready(self):
        """Connect signal handlers when app is ready."""
        # Import signals to register handlers
        # This is done inside ready() to avoid circular imports
        try:
            from . import signals  # noqa: F401
        except ImportError:
            pass
