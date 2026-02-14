
import os
import sys
import django

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Product, Variant, Media, ProductMedia

def fix_product_391155():
    print("--- Fixing Product 391155 ---")
    
    # 1. Find Product
    try:
        variant = Variant.objects.get(model_code='391155')
        product = variant.product
        print(f"Target Product: {product.title_tr} (ID: {product.id})")
    except Variant.DoesNotExist:
        print("ERROR: Variant 391155 NOT FOUND")
        return

    # 2. Find Media
    media_file = Media.objects.filter(filename='391155_Kapaksiz_Alt_Stand.jpg').first()
    if not media_file:
         # Fallback search
         media_file = Media.objects.filter(filename__icontains='391155').first()
    
    if not media_file:
        print("ERROR: Media file not found!")
        return
        
    print(f"Target Media: {media_file.filename} (ID: {media_file.id})")

    # 3. Create Link
    # Check if already exists
    link, created = ProductMedia.objects.get_or_create(
        product=product,
        media=media_file,
        defaults={
            'is_primary': True,
            'sort_order': 0,
            'variant': variant # Also link to the specific variant to be safe
        }
    )
    
    if created:
        print("SUCCESS: Created new ProductMedia link.")
    else:
        print("INFO: ProductMedia link already existed. Updating to primary.")
        link.is_primary = True
        link.variant = variant
        link.save()

    print("--- Verification ---")
    print(f"Product {product.title_tr} has {product.product_media.count()} images.")
    pm = product.product_media.first()
    print(f"Primary Image: {pm.media.filename} (Primary: {pm.is_primary})")

if __name__ == "__main__":
    fix_product_391155()
