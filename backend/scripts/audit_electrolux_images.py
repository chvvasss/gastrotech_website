
import os
import sys
import django

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.catalog.models import Product, Brand

def audit_electrolux_images():
    # Find brand (handle verify slug)
    try:
        brand = Brand.objects.get(slug="electrolux")
    except Brand.DoesNotExist:
        # Try finding by name if slug differs
        brand = Brand.objects.filter(name__icontains="Electrolux").first()
        if not brand:
            print("Brand 'Electrolux' not found.")
            return

    print(f"Auditing products for brand: {brand.name} ({brand.slug})")

    # Products for this brand
    products = Product.objects.filter(brand=brand)
    
    missing_images = []
    
    for p in products:
        if not p.product_media.exists():
            # Get variants to show codes and dimensions
            variants = p.variants.all()
            if variants:
                for v in variants:
                    # Prefer descriptive title
                    display_name = p.title_tr or p.title_en or p.name
                    missing_images.append({
                        "name": display_name,
                        "code": v.model_code,
                        "dims": v.dimensions or "N/A"
                    })
            else:
                display_name = p.title_tr or p.title_en or p.name
                missing_images.append({
                    "name": display_name,
                    "code": p.slug, 
                    "dims": "N/A"
                })

    print(f"--- Electrolux: Görseli Olmayan Ürünler ({len(missing_images)}) ---")
    print(f"{'Ürün Adı':<60} | {'Model Kodu':<20} | {'Ölçüler'}")
    print("-" * 100)
    
    for item in missing_images:
        print(f"{item['name'][:58]:<60} | {item['code']:<20} | {item['dims']}")

if __name__ == "__main__":
    audit_electrolux_images()
