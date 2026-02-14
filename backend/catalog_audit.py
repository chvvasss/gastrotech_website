"""
Catalog Topology Audit Script
==============================
Run with: python manage.py runscript catalog_audit
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.catalog.models import Category, Series, Product, Brand, Variant, BrandCategory


def main():
    print("=" * 60)
    print("CATALOG TOPOLOGY REPORT")
    print("=" * 60)
    
    # Count all entities
    print("\n--- ENTITY COUNTS ---")
    print(f"Categories: {Category.objects.count()}")
    print(f"Series: {Series.objects.count()}")
    print(f"Products: {Product.objects.count()}")
    print(f"Brands: {Brand.objects.count()}")
    print(f"Variants: {Variant.objects.count()}")
    print(f"BrandCategory links: {BrandCategory.objects.count()}")
    
    # Category tree
    print("\n--- CATEGORY TREE ---")
    root_cats = Category.objects.filter(parent__isnull=True).order_by('order')
    for cat in root_cats:
        print(f"\n[ROOT] {cat.name} (slug={cat.slug}, order={cat.order})")
        children = Category.objects.filter(parent=cat).order_by('order')
        for child in children:
            print(f"  └── {child.name} (slug={child.slug}, order={child.order})")
            grandchildren = Category.objects.filter(parent=child).order_by('order')
            for grandchild in grandchildren:
                print(f"       └── {grandchild.name} (slug={grandchild.slug})")
    
    # Check for "Hazırlık Ekipmanları"
    print("\n--- HAZIRLIK EKIPMNANLARI CHECK ---")
    hazirlik = Category.objects.filter(slug="hazirlik-ekipmanlari").first()
    if hazirlik:
        print(f"FOUND: {hazirlik.name}")
    else:
        print("NOT FOUND: hazirlik-ekipmanlari")
        similar = Category.objects.filter(name__icontains="hazır")
        if similar.exists():
            print("Similar categories found:")
            for c in similar:
                print(f"  - {c.name} ({c.slug})")
    
    # Brands
    print("\n--- BRANDS ---")
    for brand in Brand.objects.all().order_by('order'):
        cats = list(brand.categories.values_list('name', flat=True))
        print(f"  {brand.name} (slug={brand.slug}, active={brand.is_active}, cats={cats})")
    
    # Series without products
    print("\n--- EMPTY SERIES (0 products) ---")
    empty_series = []
    for series in Series.objects.all():
        if series.products.count() == 0:
            empty_series.append(f"{series.name} in {series.category.name}")
    if empty_series:
        for s in empty_series[:10]:
            print(f"  - {s}")
        if len(empty_series) > 10:
            print(f"  ... and {len(empty_series) - 10} more")
    else:
        print("  None found")
    
    # Duplicate slugs check
    print("\n--- POTENTIAL SLUG CONFLICTS ---")
    from django.db.models import Count
    dup_cat_slugs = (Category.objects
        .values('slug')
        .annotate(count=Count('id'))
        .filter(count__gt=1))
    if dup_cat_slugs:
        for d in dup_cat_slugs:
            print(f"  Category slug '{d['slug']}' appears {d['count']} times")
    else:
        print("  No duplicate category slugs (root level)")
    
    dup_series_slugs = (Series.objects
        .values('category', 'slug')
        .annotate(count=Count('id'))
        .filter(count__gt=1))
    if dup_series_slugs:
        for d in dup_series_slugs:
            print(f"  Series slug conflict in category {d['category']}")
    else:
        print("  No duplicate series slugs per category")
    
    # Products without category
    print("\n--- DATA INTEGRITY CHECK ---")
    products_no_cat = Product.objects.filter(category__isnull=True).count()
    print(f"Products without category: {products_no_cat}")
    
    products_no_series = Product.objects.filter(series__isnull=True).count()
    print(f"Products without series: {products_no_series}")
    
    variants_no_product = Variant.objects.filter(product__isnull=True).count()
    print(f"Orphan variants: {variants_no_product}")
    
    print("\n" + "=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
