
import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ["DATABASE_URL"] = "postgres://postgres:postgres@localhost:5432/gastrotech"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import CategoryCatalog
from apps.common.models import SiteSetting

def run():
    # 1. Publish all catalogs (ensure True)
    count = CategoryCatalog.objects.update(published=True)
    print(f"Published {count} catalogs.")

    # 2. Enable Catalog Mode
    try:
        setting, created = SiteSetting.objects.get_or_create(key="catalog_mode")
        setting.value = True # Assuming JSONField or similar
        setting.description = "Global catalog mode setting"
        setting.save()
        print(f"Enabled Catalog Mode in SiteSetting (created={created}).")
        
        # Verify
        print(f"Current value: {setting.value}")

    except Exception as e:
        print("Could not update SiteSetting:", e)

if __name__ == "__main__":
    run()
