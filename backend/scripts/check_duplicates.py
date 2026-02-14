import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import Category, CategoryCatalog

def run():
    print("\n--- ALL Categories ---")
    categories = Category.objects.all().order_by('slug')
    for cat in categories:
        parent_slug = cat.parent.slug if cat.parent else "None"
        catalog_count = CategoryCatalog.objects.filter(category=cat).count()
        print(f"Slug: {cat.slug:<30} | Name: {cat.name:<30} | Parent: {parent_slug:<15} | Catalogs: {catalog_count} | ID: {cat.id}")

if __name__ == "__main__":
    run()
