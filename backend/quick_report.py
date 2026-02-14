"""Quick Database State Report"""
from apps.catalog.models import Category, Series, Brand, CategoryLogoGroup, LogoGroupSeries

print("=== DATABASE STATE ===\n")

# Counts
cats = Category.objects.count()
series = Series.objects.count()
brands = Brand.objects.count()
lgs = CategoryLogoGroup.objects.count()
lgss = LogoGroupSeries.objects.count()

print(f"Categories: {cats}")
print(f"Series: {series}")
print(f"Brands: {brands}")
print(f"CategoryLogoGroups: {lgs}")
print(f"LogoGroupSeries: {lgss}\n")

# Root categories
print("=== ROOT CATEGORIES ===")
for cat in Category.objects.filter(parent__isnull=True).order_by('order'):
    children_count = cat.children.count()
    print(f"  [{cat.order}] {cat.name} ({children_count} children)")
    for child in cat.children.all().order_by('order'):
        lg_count = child.logo_groups.count()
        marker = f" [{lg_count} logo groups]" if lg_count > 0 else ""
        print(f"      [{child.order}] {child.name}{marker}")

# Logo Grid categories
print("\n=== LOGO GRID CATEGORIES ===")
cats_with_lg = Category.objects.filter(logo_groups__isnull=False).distinct()
for cat in cats_with_lg:
    print(f"\n{cat.name}:")
    for lg in cat.logo_groups.all():
        series_count = lg.series_set.count()
        print(f"  - {lg.brand.name}: {series_count} series")
