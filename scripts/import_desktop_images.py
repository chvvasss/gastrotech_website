#!/usr/bin/env python
"""
Import Desktop Images

Usage:
    python scripts/import_desktop_images.py
"""
import os
import sys
from pathlib import Path

# Setup Django Environment
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from apps.catalog.models import Product, Media, ProductMedia

# Configuration
SOURCE_DIR = Path(r"C:\Users\emir\Desktop\product_images_valid")

def get_product(filename):
    """
    Find product by matching filename (without extension) to slug.
    Filename: "kitchenaid-5k45sseob-classic-stand-mikser.jpg"
    Slug: "kitchenaid-5k45sseob-classic-stand-mikser"
    """
    name_stem = Path(filename).stem
    
    # Context: User provided filenames might be slightly different or need normalization
    
    # Custom Mappings for known mismatches
    CUSTOM_MAPPINGS = {
        # 6.6L -> 5KSM70 Series
        "kitchenaid-6.6l-empire-red": "kitchenaid-5ksm70jpxeeer-heavy-duty-stand-mikser",
        "kitchenaid-6.6l-onyx-black": "kitchenaid-5ksm70jpxeob-heavy-duty-stand-mikser",
        "kitchenaid-6.6l-white": "kitchenaid-5ksm70jpxewh-heavy-duty-stand-mikser",
        
        # 6.9L -> 5KSM7990 Series
        "kitchenaid-6.9l-empire-red": "kitchenaid-5ksm7990xeer-professional-stand-mikser",
        "kitchenaid-5ksm7990xbwh-white": "kitchenaid-5ksm7990xewh-professional-stand-mikser", # xbwh -> xewh typo?

        # 5K55 -> 5KMS55 (Heavy Duty)
        "kitchenaid-heavy-duty-5k55sxxebm": "kitchenaid-5kms55sxebm-heavy-duty-stand-mikser",
        "kitchenaid-heavy-duty-contour-silver-5k55sxxecu": "kitchenaid-5kms55sxecu-heavy-duty-stand-mikser",
        "kitchenaid-heavy-duty-empire-red": "kitchenaid-5kms55sxeeer-heavy-duty-stand-mikser",
        "kitchenaid-heavy-duty-onyx-black": "kitchenaid-5kms55sxeob-heavy-duty-stand-mikser",
        "kitchenaid-heavy-duty-white": "kitchenaid-heavy-duty-5kpm5ewh", # Fallback or different model?
    }

    normalized_name = name_stem.lower().replace(".", "-") # kitchenaid-6.6l-white
    
    # Strategy 0: Custom Mapping
    if normalized_name in CUSTOM_MAPPINGS:
        slug = CUSTOM_MAPPINGS[normalized_name]
        return Product.objects.filter(slug=slug).first()

    # Strategy 0.5: Check for exact filename match in mappings keys (in case replace didn't match)
    if name_stem.lower() in CUSTOM_MAPPINGS:
         slug = CUSTOM_MAPPINGS[name_stem.lower()]
         return Product.objects.filter(slug=slug).first()

    # Strategy 1: Exact match on slug
    product = Product.objects.filter(slug=name_stem).first()
    if product:
        return product
        
    # Strategy 2: Try replacing dots with dashes (e.g. 6.6L -> 6-6l) because slugs usually don't have dots
    slug_variant = name_stem.replace(".", "-").lower()
    product = Product.objects.filter(slug=slug_variant).first()
    if product:
        return product

    # Strategy 3: Try to find by code if the filename STARTS with the code
    # Many files start with "kitchenaid-" which is brand, maybe the next part is code?
    # e.g. "kitchenaid-5k45sseob-classic..." -> Code might be "5K45SSEOB"
    parts = name_stem.split("-")
    if len(parts) > 1:
        possible_codes = [parts[0], parts[1]] # check first few parts
        for code in possible_codes:
            if len(code) > 3: # Ignore short parts
                # Try finding a variant with this model code
                from apps.catalog.models import Variant
                variant = Variant.objects.filter(model_code__iexact=code).first()
                if variant:
                    return variant.product
                    
    return None

def import_image(filepath):
    """
    1. Find product.
    2. Delete existing images.
    3. Upload new image.
    """
    filename = filepath.name
    product = get_product(filename)
    
    if not product:
        print(f"[SKIP] Product not found for: {filename}")
        return False

    print(f"[MATCH] Found product: {product.title_tr} ({product.slug})")
    
    # 2. Delete existing images
    existing_count = ProductMedia.objects.filter(product=product).count()
    if existing_count > 0:
        print(f"  - Deleting {existing_count} existing images...")
        ProductMedia.objects.filter(product=product).delete()
    
    # 3. Upload new image
    try:
        with open(filepath, "rb") as f:
            image_data = f.read()
            
        media = Media.objects.create(
            kind=Media.Kind.IMAGE,
            filename=filename,
            content_type="image/jpeg", # Assuming jpg from list
            bytes=image_data # Correct field name is 'bytes', not 'data'
        )
        
        ProductMedia.objects.create(
            product=product,
            media=media,
            is_primary=True,
            sort_order=0
        )
        print(f"  + Uploaded new image: {filename}")
        return True
        
    except Exception as e:
        print(f"  [ERROR] Failed to upload {filename}: {e}")
        return False

def main():
    print(f"Scanning directory: {SOURCE_DIR}")
    if not SOURCE_DIR.exists():
        print(f"Directory not found: {SOURCE_DIR}")
        return
        
    files = list(SOURCE_DIR.glob("*.*"))
    print(f"Found {len(files)} files.")
    
    success_count = 0
    
    for filepath in files:
        if filepath.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.webp']:
            continue
            
        if import_image(filepath):
            success_count += 1
            
    print("-" * 30)
    print(f"Completed. {success_count}/{len(files)} images imported.")

if __name__ == "__main__":
    main()
