"""
User models for the accounts app.

This module provides a custom user model with email-based authentication
and role-based access control.
"""

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with email as the primary identifier.

    This model uses email instead of username for authentication and
    includes a role field for basic role-based access control.

    Attributes:
        id: UUID primary key
        email: Unique email address (used for login)
        first_name: User's first name
        last_name: User's last name
        role: User role (admin or editor)
        is_active: Whether the user account is active
        is_staff: Whether the user can access the admin site
        created_at: Timestamp when the user was created
        updated_at: Timestamp when the user was last updated
    """

    class Role(models.TextChoices):
        """User role choices."""

        ADMIN = "admin", "Admin"
        EDITOR = "editor", "Editor"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this user",
    )
    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="Email address (used for login)",
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="User's first name",
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="User's last name",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EDITOR,
        db_index=True,
        help_text="User role for access control",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this user account is active",
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Whether the user can access the admin site",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this user was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this user was last updated",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the user's full name."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def get_short_name(self):
        """Return the user's first name or email."""
        return self.first_name or self.email

    @property
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == self.Role.ADMIN

    @property
    def is_editor(self):
        """Check if user has editor role."""
        return self.role == self.Role.EDITOR
