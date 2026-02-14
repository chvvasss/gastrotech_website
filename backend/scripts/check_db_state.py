
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import models
from apps.catalog.models import Category, Product, Series

print("=" * 80)
print("DATABASE STATE CHECK")
print("=" * 80)

# Check firinlar category
try:
    firinlar_cat = Category.objects.get(slug='firinlar')
    print(f"\n[OK] Firinlar category exists: {firinlar_cat.name} (ID: {firinlar_cat.id})")
except Category.DoesNotExist:
    print("\n[ERROR] Firinlar category NOT FOUND!")

# Check products
firinlar_products = Product.objects.filter(category__slug='firinlar', status='active')
print(f"\nProducts in 'firinlar' category: {firinlar_products.count()}")

if firinlar_products.exists():
    print("\nSample products:")
    for p in firinlar_products[:5]:
        series_name = p.series.name if p.series else "NO SERIES"
        series_cat = p.series.category.slug if (p.series and p.series.category) else "NO CAT"
        print(f"  - {p.slug}")
        print(f"    Product.category: {p.category.slug if p.category else 'NULL'}")
        print(f"    Product.series: {series_name}")
        print(f"    Series.category: {series_cat}")

# Check series
firinlar_series = Series.objects.filter(category__slug='firinlar')
print(f"\nSeries in 'firinlar' category: {firinlar_series.count()}")

# Check which JSON products are in DB
import json
json_file = r"C:\gastrotech.com.tr.0101\gastrotech.com_cursor\ceysonlar\catalog_bundle_final_v1.json"
with open(json_file, 'r', encoding='utf-8') as f:
    products_json = json.load(f)

json_firinlar = [p for p in products_json if p.get('category') == 'firinlar']
print(f"\nJSON products with category='firinlar': {len(json_firinlar)}")

print("\nChecking which JSON products exist in DB:")
for p_json in json_firinlar:
    slug = p_json['slug']
    try:
        db_product = Product.objects.select_related('category', 'series', 'series__category').get(slug=slug)
        db_cat = db_product.category.slug if db_product.category else 'NULL'
        series_cat = db_product.series.category.slug if (db_product.series and db_product.series.category) else 'NULL'
        status = "OK" if db_cat == 'firinlar' else f"WRONG (product.cat={db_cat}, series.cat={series_cat})"
        print(f"  [{status}] {slug}")
    except Product.DoesNotExist:
        print(f"  [NOT FOUND] {slug}")

print("\n" + "=" * 80)
