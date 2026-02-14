
import os
import sys
import django

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.catalog.models import Product, Series

def audit_900_series_images():
    # Series can be non-unique by slug (scoped to category)
    series_list = Series.objects.filter(slug="900-serisi")
    if not series_list.exists():
        print("Series '900-serisi' not found.")
        return

    # Products in 900 Series (across any category having this series)
    products = Product.objects.filter(series__in=series_list)
    
    missing_images = []
    
    for p in products:
        if not p.product_media.exists():
            # Get variants to show codes and dimensions
            variants = p.variants.all()
            if variants:
                for v in variants:
                    missing_images.append({
                        "name": p.name,
                        "code": v.model_code,
                        "dims": v.dimensions or "N/A"
                    })
            else:
                # Fallback if no variants (unlikely but possible)
                missing_images.append({
                    "name": p.name,
                    "code": p.slug, # Fallback
                    "dims": "N/A"
                })

    print(f"--- 900 Serisi: Görseli Olmayan Ürünler ({len(missing_images)}) ---")
    print(f"{'Ürün Adı':<40} | {'Model Kodu':<20} | {'Ölçüler'}")
    print("-" * 80)
    
    for item in missing_images:
        print(f"{item['name'][:38]:<40} | {item['code']:<20} | {item['dims']}")

if __name__ == "__main__":
    audit_900_series_images()
