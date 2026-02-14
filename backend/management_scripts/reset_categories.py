"""
Django management script to reset and create main categories.
Run with: python manage.py shell < management_scripts/reset_categories.py
"""

from django.db import transaction
from apps.catalog.models import Category, Product, ProductVariant, Series, Brand

def reset_all_categories():
    """Delete all categories, products, series, and brands."""
    print("\n" + "="*70)
    print("RESETTING DATABASE - DELETING ALL DATA")
    print("="*70)

    with transaction.atomic():
        # Delete in correct order to avoid FK constraints
        print("\n[1/5] Deleting Product Variants...")
        variant_count = ProductVariant.objects.count()
        ProductVariant.objects.all().delete()
        print(f"    ✓ Deleted {variant_count} variants")

        print("\n[2/5] Deleting Products...")
        product_count = Product.objects.count()
        Product.objects.all().delete()
        print(f"    ✓ Deleted {product_count} products")

        print("\n[3/5] Deleting Series...")
        series_count = Series.objects.count()
        Series.objects.all().delete()
        print(f"    ✓ Deleted {series_count} series")

        print("\n[4/5] Deleting Categories...")
        category_count = Category.objects.count()
        Category.objects.all().delete()
        print(f"    ✓ Deleted {category_count} categories")

        print("\n[5/5] Deleting Brands...")
        brand_count = Brand.objects.count()
        Brand.objects.all().delete()
        print(f"    ✓ Deleted {brand_count} brands")

    print("\n✅ Database reset complete!\n")

def create_main_categories():
    """Create the 8 main root categories."""
    print("="*70)
    print("CREATING MAIN CATEGORIES")
    print("="*70 + "\n")

    categories = [
        {
            'name': 'Pişirme Ekipmanları',
            'slug': 'pisirme-ekipmanlari',
            'description_short': 'Profesyonel mutfak pişirme çözümleri',
            'order': 1,
        },
        {
            'name': 'Fırınlar',
            'slug': 'firinlar',
            'description_short': 'Profesyonel fırın çözümleri',
            'order': 2,
        },
        {
            'name': 'Soğutma Üniteleri',
            'slug': 'sogutma-uniteleri',
            'description_short': 'Endüstriyel soğutma sistemleri',
            'order': 3,
        },
        {
            'name': 'Hazırlık Ekipmanları',
            'slug': 'hazirlik-ekipmanlari',
            'description_short': 'Mutfak hazırlık ve işleme ekipmanları',
            'order': 4,
        },
        {
            'name': 'Kafeterya Ekipmanları',
            'slug': 'kafeterya-ekipmanlari',
            'description_short': 'Kafeterya ve self-servis çözümleri',
            'order': 5,
        },
        {
            'name': 'Çamaşırhane',
            'slug': 'camasirhane',
            'description_short': 'Endüstriyel çamaşırhane ekipmanları',
            'order': 6,
        },
        {
            'name': 'Tamamlayıcı Ekipmanlar',
            'slug': 'tamamlayici-ekipmanlar',
            'description_short': 'Mutfak tamamlayıcı ekipmanları',
            'order': 7,
        },
        {
            'name': 'Bulaşıkhane',
            'slug': 'bulasıkhane',
            'description_short': 'Profesyonel bulaşıkhane sistemleri',
            'order': 8,
        },
    ]

    created_categories = []

    with transaction.atomic():
        for cat_data in categories:
            category = Category.objects.create(
                name=cat_data['name'],
                slug=cat_data['slug'],
                description_short=cat_data['description_short'],
                order=cat_data['order'],
                parent=None,  # Root category
                is_featured=True,
                menu_label=cat_data['name'],
            )
            created_categories.append(category)
            print(f"✓ Created: {category.name} (slug: {category.slug})")

    print(f"\n✅ Successfully created {len(created_categories)} main categories!\n")
    return created_categories

def verify_categories():
    """Verify created categories."""
    print("="*70)
    print("VERIFICATION")
    print("="*70 + "\n")

    root_categories = Category.objects.filter(parent=None).order_by('order')

    print(f"Total root categories: {root_categories.count()}\n")
    print("Category Structure:")
    print("-" * 50)

    for cat in root_categories:
        print(f"{cat.order}. {cat.name}")
        print(f"   Slug: {cat.slug}")
        print(f"   Featured: {cat.is_featured}")
        print(f"   Description: {cat.description_short}")
        print()

    print("✅ Verification complete!\n")

# Run the script
print("\n")
print("╔" + "="*68 + "╗")
print("║" + " "*15 + "CATEGORY RESET & CREATION SCRIPT" + " "*21 + "║")
print("╚" + "="*68 + "╝")
print()

# Step 1: Reset everything
reset_all_categories()

# Step 2: Create main categories
create_main_categories()

# Step 3: Verify
verify_categories()

print("="*70)
print("🎉 ALL DONE!")
print("="*70)
print()
print("Next steps:")
print("1. Restart Django server: python manage.py runserver")
print("2. Visit: http://localhost:3000/kategori")
print("3. All 8 main categories should be visible")
print()
