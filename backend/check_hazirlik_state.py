"""Check current state of Hazirlik Ekipmanlari categories and series."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gastrotech.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.catalog.models import Category, Series, Product, Brand, BrandCategory

# Get parent category
cat = Category.objects.get(slug='hazirlik-ekipmanlari')
print("=" * 60)
print(f"ANA KATEGORI: {cat.name}")
print("=" * 60)

# Get subcategories
subcats = cat.children.all().order_by('order')
print(f"\nAlt Kategori Sayisi: {subcats.count()}")

for c in subcats:
    series_list = c.series_set.all()
    print(f"\n  [{c.name}] ({c.slug})")
    print(f"    Seri Sayisi: {series_list.count()}")
    
    for s in series_list:
        prod_count = s.product_set.count()
        print(f"      - {s.name}: {prod_count} urun")

# Check brand associations
print("\n" + "=" * 60)
print("MARKA BAGLANTILARI")
print("=" * 60)

for c in subcats:
    brand_cats = BrandCategory.objects.filter(category=c)
    if brand_cats.exists():
        print(f"\n  [{c.name}] Markalar:")
        for bc in brand_cats:
            print(f"    - {bc.brand.name}")
    else:
        print(f"\n  [{c.name}] MARKA YOK!")

# Check parent category series
parent_series = Series.objects.filter(category=cat)
print("\n" + "=" * 60)
print(f"ANA KATEGORIDE KALAN SERILER: {parent_series.count()}")
print("=" * 60)
if parent_series.count() > 0:
    for s in parent_series[:10]:
        print(f"  - {s.name}")
    if parent_series.count() > 10:
        print(f"  ... ve {parent_series.count() - 10} tane daha")
