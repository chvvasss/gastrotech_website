
import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import CategoryCatalog

def run():
    catalogs = CategoryCatalog.objects.all().select_related('category', 'media')
    print(f"Found {catalogs.count()} catalogs:")
    for c in catalogs:
        print(f"  [{c.category.slug}] {c.title_tr} -> Media: {c.media.filename} (Size: {len(c.media.bytes)} bytes)")
        # Check if media has a url property/method
        if hasattr(c.media, 'url'):
             print(f"    Media URL: {c.media.url}")
        elif hasattr(c.media, 'file'):
             print(f"    Media File URL: {c.media.file.url}")

if __name__ == "__main__":
    run()
