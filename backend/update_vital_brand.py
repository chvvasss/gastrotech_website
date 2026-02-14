import os
import django

# Setup Django environment
import os
import django

# No extra sys.path needed if we run from backend/ dir
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.catalog.models import Product, Brand, Category, BrandCategory, Media

def run():
    print("Starting VITAL brand update...")
    
    # 1. Get or Create VITAL Brand
    # Try different casing just in case, but usually we want "VITAL" or "Vital"
    # User said "VITAL".
    vital_brand, created = Brand.objects.get_or_create(
        name__iexact="VITAL",
        defaults={'name': 'VITAL', 'slug': 'vital'}
    )
    # If it was found by iexact, get the actual object (in case it was 'Vital')
    if not created:
        vital_brand = Brand.objects.get(name__iexact="VITAL")
        
    print(f"Target Brand: {vital_brand.name} (Created: {created})")

    # 2. Find products with images
    products_with_images = Product.objects.filter(
        product_media__media__kind=Media.Kind.IMAGE
    ).distinct()
    
    print(f"Found {products_with_images.count()} products with images.")
    
    products_updated = 0
    categories_updated = 0
    
    for product in products_with_images:
        # Update Brand
        if product.brand != vital_brand:
            product.brand = vital_brand
            product.save(update_fields=['brand', 'updated_at'])
            products_updated += 1
            
        # Ensure Category <-> Brand link
        # Product -> Series -> Category
        # Also Product -> Category (denormalized)
        
        cats_to_check = set()
        if product.category:
            cats_to_check.add(product.category)
        if product.series and product.series.category:
            cats_to_check.add(product.series.category)
            
        for cat in cats_to_check:
            obj, cat_created = BrandCategory.objects.get_or_create(
                brand=vital_brand,
                category=cat,
                defaults={'is_active': True}
            )
            if cat_created:
                categories_updated += 1
                print(f"  - Linked VITAL to Category: {cat.name}")

    print(f"Done. Updated {products_updated} products and {categories_updated} category links.")

if __name__ == "__main__":
    run()
