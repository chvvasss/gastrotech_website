
import os
import sys
import django
import difflib

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Product, Media, ProductMedia

def fuzzy_match(dry_run=True):
    print(f"--- Fuzzy Matching Orphan Images (Dry Run: {dry_run}) ---")
    
    # 1. Get products without images
    img_less_products = Product.objects.filter(product_media__isnull=True)
    products_count = img_less_products.count()
    print(f"Products missing images: {products_count}")
    
    # 2. Get all orphan images (ONLY IDs and Filenames to save memory)
    # Using iterator() to avoid loading everything at once if we were iterating, 
    # but here we need a dict so we'll fetch only specific fields.
    orphans_qs = Media.objects.filter(media_products__isnull=True, kind='image').values('id', 'filename')
    
    print("Loading orphan filenames...")
    orphan_filenames = {m['id']: m['filename'] for m in orphans_qs}
    print(f"Orphan filenames loaded: {len(orphan_filenames)}")
    
    matches = []
    
    for product in img_less_products:
        variants = product.variants.all()
        codes = [v.model_code for v in variants if v.model_code]
        if not codes:
            continue
            
        target_code = codes[0]
        
        best_match_id = None
        best_score = 0
        best_filename = ""
        
        for mid, filename in orphan_filenames.items():
            name_part = os.path.splitext(filename)[0]
            first_part = name_part.split('_')[0].split('-')[0]
            
            # Difflib ratio
            ratio = difflib.SequenceMatcher(None, target_code, first_part).ratio()
            
            if ratio > best_score:
                best_score = ratio
                best_match_id = mid
                best_filename = filename
        
        # Threshold > 0.85 to be safe (e.g. 391145 vs 39114 = 0.9)
        # 39136 vs 391136: 
        # "39136" len 5, "391136" len 6. Match is "39136" (5 chars).
        # 2 * 5 / (5 + 6) = 10 / 11 = 0.90
        
        if best_score > 0.85: 
            print(f"[MATCH FOUND] {product.title_tr[:30]}...")
            print(f"   Code: {target_code}")
            print(f"   File: {best_filename}")
            print(f"   Score: {best_score:.2f}")
            
            matches.append((product, best_match_id))
            
            if not dry_run:
                media = Media.objects.get(id=best_match_id)
                ProductMedia.objects.create(
                    product=product,
                    media=media,
                    variant=variants.first(),
                    is_primary=True,
                    sort_order=0
                )
                print("   -> LINKED")
    
    print(f"\nTotal Matches Found: {len(matches)}")

if __name__ == "__main__":
    # Change to False to apply
    fuzzy_match(dry_run=True)
