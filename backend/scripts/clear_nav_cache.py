
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.cache_keys import clear_nav_cache

def clear_cache():
    print("=== Clearing Navigation Cache ===")
    clear_nav_cache()
    print("✓ Navigation cache cleared successfully")
    print("\nNext: Visit http://localhost:8000/api/v1/nav/ to verify")

if __name__ == "__main__":
    clear_cache()
