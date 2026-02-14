"""
Management command to ensure a dev admin user exists.
ONLY runs in development mode (DEBUG=True or DJANGO_ENV=dev).
"""

import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

DEV_ADMIN_EMAIL = "admin@gastrotech.com"
DEV_ADMIN_PASSWORD = "admin123"


class Command(BaseCommand):
    help = "Ensure dev admin user exists (only in development mode)"

    def handle(self, *args, **options):
        # Check if we're in development mode
        django_env = os.environ.get("DJANGO_ENV", "").lower()
        is_dev = django_env == "dev" or django_env == "development" or settings.DEBUG

        if not is_dev:
            self.stdout.write(
                self.style.WARNING(
                    "Skipping: Not in development mode (DEBUG=False, DJANGO_ENV != dev)"
                )
            )
            return

        self.stdout.write(f"Ensuring dev admin user: {DEV_ADMIN_EMAIL}")

        try:
            user = User.objects.get(email=DEV_ADMIN_EMAIL)
            # User exists, update password and permissions
            user.set_password(DEV_ADMIN_PASSWORD)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated existing user: {DEV_ADMIN_EMAIL} (password reset, superuser=True)"
                )
            )
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_superuser(
                email=DEV_ADMIN_EMAIL,
                password=DEV_ADMIN_PASSWORD,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created new superuser: {DEV_ADMIN_EMAIL}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Dev admin ready:\n"
                f"  Email: {DEV_ADMIN_EMAIL}\n"
                f"  Password: {DEV_ADMIN_PASSWORD}\n"
                f"  is_staff: True\n"
                f"  is_superuser: True"
            )
        )
