"""Auto Cleanup Script"""
from apps.catalog.models import Category, Series, Brand, CategoryLogoGroup, LogoGroupSeries

print("=" * 60)
print("AUTO CLEANUP")
print("=" * 60)

# 1. Orphaned LogoGroupSeries
print("\n1. Orphaned LogoGroupSeries...")
count = 0
for lgs in LogoGroupSeries.objects.all():
    if not Series.objects.filter(id=lgs.series_id).exists():
        lgs.delete()
        count += 1
print(f"  Deleted: {count}")

# 2. Empty CategoryLogoGroups
print("\n2. Empty CategoryLogoGroups...")
count = 0
for lg in CategoryLogoGroup.objects.all():
    if lg.series_set.count() == 0:
        lg.delete()
        count += 1
print(f"  Deleted: {count}")

# 3. Orphaned Brands
print("\n3. Brands (report only)...")
for brand in Brand.objects.all():
    lg_count = brand.category_logo_groups.count()
    prod_count = brand.products.count()
    print(f"  {brand.name}: LogoGroups={lg_count}, Products={prod_count}")

# 4. Series without category
print("\n4. Series without category...")
no_cat = Series.objects.filter(category__isnull=True).count()
print(f"  Count: {no_cat}")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
