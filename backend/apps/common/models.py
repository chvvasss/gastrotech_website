"""
Common models and base classes for Gastrotech.

This module provides abstract base models that are used across the application
to ensure consistent behavior and reduce code duplication.
"""

import uuid

from django.db import models


class TimeStampedUUIDModel(models.Model):
    """
    Abstract base model with UUID primary key and timestamp fields.

    This model provides:
    - `id`: UUID primary key (auto-generated)
    - `created_at`: Timestamp when the record was created
    - `updated_at`: Timestamp when the record was last updated

    All models that need these fields should inherit from this class.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this record",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when this record was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this record was last updated",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.id)


class SiteSetting(TimeStampedUUIDModel):
    """
    Global site settings.

    Stores configuration values like 'show_prices'.
    Designed to be cached heavily.
    """
    key = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique key for the setting (e.g. 'show_prices')",
    )
    value = models.JSONField(
        default=dict,
        help_text="JSON value for the setting",
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Human-readable description",
    )

    def __str__(self):
        return self.key
