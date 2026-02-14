
import os
import sys
import django
from django.db.models import Q

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Product, Variant, Media, ProductMedia

def scan_orphans(dry_run=True):
    print(f"--- Scanning for Orphan Images (Dry Run: {dry_run}) ---")
    
    # 1. Get products without images
    img_less_products = Product.objects.filter(product_media__isnull=True)
    print(f"Products missing images: {img_less_products.count()}")
    
    matches_found = 0
    
    for product in img_less_products:
        # Get all model codes for this product's variants
        # Filter out empty or None codes
        codes = [
            v.model_code.strip() 
            for v in product.variants.all() 
            if v.model_code and v.model_code.strip()
        ]
        
        if not codes:
            continue
            
        # Search for orphan media matching these codes
        # We look for unlinked media OR media validly seemingly belonging to this code
        # Ideally only "orphans" (no relations) to avoid stealing, but maybe user wants shared?
        # Let's stick to orphans (no product_media links)
        
        for code in codes:
            # Look for filename containing the code
            # We want to be careful not to match "10" in "100"
            # safe assumption: code is usually distinct or followed by _ / -
            
            # Simple contains first
            candidates = Media.objects.filter(
                filename__icontains=code
            ).filter(
                media_products__isnull=True # Must be orphan
            )
            
            for media in candidates:
                # Double check reasonable match (e.g. filename starts with code or is surrounded by delimiters)
                # But for now, listing is enough
                print(f"[MATCH] Product: {product.title_tr[:30]}... | Code: {code} | Media: {media.filename}")
                matches_found += 1
                
                if not dry_run:
                    # Link it
                    ProductMedia.objects.create(
                        product=product,
                        media=media,
                        variant=product.variants.filter(model_code=code).first(), # Link to specific variant if possible
                        is_primary=(product.product_media.count() == 0), # Primary if it's the first one
                        sort_order=0
                    )
                    print("   -> LINKED!")

    print(f"\nTotal Matches Found: {matches_found}")

if __name__ == "__main__":
    # CHANGE THIS TO FALSE TO APPLY FIXES
    DRY_RUN = True 
    scan_orphans(dry_run=DRY_RUN)
