
import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.core.cache import cache
from apps.catalog.models import Category, CategoryCatalog, Series
from apps.catalog.models import Product

# Strategy: For each pair, keep the one with products/series, move catalogs to it, delete the empty one.
# Determined by checking which slug has products:
#
# camasirhane (4 products) <-- KEEP, camasirhane-ekipmanlari (0 products) <-- DELETE
# hazirlik-ekipmanlari (19 products) <-- KEEP, hazirlik (0 products) <-- DELETE
# kafeterya-ekipmanlari (84 products) <-- KEEP, kafeterya (0 products) <-- DELETE
# pisirme-uniteleri (109 products) <-- KEEP, pisirme (0 products) <-- DELETE
# sogutma-uniteleri (43 products) <-- KEEP, sogutma (0 products) <-- DELETE
# tamamlayici-ekipmanlar (25 products) <-- KEEP, tamamlayici (0 products) <-- DELETE
# firinlar (11 products) <-- already correct, only has its own catalog

# Mapping: empty_slug_to_delete -> slug_with_products_to_keep
MAPPING = {
    "camasirhane-ekipmanlari": "camasirhane",
    "hazirlik":                "hazirlik-ekipmanlari",
    "kafeterya":               "kafeterya-ekipmanlari",
    "pisirme":                 "pisirme-uniteleri",
    "sogutma":                 "sogutma-uniteleri",
    "tamamlayici":             "tamamlayici-ekipmanlar",
}

def run():
    moved = 0
    deleted_cats = 0

    for empty_slug, keep_slug in MAPPING.items():
        empty_cat = Category.objects.filter(slug=empty_slug).first()
        keep_cat = Category.objects.filter(slug=keep_slug).first()

        if not empty_cat:
            print(f"[SKIP] Category '{empty_slug}' not found (already deleted?)")
            continue
        if not keep_cat:
            print(f"[ERROR] Target category '{keep_slug}' not found!")
            continue

        # Safety check: make sure the "empty" one truly has no products/series
        series_count = Series.objects.filter(category=empty_cat).count()
        product_count = Product.objects.filter(category=empty_cat).count()
        if series_count > 0 or product_count > 0:
            print(f"[ERROR] '{empty_slug}' has {series_count} series and {product_count} products! Cannot delete. Skipping.")
            continue

        # Move all catalogs from empty to keep
        catalogs = CategoryCatalog.objects.filter(category=empty_cat)
        count = catalogs.count()
        if count > 0:
            catalogs.update(category=keep_cat)
            moved += count
            print(f"[MOVE] {count} catalog(s): {empty_slug} -> {keep_slug}")
        else:
            print(f"[INFO] No catalogs in '{empty_slug}' to move")

        # Delete the empty category
        empty_cat.delete()
        deleted_cats += 1
        print(f"[DELETE] Category '{empty_slug}' deleted")

    # Clear cache
    cache.clear()
    print(f"\n[CACHE] Redis cache cleared")
    print(f"\nDone: {moved} catalogs moved, {deleted_cats} duplicate categories deleted")

    # Print final state
    print("\n--- Final Categories ---")
    for c in Category.objects.all().order_by('slug'):
        s = Series.objects.filter(category=c).count()
        p = Product.objects.filter(category=c).count()
        cat = CategoryCatalog.objects.filter(category=c).count()
        print(f"  {c.slug:30s} | {c.name:30s} | series={s:3d} | products={p:4d} | catalogs={cat:2d}")

if __name__ == "__main__":
    run()
