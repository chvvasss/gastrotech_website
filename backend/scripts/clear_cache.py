
import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.core.cache import cache

def run():
    print("Clearing cache...")
    cache.clear()
    print("Cache cleared.")
    
    # Also verify catalog_mode
    from apps.common.utils import get_catalog_mode
    mode = get_catalog_mode()
    print(f"Catalog Mode after clear: {mode}")

if __name__ == "__main__":
    run()
