"""
Cleanup Orphaned Data Script
-----------------------------
Identifies and removes orphaned series, logo groups, and brands
left over from deleted categories.
"""
from apps.catalog.models import Category, Series, Brand, CategoryLogoGroup, LogoGroupSeries
from django.db import transaction

def cleanup():
    print("=" * 60)
    print("ORPHAN CLEANUP")
    print("=" * 60)
    
    # 1. Find orphaned LogoGroupSeries (series no longer exists)
    print("\n1. Checking LogoGroupSeries...")
    orphaned_lgs = []
    for lgs in LogoGroupSeries.objects.all():
        if not Series.objects.filter(id=lgs.series_id).exists():
            orphaned_lgs.append(lgs)
            print(f"  ✗ Orphaned LogoGroupSeries: {lgs.id} (series_id={lgs.series_id} not found)")
    
    if orphaned_lgs:
        print(f"\nDeleting {len(orphaned_lgs)} orphaned LogoGroupSeries...")
        for lgs in orphaned_lgs:
            lgs.delete()
        print("  ✓ Deleted")
    else:
        print("  ✓ No orphaned LogoGroupSeries")
    
    # 2. Find empty CategoryLogoGroups (no series)
    print("\n2. Checking CategoryLogoGroups...")
    empty_lgs = []
    for lg in CategoryLogoGroup.objects.all():
        if lg.series_set.count() == 0:
            empty_lgs.append(lg)
            print(f"  ✗ Empty CategoryLogoGroup: {lg.category.name} -> {lg.brand.name}")
    
    if empty_lgs:
        print(f"\nDeleting {len(empty_lgs)} empty CategoryLogoGroups...")
        for lg in empty_lgs:
            lg.delete()
        print("  ✓ Deleted")
    else:
        print("  ✓ No empty CategoryLogoGroups")
    
    # 3. Find unused brands (no logo groups, no products)
    print("\n3. Checking unused brands...")
    unused_brands = []
    for brand in Brand.objects.all():
        has_logo_groups = brand.category_logo_groups.exists()
        has_products = brand.products.exists()
        if not has_logo_groups and not has_products:
            unused_brands.append(brand)
            print(f"  ⚠ Unused brand: {brand.name} ({brand.slug})")
    
   if unused_brands:
        user_confirm = input(f"\nDelete {len(unused_brands)} unused brands? (y/N): ")
        if user_confirm.lower() == 'y':
            for brand in unused_brands:
                brand.delete()
            print("  ✓ Deleted")
        else:
            print("  ℹ Skipped (keeping unused brands)")
    else:
        print("  ✓ No unused brands")
    
    # 4. Find series without category
    print("\n4. Checking series without category...")
    no_cat_series = Series.objects.filter(category__isnull=True)
    if no_cat_series.exists():
        print(f"  ⚠ {no_cat_series.count()} series without category:")
        for s in no_cat_series[:10]:
            print(f"     - {s.name} ({s.slug})")
    else:
        print("  ✓ All series have categories")
    
    print("\n" + "=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)

cleanup()
