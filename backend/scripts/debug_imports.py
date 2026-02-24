import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from django.urls import include, path
from importlib import import_module

modules_to_test = [
    "config.urls",
    "apps.api.v1.urls",
    "apps.common.api.urls",
    "apps.orders.urls",
    "apps.catalog.urls",
    "apps.blog.urls",
    "apps.catalog.admin_urls",
    "apps.inquiries.admin_urls",
    "apps.ops.urls",
    "apps.blog.admin_urls",
    "apps.inquiries.urls",
]

print("Testing imports...")
for module_name in modules_to_test:
    try:
        print(f"Importing {module_name}...", end="")
        import_module(module_name)
        print(" OK")
    except Exception as e:
        print(f" FAIL")
        print(f"Error importing {module_name}: {e}")
        import traceback
        traceback.print_exc()
