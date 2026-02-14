"""
Merge duplicate series and migrate Pişirme Üniteleri to Pişirme Ekipmanları
"""
from apps.catalog.models import Category, Series, Product

# Get both categories
pu = Category.objects.get(slug='pisirme-uniteleri')
pe = Category.objects.get(slug='pisirme-ekipmanlari')

print(f"Migrating: {pu.name} → {pe.name}\n")

# Get series from both categories
pu_series = Series.objects.filter(category=pu)
pe_series_slugs = set(Series.objects.filter(category=pe).values_list('slug', flat=True))

for series in pu_series:
    if series.slug in pe_series_slugs:
        # Duplicate exists in target category
        target_series = Series.objects.get(category=pe, slug=series.slug)
        print(f"DUPLICATE: {series.slug}")
        print(f"  - Moving products from PU series to PE series")
        
        # Move all products from this series to the target series
        products = Product.objects.filter(series=series)
        count = products.update(series=target_series, category=pe)
        print(f"  - Moved {count} products")
        
        # Delete the duplicate series
        series.delete()
        print(f"  - Deleted duplicate series\n")
    else:
        # No duplicate, just move the series
        print(f"MOVING: {series.slug}")
        series.category = pe
        series.save()
        
        # Also move products
        products = Product.objects.filter(series=series)
        count = products.update(category=pe)
        print(f"  - Moved series and {count} products\n")

# Move any remaining products not in a series
remaining_products = Product.objects.filter(category=pu)
count = remaining_products.update(category=pe)
if count > 0:
    print(f"Moved {count} orphan products (no series)\n")

# Delete the empty category
print(f"Deleting category: {pu.name}")
pu.delete()

print("\n✅ SUCCESS! All content merged into:", pe.name)
