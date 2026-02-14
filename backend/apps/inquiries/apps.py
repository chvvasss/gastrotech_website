"""
Inquiries app configuration.
"""

from django.apps import AppConfig


class InquiriesConfig(AppConfig):
    """Configuration for the inquiries app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.inquiries"
    verbose_name = "B2B Inquiries"
