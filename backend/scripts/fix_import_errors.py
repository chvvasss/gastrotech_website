
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.catalog.models import Category, Brand
from apps.common.slugify_tr import slugify_tr

def fix_import_errors():
    print("Fixing Category Slugs...")
    
    # 1. Fix Pişirme Ekipmanları -> Pişirme Üniteleri
    try:
        cat = Category.objects.get(slug='pisirme-ekipmanlari')
        cat.name = "Pişirme Üniteleri"
        cat.slug = "pisirme-uniteleri"
        cat.save()
        print("Updated: Pişirme Ekipmanları -> Pişirme Üniteleri")
    except Category.DoesNotExist:
        print("Category 'pisirme-ekipmanlari' not found (maybe already fixed?)")

    # 2. Fix Bulaşıkhane -> Bulaşık Makineleri
    try:
        cat = Category.objects.get(slug='bulasikhane')
        cat.name = "Bulaşık Makineleri"
        cat.slug = "bulasik-makineleri"
        cat.save()
        print("Updated: Bulaşıkhane -> Bulaşık Makineleri")
    except Category.DoesNotExist:
        print("Category 'bulasikhane' not found (maybe already fixed?)")

    # 3. Create 'Aksesuarlar'
    cat, created = Category.objects.get_or_create(
        slug='aksesuarlar',
        defaults={
            'name': 'Aksesuarlar',
            'order': 9,
            'is_featured': True
        }
    )
    if created:
        print("Created: Aksesuarlar")
    else:
        print("Existing: Aksesuarlar")

    print("\nCreating Missing Brands...")
    brands = [
        "Gastrotech", "Electrolux", "Salva", "Asterm", "Mychef", 
        "Frenox", "Scotsman", "Bravilor Bonamat", "Magister", 
        "La Cimbali", "Bezzera", "Gtech", "Fiorenzato", 
        "Pietro Grinders", "Mahlkonig", "Puqpress", "Cunill", 
        "Kalko", "Cambro", "Imperia", "KitchenAid"
    ]

    for brand_name in brands:
        brand, created = Brand.objects.get_or_create(
            slug=slugify_tr(brand_name),
            defaults={'name': brand_name, 'is_active': True}
        )
        if created:
            print(f"Created Brand: {brand_name}")
        else:
            print(f"Existing Brand: {brand_name}")

    print("\nFixes Terminated.")

if __name__ == '__main__':
    fix_import_errors()
