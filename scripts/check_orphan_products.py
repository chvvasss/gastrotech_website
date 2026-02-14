"""
Check for orphaned products in tamamlayici-ekipmanlar category.
"""

import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.catalog.models import Category, Product, Series


def check_orphans():
    """Check for products still under old category."""
    
    print("\n" + "="*60)
    print("CHECKING TAMAMLAYICI EKIPMANLAR")
    print("="*60 + "\n")
    
    # Get categories
    tamamlayici = Category.objects.get(slug='tamamlayici-ekipmanlar')
    teshir = Category.objects.get(slug='teshir-uniteleri')
    setustu = Category.objects.get(slug='setustu-teshir-uniteleri')
    
    print(f"Tamamlayici: {tamamlayici.name}")
    subs = Category.objects.filter(parent=tamamlayici)
    print(f"  Subcategories: {[c.slug for c in subs]}\n")
    
    print(f"Teshir: {teshir.name} (parent: {teshir.parent.slug})")
    print(f"Setustu: {setustu.name} (parent: {setustu.parent.slug})\n")
    
    # Check series in old location
    print("="*60)
    print("SERIES IN OLD LOCATION (teshir-uniteleri)")
    print("="*60)
    series_in_teshir = Series.objects.filter(category=teshir)
    print(f"Series count: {series_in_teshir.count()}\n")
    
    for s in series_in_teshir:
        prods = Product.objects.filter(series=s)
        print(f"Series: {s.slug} ({s.name})")
        print(f"  Category: {s.category.slug}")
        print(f"  Products: {prods.count()}")
        for p in prods[:5]:
            print(f"    - {p.slug}")
        print()


if __name__ == '__main__':
    check_orphans()
