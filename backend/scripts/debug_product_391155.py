
import os
import sys
import django
from django.db.models import Q

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Product, Variant, Media

def debug_product_391155():
    print("--- Debugging Product 391155 ---")
    
    # 1. Find Product
    try:
        variant = Variant.objects.get(model_code='391155')
        product = variant.product
        print(f"FOUND Product: {product.title_tr} (ID: {product.id})")
        print(f"Variant: {variant.model_code} (ID: {variant.id})")
    except Variant.DoesNotExist:
        print("ERROR: Variant 391155 NOT FOUND")
        return

    # 2. Check ProductMedia
    media_links = product.product_media.all()
    print(f"\nExisting ProductMedia Links: {media_links.count()}")
    for pm in media_links:
        print(f"- Media ID: {pm.media.id}")
        print(f"  Filename: {pm.media.filename}")
        print(f"  Is Primary: {pm.is_primary}")
        print(f"  Sort Order: {pm.sort_order}")

    # 3. Search for potential orphan Media
    print("\n--- Searching for Matching Media in Database ---")
    
    # Search for filenames containing 391155
    potential_media = Media.objects.filter(filename__icontains='391155')
    
    if potential_media.exists():
        print(f"Found {potential_media.count()} potential media files:")
        for m in potential_media:
            print(f"- Media ID: {m.id}")
            print(f"  Filename: {m.filename}")
            print(f"  Size: {m.size_bytes} bytes")
            print(f"  Created: {m.created_at}")
            
            # Check if linked to ANY product
            linked_products = m.media_products.all()
            if linked_products.exists():
                print(f"  -> Linked to {linked_products.count()} products:")
                for lp in linked_products:
                    print(f"     * {lp.product.title_tr} (Is Primary: {lp.is_primary})")
            else:
                print("  -> ORPHAN (Not linked to any product)")
    else:
        print("No media files found containing '391155' in filename.")

if __name__ == "__main__":
    debug_product_391155()
