"""
Final verification: list all categories with their series, product, and catalog counts.
Also check for any duplicate categories.
"""
import django, os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Suppress debug logging
import logging
logging.disable(logging.DEBUG)

django.setup()

from apps.catalog.models import Category, CategoryCatalog, Series, Product

print("=" * 80)
print("FINAL CATEGORY VERIFICATION")
print("=" * 80)

cats = Category.objects.all().order_by('slug')
print(f"\nTotal categories: {cats.count()}\n")
print(f"{'Slug':<35} {'Name':<30} {'Series':>6} {'Prod':>6} {'Cat':>4}")
print("-" * 85)

for c in cats:
    s = Series.objects.filter(category=c).count()
    p = Product.objects.filter(category=c).count()
    cc = CategoryCatalog.objects.filter(category=c).count()
    print(f"{c.slug:<35} {str(c.name):<30} {s:>6} {p:>6} {cc:>4}")

# Check for duplicate-looking slugs
print("\n" + "=" * 80)
print("DUPLICATE CHECK")
print("=" * 80)

slugs = list(cats.values_list('slug', flat=True))
known_pairs = [
    ('camasirhane', 'camasirhane-ekipmanlari'),
    ('hazirlik', 'hazirlik-ekipmanlari'),
    ('kafeterya', 'kafeterya-ekipmanlari'),
    ('pisirme', 'pisirme-uniteleri'),
    ('sogutma', 'sogutma-uniteleri'),
    ('tamamlayici', 'tamamlayici-ekipmanlar'),
]

found_dupes = False
for short, long in known_pairs:
    if short in slugs and long in slugs:
        print(f"[DUPLICATE FOUND] Both '{short}' and '{long}' exist!")
        found_dupes = True

if not found_dupes:
    print("[OK] No duplicate category pairs found.")

# Check for duplicate catalogs
print("\n" + "=" * 80)
print("DUPLICATE CATALOG CHECK")
print("=" * 80)

from django.db.models import Count
dupes = (CategoryCatalog.objects
    .values('category_id', 'title_tr')
    .annotate(cnt=Count('id'))
    .filter(cnt__gt=1))

if dupes.count() == 0:
    print("[OK] No duplicate catalog entries found.")
else:
    for d in dupes:
        cat = Category.objects.get(id=d['category_id'])
        print(f"[DUPE] {cat.slug}: '{d['title_tr']}' appears {d['cnt']} times")

print("\n" + "=" * 80)
print("ALL CATALOGS BY CATEGORY")
print("=" * 80)

for c in cats:
    catalogs = CategoryCatalog.objects.filter(category=c)
    if catalogs.exists():
        print(f"\n[{c.slug}] ({catalogs.count()} catalogs)")
        for cc in catalogs:
            print(f"  - {cc.title_tr}")
