"""
Move orphaned series from teshir-uniteleri to setustu-teshir-uniteleri.
Also check brand logos.
"""

import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.catalog.models import Category, Series, Brand


def fix_orphaned_series():
    """Move series to correct category."""
    
    print("\n" + "="*60)
    print("FIXING ORPHANED SERIES")
    print("="*60 + "\n")
    
    # Get categories
    old_cat = Category.objects.get(slug='teshir-uniteleri')
    new_cat = Category.objects.get(slug='setustu-teshir-uniteleri')
    
    print(f"Old category: {old_cat.name} (parent: {old_cat.parent.slug})")
    print(f"New category: {new_cat.name} (parent: {new_cat.parent.slug})\n")
    
    # Get series to move
    series_to_move = Series.objects.filter(category=old_cat)
    print(f"Found {series_to_move.count()} series to move:\n")
    
    for series in series_to_move:
        prod_count = series.products.count()
        print(f"  [{series.slug}] {series.name}")
        print(f"    Products: {prod_count}")
        print(f"    Moving from: {series.category.slug}")
        print(f"    Moving to: {new_cat.slug}")
        
        # Move the series
        series.category = new_cat
        series.save()
        print(f"    [OK] Moved!\n")
    
    print("="*60)
    print("CHECKING BRAND LOGOS")
    print("="*60 + "\n")
    
    brands = Brand.objects.all()
    print(f"Total brands: {brands.count()}\n")
    
    no_logo_count = 0
    for brand in brands:
        if not brand.logo_media:
            no_logo_count += 1
            print(f"  [!] {brand.name} ({brand.slug}): NO LOGO")
        else:
            print(f"  [OK] {brand.name}: has logo (ID: {str(brand.logo_media.id)[:8]}...)")
    
    print(f"\nBrands without logos: {no_logo_count}/{brands.count()}")
    
    print("\n[OK] Done!\n")


if __name__ == '__main__':
    fix_orphaned_series()
