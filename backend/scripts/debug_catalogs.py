
import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ["DATABASE_URL"] = "postgres://postgres:postgres@localhost:5432/gastrotech"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import CategoryCatalog, Category
from apps.common.utils import get_catalog_mode
from django.db import connection

def run():
    print(f"DB Name: {connection.settings_dict['NAME']}")
    print(f"Catalog Mode: {get_catalog_mode()}")
    
    print("\n--- Catalogs ---")
    catalogs = CategoryCatalog.objects.all()
    for c in catalogs:
        print(f"ID: {c.id}, Published: {c.published}, Category Slug: '{c.category.slug}', Title: '{c.title_tr}'")

    print("\n--- Category: firinlar ---")
    try:
        cat = Category.objects.get(slug="firinlar")
        print(f"Found Category: {cat.name}, Slug: {cat.slug}, ID: {cat.id}")
        cat_catalogs = CategoryCatalog.objects.filter(category=cat)
        print(f"Catalogs linked to this category: {cat_catalogs.count()}")
    except Category.DoesNotExist:
        print("Category 'firinlar' NOT FOUND.")
        # Suggest close matches
        print("Closest matches:")
        for c in Category.objects.filter(slug__icontains="firin"):
             print(f"- {c.name} ({c.slug})")

if __name__ == "__main__":
    run()
