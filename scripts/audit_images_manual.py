
import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import Variant, ProductMedia

IMAGE_DIR = r"C:\gastrotech.com.tr.0101\gastrotech.com_cursor\fotolar1"

def get_model_code(filename):
    stem = Path(filename).stem
    base = stem.split('_')[0]
    if '(' in base:
         base = base.split('(')[0]
    return base.strip()

def audit():
    print("Starting Manual Audit...")
    
    files_scanned = 0
    files_no_variant = []
    products_with_matching_files_but_no_link = []
    
    # 1. Check Files -> DB
    for root, dirs, files in os.walk(IMAGE_DIR):
        for file in files:
            if not file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                continue
            
            files_scanned += 1
            code = get_model_code(file)
            
            # Check if variant exists
            variant = Variant.objects.filter(model_code__iexact=code).first()
            if not variant:
                files_no_variant.append(f"{file} -> Extracted Code: '{code}' (No Variant found)")
                continue
                
            # Check if linked
            # We look for ANY media linked to this product that matches this filename roughly?
            # Or just check if the product has images at all?
            has_media = ProductMedia.objects.filter(product=variant.product).exists()
            if not has_media:
                products_with_matching_files_but_no_link.append(f"{file} -> Variant {variant.model_code} -> Product {variant.product.id} (Has NO images linked)")

    print(f"Scanned {files_scanned} files.")
    
    print("\n--- Files with NO Matching Variant (Potential Renaming Needed) ---")
    if files_no_variant:
        for f in files_no_variant[:50]: # Limit output
            print(f)
        if len(files_no_variant) > 50:
            print(f"... and {len(files_no_variant) - 50} more.")
    else:
        print("NONE. All files matched a Variant.")

    print("\n--- Products with Matching Files but NO Links (Import Failure?) ---")
    if products_with_matching_files_but_no_link:
        for p in products_with_matching_files_but_no_link:
            print(p)
    else:
        print("NONE. All matched products have at least one image.")

if __name__ == "__main__":
    audit()
