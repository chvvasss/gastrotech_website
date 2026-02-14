"""
Comprehensive Catalog Audit Script
-----------------------------------
Analyzes all categories, brands, series, logo groups, and their relationships.
Identifies duplicates, orphans, and structural issues.
"""
from apps.catalog.models import Category, Series, Brand, CategoryLogoGroup, LogoGroupSeries
from django.db.models import Count

def audit():
    print("=" * 60)
    print("COMPREHENSIVE CATALOG AUDIT")
    print("=" * 60)
    
    # 1. Categories
    print("\n1. CATEGORIES")
    print("-" * 40)
    all_cats = Category.objects.all().order_by('order')
    root_cats = all_cats.filter(parent__isnull=True)
    print(f"Total: {all_cats.count()}")
    print(f"Root-level: {root_cats.count()}")
    
    print("\nCategory Tree:")
    for cat in root_cats:
        children = cat.children.all().order_by('order')
        print(f"  [{cat.order}] {cat.name} ({cat.slug})")
        for child in children:
            logo_count = child.logo_groups.count()
            print(f"      [{child.order}] {child.name} ({child.slug}) - LogoGroups: {logo_count}")
    
    # 2. Brands
    print("\n2. BRANDS")
    print("-" * 40)
    all_brands = Brand.objects.all().order_by('order')
    print(f"Total: {all_brands.count()}")
    for b in all_brands:
        lg_count = b.category_logo_groups.count()
        print(f"  [{b.order}] {b.name} ({b.slug}) - Active: {b.is_active}, LogoGroups: {lg_count}")
    
    # 3. CategoryLogoGroups
    print("\n3. CATEGORY LOGO GROUPS")
    print("-" * 40)
    all_lgs = CategoryLogoGroup.objects.all().select_related('category', 'brand')
    print(f"Total: {all_lgs.count()}")
    for lg in all_lgs:
        series_count = lg.series_set.count()
        print(f"  {lg.category.name} -> {lg.brand.name}: {series_count} series")
        for lgs in lg.series_set.all().order_by('order'):
            print(f"      * {lgs.series.name} (Heading: {lgs.is_heading})")
    
    # 4. Series without LogoGroup
    print("\n4. ORPHAN SERIES (no logo group)")
    print("-" * 40)
    orphan_series = Series.objects.annotate(lg_count=Count('logo_groups')).filter(lg_count=0)
    print(f"Total orphan series: {orphan_series.count()}")
    if orphan_series.count() > 0:
        for s in orphan_series[:20]:
            print(f"  - {s.name} ({s.slug}) in Category: {s.category.name if s.category else 'None'}")
        if orphan_series.count() > 20:
            print(f"  ... and {orphan_series.count() - 20} more")
    
    # 5. Duplicate slugs
    print("\n5. DUPLICATE SLUGS")
    print("-" * 40)
    dup_cat_slugs = Category.objects.values('slug').annotate(count=Count('id')).filter(count__gt=1)
    dup_series_slugs = Series.objects.values('slug').annotate(count=Count('id')).filter(count__gt=1)
    dup_brand_slugs = Brand.objects.values('slug').annotate(count=Count('id')).filter(count__gt=1)
    
    print(f"Duplicate Category slugs: {dup_cat_slugs.count()}")
    for d in dup_cat_slugs:
        print(f"  - {d['slug']} (x{d['count']})")
    
    print(f"Duplicate Series slugs: {dup_series_slugs.count()}")
    for d in dup_series_slugs:
        print(f"  - {d['slug']} (x{d['count']})")
    
    print(f"Duplicate Brand slugs: {dup_brand_slugs.count()}")
    for d in dup_brand_slugs:
        print(f"  - {d['slug']} (x{d['count']})")
        
    # 6. Key categories check
    print("\n6. KEY CATEGORIES CHECK")
    print("-" * 40)
    key_slugs = [
        'sogutma-uniteleri', 'buz-makineleri', 'sogutma-ekipmanlari',
        'pisirme-ekipmanlari', 'firinlar', 'pizza-firinlari',
        'hazirlik-ekipmanlari'
    ]
    for slug in key_slugs:
        cat = Category.objects.filter(slug=slug).first()
        if cat:
            parent_name = cat.parent.name if cat.parent else "ROOT"
            print(f"  ✓ {slug} -> Parent: {parent_name}")
        else:
            print(f"  ✗ {slug} -> NOT FOUND")
    
    print("\n" + "=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)

audit()
