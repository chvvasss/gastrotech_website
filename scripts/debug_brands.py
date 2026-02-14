import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.catalog.models import Brand, Product

print("Debugging brand filtering...")
print()

# Check products
products = Product.objects.filter(
    series__category__slug='pizza-firini',
    status='active'
)
print(f"Products in pizza-firini subcategory: {products.count()}")
for p in products:
    print(f"  - {p.title_tr} | Brand: {p.brand} | Series: {p.series.name} | Category: {p.series.category.name}")
print()

# Check brands
brands = Brand.objects.filter(is_active=True)
print(f"Total active brands: {brands.count()}")
for b in brands:
    print(f"  - {b.name} ({b.slug})")
print()

# Try the filter
brands_filtered = Brand.objects.filter(
    is_active=True,
    products__series__category__slug='pizza-firini',
    products__status='active'
).distinct()
print(f"Brands with products in pizza-firini: {brands_filtered.count()}")
for b in brands_filtered:
    print(f"  - {b.name} ({b.slug})")
print()

# Check the SQL query
print("SQL Query:")
print(brands_filtered.query)
