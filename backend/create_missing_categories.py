"""
Create missing categories for import errors
"""
from apps.catalog.models import Category

# Get parent category
kafeterya = Category.objects.get(slug='kafeterya-ekipmanlari')

# Categories to create
categories = [
    # Coffee equipment
    {
        'name': 'Kahve Makineleri',
        'slug': 'kahve-makineleri',
        'parent': kafeterya,
        'order': 1,
    },
    {
        'name': 'Kahve Değirmenleri',
        'slug': 'kahve-degirmenleri',
        'parent': kafeterya,
        'order': 2,
    },
    {
        'name': 'Kahve Ekipmanları',
        'slug': 'kahve-ekipmanlari',
        'parent': kafeterya,
        'order': 3,
    },
    # Beverage equipment
    {
        'name': 'İçecek Hazırlık',
        'slug': 'icecek-hazirlik',
        'parent': kafeterya,
        'order': 4,
    },
]

# Check if we need teshir-uniteleri under a different parent
# It's "display units" so might go under "Tamamlayıcı Ekipmanlar"
tamamlayici = Category.objects.filter(slug='tamamlayici-ekipmanlar').first()
if tamamlayici:
    categories.append({
        'name': 'Teşhir Üniteleri',
        'slug': 'teshir-uniteleri',
        'parent': tamamlayici,
        'order': 1,
    })
else:
    # If not found, put it under root
    categories.append({
        'name': 'Teşhir Üniteleri',
        'slug': 'teshir-uniteleri',
        'parent': None,
        'order': 100,
    })

print("Creating categories...")
for cat_data in categories:
    cat, created = Category.objects.get_or_create(
        slug=cat_data['slug'],
        defaults=cat_data
    )
    if created:
        print(f"✅ Created: {cat.name} ({cat.slug}) under {cat.parent.name if cat.parent else 'ROOT'}")
    else:
        print(f"⚠️  Already exists: {cat.name} ({cat.slug})")

print("\n✅ Done! All categories created.")
