"""
Audit all products and list those without any images.
"""

import os
import sys
import django
from collections import defaultdict

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.catalog.models import Product

def audit_images():
    print("\n" + "="*80)
    print("PRODUCT IMAGE AUDIT")
    print("="*80 + "\n")
    
    # Get all products with prefetch
    products = Product.objects.all().select_related(
        'series', 'series__category', 'brand'
    ).prefetch_related('product_media')
    
    total_products = products.count()
    products_without_images = []
    
    for product in products:
        media_count = product.product_media.count()
        if media_count == 0:
            products_without_images.append(product)

    missing_count = len(products_without_images)
    
    print(f"Total Products: {total_products}")
    print(f"Products with Images: {total_products - missing_count}")
    print(f"Products WITHOUT Images: {missing_count}")
    print(f"Coverage: {((total_products - missing_count) / total_products * 100):.1f}%\n")
    
    if missing_count == 0:
        print("Great! All products have images.")
        return

    print("="*80)
    print("LIST OF PRODUCTS WITHOUT IMAGES")
    print("="*80 + "\n")

    # Group by Category > Series
    grouped = defaultdict(lambda: defaultdict(list))
    
    for p in products_without_images:
        cat_name = p.series.category.name if p.series and p.series.category else "Uncategorized"
        series_name = p.series.name if p.series else "No Series"
        grouped[cat_name][series_name].append(p)
    
    for cat_name, series_dict in sorted(grouped.items()):
        print(f"[CATEGORY]: {cat_name.upper()}")
        print("-" * 60)
        
        for series_name, prods in sorted(series_dict.items()):
            print(f"  [SERIES]: {series_name}")
            for p in prods:
                brand_name = p.brand.name if p.brand else "No Brand"
                status = "Active" if p.status == 'active' else "Passive"
                print(f"    - [{p.slug}] {p.title_tr or p.name} ({brand_name}) - {status}")
            print()
        print("\n")

if __name__ == '__main__':
    audit_images()
