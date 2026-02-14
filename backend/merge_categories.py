"""
Merge Pişirme Üniteleri into Pişirme Ekipmanları
"""
from apps.catalog.models import Category, Series, Product

# Get both categories
pu = Category.objects.get(slug='pisirme-uniteleri')
pe = Category.objects.get(slug='pisirme-ekipmanlari')

print(f"Pişirme Üniteleri: ID={pu.id}, Parent={pu.parent.name if pu.parent else 'ROOT'}")
print(f"Pişirme Ekipmanları: ID={pe.id}, Parent={pe.parent.name if pe.parent else 'ROOT'}")
print()

# Get all descendants of Pişirme Üniteleri (including itself)
pu_tree = list(pu.get_descendants(include_self=True))
print(f"Categories in Pişirme Üniteleri tree: {len(pu_tree)}")
for cat in pu_tree:
    print(f"  - {cat.name} ({cat.slug})")
print()

# Get all series pointing to Pişirme Üniteleri tree
pu_cat_ids = [c.id for c in pu_tree]
series_in_pu = Series.objects.filter(category_id__in=pu_cat_ids)
print(f"Series in Pişirme Üniteleri: {series_in_pu.count()}")
for s in series_in_pu:
    print(f"  - {s.name} (category: {s.category.name})")
print()

# Get all products directly in Pişirme Üniteleri tree (not via series)
products_in_pu = Product.objects.filter(category_id__in=pu_cat_ids)
print(f"Products directly in Pişirme Üniteleri: {products_in_pu.count()}")
for p in products_in_pu[:10]:
    print(f"  - {p.name} (category: {p.category.name if p.category else 'None'})")
print()

# Plan the migration:
print("=" * 60)
print("MIGRATION PLAN:")
print("=" * 60)
print(f"1. Move {series_in_pu.count()} series from Pişirme Üniteleri → Pişirme Ekipmanları")
print(f"2. Move {products_in_pu.count()} products from Pişirme Üniteleri → Pişirme Ekipmanları")
print(f"3. Move {len(pu_tree) - 1} subcategories to Pişirme Ekipmanları (if any)")
print(f"4. Delete or deactivate Pişirme Üniteleri category")
print()

# Ask for confirmation
response = input("Proceed with migration? (yes/no): ")
if response.lower() != 'yes':
    print("Migration cancelled.")
    exit()

print("\nExecuting migration...")

# 1. Move all subcategories to be children of Pişirme Ekipmanları
subcats = pu.children.all()
for subcat in subcats:
    print(f"  Moving subcategory: {subcat.name}")
    subcat.parent = pe
    subcat.save()

# 2. Move all series
for s in series_in_pu:
    print(f"  Moving series: {s.name}")
    s.category = pe
    s.save()

# 3. Move all products
for p in products_in_pu:
    print(f"  Moving product: {p.name}")
    p.category = pe
    p.save()

# 4. Delete Pişirme Üniteleri
print(f"\nDeleting category: {pu.name}")
pu.delete()

print("\n✅ Migration completed successfully!")
print(f"All content moved to: {pe.name} ({pe.slug})")
