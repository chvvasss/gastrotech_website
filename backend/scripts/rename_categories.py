import os
import sys
import django
from pathlib import Path
from django.db import transaction

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import Category, CategoryCatalog, Product, Series

# Old Slug -> New Slug, New Name
RENAME_MAP = {
    "bulasik-yikama": ("bulasik", "Bulaşık"),
    "camasirhane-ekipmanlari": ("camasirhane", "Çamaşırhane"),
    "hazirlik-ekipmanlari": ("hazirlik", "Hazırlık"),
    "pisirme-uniteleri": ("pisirme", "Pişirme"),
    "sogutma-grubu": ("sogutma", "Soğutma"),
    "kafeterya-ekipmanlari": ("kafeterya", "Kafeterya"),
    "tamamlayici-urunler": ("tamamlayici", "Tamamlayıcı"),
}

@transaction.atomic
def run():
    print("--- Categories Renaming Migration ---")
    
    for old_slug, (new_slug, new_name) in RENAME_MAP.items():
        print(f"\nProcessing '{old_slug}' -> '{new_slug}' ({new_name})")
        
        old_cat = Category.objects.filter(slug=old_slug).first()
        new_cat = Category.objects.filter(slug=new_slug).first()
        
        if not old_cat:
            print(f"  [SKIP] Old category '{old_slug}' not found.")
            if new_cat:
                 # Just ensure name is correct
                 if new_cat.name != new_name:
                     new_cat.name = new_name
                     new_cat.save()
                     print(f"  [UPDATE] Updated existing new category name to '{new_name}'")
            continue
            
        if new_cat:
            print(f"  [MERGE] Target category '{new_slug}' already exists. Merging...")
            # Move contents from old to new
            
            # 1. Products
            products = Product.objects.filter(category=old_cat)
            count_p = products.count()
            products.update(category=new_cat)
            print(f"  - Moved {count_p} products.")
            
            # 2. Series
            series = Series.objects.filter(category=old_cat)
            count_s = series.count()
            series.update(category=new_cat)
            print(f"  - Moved {count_s} series.")
            
            # 3. Catalogs
            catalogs = CategoryCatalog.objects.filter(category=old_cat)
            count_c = catalogs.count()
            catalogs.update(category=new_cat)
            print(f"  - Moved {count_c} catalogs.")
            
            # Delete old
            print(f"  [DELETE] Deleting old category '{old_slug}'")
            old_cat.delete()
            
        else:
            print(f"  [RENAME] Renaming '{old_slug}' -> '{new_slug}'")
            old_cat.slug = new_slug
            old_cat.name = new_name
            old_cat.save()

    print("\nMigration Completed.")

if __name__ == "__main__":
    run()
