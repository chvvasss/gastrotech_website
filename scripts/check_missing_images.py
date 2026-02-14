#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Add backend to path for Django access
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django
from django.utils import timezone
django.setup()

from apps.catalog.models import Product

def main():
    print("Checking for products without images...")
    
    # Check Active products
    missing_active = Product.objects.filter(
        product_media__isnull=True,
        status='active'
    ).select_related('brand').order_by('name') # A-Z
    
    count = missing_active.count()
    
    print(f"Total Active Products without images: {count}")
    
    output_path = SCRIPT_DIR / "missing_images_report.txt"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"MISSING IMAGES REPORT (Date: {timezone.now()})\n")
        f.write(f"Total Active Products Without Images: {count}\n")
        f.write("="*80 + "\n")
        f.write(f"{'PRODUCT NAME':<50} | {'BRAND':<20} | {'SLUG'}\n")
        f.write("-" * 80 + "\n")
        
        for p in missing_active:
            brand_name = p.brand.name if p.brand else "-"
            # Handle potential None name
            name = p.name or "No Name"
            line = f"{name[:48]:<50} | {brand_name[:18]:<20} | {p.slug}"
            f.write(line + "\n")
    
    print(f"List saved to: {output_path}")
    print("Top 10 missing:")
    for p in missing_active[:10]:
        brand_name = p.brand.name if p.brand else "-"
        print(f" - {p.name} ({brand_name})")

if __name__ == "__main__":
    main()
