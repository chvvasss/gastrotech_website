"""
Create missing brands for import errors
"""
from apps.catalog.models import Brand

# Brands to create (coffee/beverage equipment brands)
brands = [
    {'name': 'Bravilor Bonamat', 'slug': 'bravilor-bonamat', 'is_active': True},
    {'name': 'Magister', 'slug': 'magister', 'is_active': True},
    {'name': 'Bezzera', 'slug': 'bezzera', 'is_active': True},
    {'name': 'Dr. Coffee', 'slug': 'dr-coffee', 'is_active': True},
    {'name': 'Fiorenzato', 'slug': 'fiorenzato', 'is_active': True},
    {'name': 'Mahlkönig', 'slug': 'mahlkonig', 'is_active': True},
    {'name': 'PuqPress', 'slug': 'puqpress', 'is_active': True},
    {'name': 'Santos', 'slug': 'santos', 'is_active': True},
    {'name': 'Kalko', 'slug': 'kalko', 'is_active': True},
]

print("Creating brands...")
for brand_data in brands:
    brand, created = Brand.objects.get_or_create(
        slug=brand_data['slug'],
        defaults=brand_data
    )
    if created:
        print(f"✅ Created: {brand.name} ({brand.slug})")
    else:
        print(f"⚠️  Already exists: {brand.name} ({brand.slug})")

print(f"\n✅ Done! {len(brands)} brands processed.")
