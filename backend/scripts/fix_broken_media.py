import os
import sys
from pathlib import Path
from django.db.models import Q

sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ["DATABASE_URL"] = "postgres://postgres:postgres@localhost:5432/gastrotech"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from apps.catalog.models import Media, ProductMedia, Brand, Category, Series, CatalogAsset, CategoryCatalog

def run():
    print("=== Fixing Broken Media (A to Z Clean Up) ===\n")
    
    # 1. Identify Empty Media
    print("Identifing empty media...")
    empty_media = Media.objects.filter(Q(bytes=None) | Q(bytes=b''))
    empty_count = empty_media.count()
    print(f"Found {empty_count} media records with no content.")
    
    if empty_count == 0:
        print("No broken media found. Exiting.")
        return

    empty_media_ids = list(empty_media.values_list('id', flat=True))
    
    # 2. Clean up ProductMedia
    print("\nCleaning up ProductMedia...")
    deleted_pm_count, _ = ProductMedia.objects.filter(media_id__in=empty_media_ids).delete()
    print(f"Deleted {deleted_pm_count} broken ProductMedia links.")
    
    # 3. Clean up Brand Logos
    print("Checking Brands...")
    brands = Brand.objects.filter(logo_media_id__in=empty_media_ids)
    print(f"Updating {brands.count()} brands...")
    brands.update(logo_media=None)
    
    # 4. Clean up Category Covers
    print("Checking Categories...")
    cats = Category.objects.filter(cover_media_id__in=empty_media_ids)
    print(f"Updating {cats.count()} categories...")
    cats.update(cover_media=None)
    
    # 5. Clean up Series Covers
    print("Checking Series...")
    series = Series.objects.filter(cover_media_id__in=empty_media_ids)
    print(f"Updating {series.count()} series...")
    series.update(cover_media=None)
    
    # 6. Clean up CatalogAssets (PDFs)
    # If a catalog asset has no media, it's useless. Delete the asset?
    # Or just nullify? If it's a download link, null media means broken link.
    # Better to delete the Asset if it relies on this media.
    print("Checking CatalogAssets...")
    assets = CatalogAsset.objects.filter(media_id__in=empty_media_ids)
    print(f"Deleting {assets.count()} broken catalog assets...")
    assets.delete()
    
    # 7. Clean up CategoryCatalog
    print("Checking CategoryCatalogs...")
    cat_catalogs = CategoryCatalog.objects.filter(media_id__in=empty_media_ids)
    print(f"Deleting {cat_catalogs.count()} broken category catalogs...")
    cat_catalogs.delete()
    
    # 8. Delete the Empty Media records
    print("\nDeleting empty Media records...")
    deleted_media_count, _ = empty_media.delete()
    print(f"Deleted {deleted_media_count} empty Media records.")
    
    print("\n=== Fix Complete ===")
    print("Broken images should now disappear (replaced by placeholders or nothing).")

if __name__ == "__main__":
    run()
