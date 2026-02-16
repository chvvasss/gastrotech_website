"""
ASGI config for Gastrotech project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import sys

from django.core.asgi import get_asgi_application

if "DJANGO_SETTINGS_MODULE" not in os.environ:
    print(
        "ERROR: DJANGO_SETTINGS_MODULE environment variable is not set.\n"
        "Set it to 'config.settings.dev' or 'config.settings.prod'.",
        file=sys.stderr,
    )
    sys.exit(1)

application = get_asgi_application()
