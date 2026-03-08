"""Check product data structure integrity."""
import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Category, Series, Product, Variant, TaxonomyNode

print("=== CATEGORY > SERIES > PRODUCT HIERARCHY ===")
for cat in Category.objects.all().order_by("order"):
    series_qs = Series.objects.filter(category=cat).order_by("order")
    prod_count = Product.objects.filter(category=cat).count()
    print(f"\n[{cat.slug}] {cat.name} - {series_qs.count()} series, {prod_count} products")
    for s in series_qs:
        prods = Product.objects.filter(series=s)
        print(f"  Series: {s.slug} ({s.name}) -> {prods.count()} products")
        for p in prods[:3]:
            vcount = Variant.objects.filter(product=p).count()
            print(f"    - {p.slug} ({p.name}) [{vcount} variants]")
        if prods.count() > 3:
            print(f"    ... +{prods.count()-3} more")

print("\n=== ORPHAN CHECK ===")
no_series = Product.objects.filter(series__isnull=True).count()
no_cat = Product.objects.filter(category__isnull=True).count()
no_brand = Product.objects.filter(brand__isnull=True).count()
print(f"Products without series: {no_series}")
print(f"Products without category: {no_cat}")
print(f"Products without brand: {no_brand}")

# Products with 0 variants
zero_var = []
for p in Product.objects.all():
    if Variant.objects.filter(product=p).count() == 0:
        zero_var.append(p.slug)
print(f"Products with 0 variants: {len(zero_var)}")
if zero_var:
    for s in zero_var[:10]:
        print(f"  - {s}")

print("\n=== SERIES-CATEGORY MISMATCH ===")
mismatches = 0
for p in Product.objects.select_related("series", "category", "series__category").all():
    if p.series and p.series.category_id != p.category_id:
        print(f"  MISMATCH: {p.slug} -> product.cat={p.category.slug}, series.cat={p.series.category.slug}")
        mismatches += 1
print(f"Total mismatches: {mismatches}")

print("\n=== SAMPLE PRODUCTS WITH DETAILS ===")
for p in Product.objects.select_related("series", "category", "brand").all()[:10]:
    variants = Variant.objects.filter(product=p)
    print(f"\n  Product: {p.slug}")
    print(f"  Name: {p.name}")
    print(f"  Category: {p.category.slug if p.category else 'NONE'}")
    print(f"  Series: {p.series.slug if p.series else 'NONE'}")
    print(f"  Brand: {p.brand.slug if p.brand else 'NONE'}")
    print(f"  Status: {p.status}")
    print(f"  Variants: {variants.count()}")
    print(f"  General Features: {len(p.general_features)} items")
    print(f"  Short Specs: {len(p.short_specs)} items")
    print(f"  Spec Layout: {p.spec_layout}")
    for v in variants[:2]:
        print(f"    Variant: {v.model_code} - price={v.list_price}, weight={v.weight_kg}, dims={v.dimensions}")
        spec_count = len(v.specs) if v.specs else 0
        print(f"      Specs: {spec_count} keys")

print("\n=== SERIES SIZE DISTRIBUTION ===")
big_series = []
single_series = []
for s in Series.objects.all():
    cnt = Product.objects.filter(series=s).count()
    if cnt > 20:
        big_series.append((s.slug, cnt))
    if cnt == 1:
        single_series.append(s.slug)

print(f"Series with >20 products (should these be split?):")
for slug, cnt in sorted(big_series, key=lambda x: -x[1]):
    print(f"  {slug}: {cnt} products")

print(f"\nSingleton series (1 product): {len(single_series)}")
for slug in single_series[:10]:
    print(f"  {slug}")
if len(single_series) > 10:
    print(f"  ... +{len(single_series)-10} more")
