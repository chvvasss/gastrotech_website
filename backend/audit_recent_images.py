
import os
import django
import sys

# Setup Django environment
sys.path.append('/app')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import ProductMedia, Product, Media

def audit_recent_links():
    # Get the most recent 600 product-media links (covering the last import)
    recent_links = ProductMedia.objects.select_related('product', 'media').order_by('-media__created_at')[:600]

    print(f"{'Product Name':<40} | {'Variants':<30} | {'Image Filename':<40} | {'Status'}")
    print("-" * 120)

    mismatch_count = 0
    total_checked = 0

    for pm in recent_links:
        product = pm.product
        media = pm.media
        filename = media.filename.lower().split('.')[0]
        
        # Get all variant model codes for this product
        variants = product.variants.all()
        model_codes = [v.model_code.lower() for v in variants if v.model_code]
        
        # Check if any model code matches the filename
        # We look for model code in filename OR filename in model code (fuzzy)
        is_match = False
        matched_code = ""
        
        for code in model_codes:
            # Clean code and filename for better matching (remove non-alphanumeric)
            code_clean = "".join(c for c in code if c.isalnum())
            filename_clean = "".join(c for c in filename if c.isalnum())
            
            if code_clean in filename_clean or filename_clean in code_clean:
                is_match = True
                matched_code = code
                break
        
        total_checked += 1
        
        if not is_match:
            mismatch_count += 1
            variants_str = ", ".join(model_codes[:3])
            print(f"{product.name[:38]:<40} | {variants_str[:30]:<30} | {media.filename[:38]:<40} | MISMATCH")

    print("-" * 120)
    print(f"Total Checked: {total_checked}")
    print(f"Total Mismatches Found: {mismatch_count}")

if __name__ == "__main__":
    audit_recent_links()
