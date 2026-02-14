"""
Create missing categories that are causing product import errors.

This script adds 8 missing category slugs referenced by 52 products:
- 6 cooling equipment categories under sogutma-uniteleri
- 1 display equipment category under teshir-uniteleri
- 1 café equipment category under kafeterya-ekipmanlari
"""

import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.catalog.models import Category


def create_missing_categories():
    """Create all missing categories with proper parent assignments."""
    
    print("\n" + "="*60)
    print("CREATING MISSING CATEGORIES")
    print("="*60 + "\n")
    
    created_count = 0
    existing_count = 0
    
    # Get parent categories
    try:
        sogutma = Category.objects.get(slug='sogutma-uniteleri')
        print(f"[OK] Found parent: {sogutma.name} ({sogutma.slug})")
    except Category.DoesNotExist:
        print("[ERROR] Parent category 'sogutma-uniteleri' not found!")
        return
    
    try:
        tamamlayici = Category.objects.get(slug='tamamlayici-ekipmanlar')
        teshir = Category.objects.get(slug='teshir-uniteleri', parent=tamamlayici)
        print(f"[OK] Found parent: {teshir.name} ({teshir.slug})")
    except Category.DoesNotExist:
        print("[ERROR] Parent category 'teshir-uniteleri' not found!")
        return
    
    try:
        kafeterya = Category.objects.get(slug='kafeterya-ekipmanlari')
        print(f"[OK] Found parent: {kafeterya.name} ({kafeterya.slug})")
    except Category.DoesNotExist:
        print("[ERROR] Parent category 'kafeterya-ekipmanlari' not found!")
        return

    
    print("\n" + "-"*60)
    print("COOLING EQUIPMENT CATEGORIES")
    print("-"*60 + "\n")
    
    # Define cooling equipment categories
    cooling_categories = [
        {
            'slug': 'pizza-salata-hazirlik-buzdolaplari',
            'name': 'Pizza & Salata Hazırlık Buzdolapları',
            'description_short': 'Pizza ve salata hazırlık buzdolapları',
            'parent': sogutma,
            'order': 10,
        },
        {
            'slug': 'dik-tip-buzdolaplari',
            'name': 'Dik Tip Buzdolapları',
            'description_short': 'Dikey buzdolapları ve dondurucular',
            'parent': sogutma,
            'order': 20,
        },
        {
            'slug': 'dik-tip-kombinasyonlu-buzdolaplari',
            'name': 'Dik Tip Kombinasyonlu Buzdolapları',
            'description_short': 'Dikey kombinasyonlu soğutmalı buzdolapları',
            'parent': sogutma,
            'order': 30,
        },
        {
            'slug': 'tezgah-tip-buzdolaplari-dondurucu',
            'name': 'Tezgah Tip Buzdolapları & Dondurucu',
            'description_short': 'Tezgah tipi buzdolapları ve dondurucular',
            'parent': sogutma,
            'order': 40,
        },
        {
            'slug': 'sok-sogutucu-dondurucular',
            'name': 'Şok Soğutucu & Dondurucular',
            'description_short': 'Şok soğutma ve dondurma ekipmanları',
            'parent': sogutma,
            'order': 50,
        },
        {
            'slug': 'dry-age-buzdolaplari',
            'name': 'Dry Age Buzdolapları',
            'description_short': 'Et olgunlaştırma buzdolapları',
            'parent': sogutma,
            'order': 60,
        },
    ]
    
    for cat_data in cooling_categories:
        cat, created = Category.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        if created:
            print(f"  [+] Created: {cat.name}")
            created_count += 1
        else:
            print(f"  [=] Exists: {cat.name}")
            existing_count += 1
    
    print("\n" + "-"*60)
    print("DISPLAY EQUIPMENT CATEGORIES")
    print("-"*60 + "\n")
    
    # Define display equipment category
    display_category = {
        'slug': 'setustu-teshir-uniteleri',
        'name': 'Setüstü Teşhir Üniteleri',
        'description_short': 'Tezgah üstü teşhir ekipmanları',
        'parent': teshir,
        'order': 10,
    }
    
    cat, created = Category.objects.get_or_create(
        slug=display_category['slug'],
        defaults=display_category
    )
    if created:
        print(f"  [+] Created: {cat.name}")
        created_count += 1
    else:
        print(f"  [=] Exists: {cat.name}")
        existing_count += 1
    
    print("\n" + "-"*60)
    print("CAFÉ EQUIPMENT CATEGORIES")
    print("-"*60 + "\n")
    
    # Define café equipment category
    cafe_category = {
        'slug': 'kokteyl-tezgahi',
        'name': 'Kokteyl Tezgahı',
        'description_short': 'Kokteyl hazırlık tezgahları',
        'parent': kafeterya,
        'order': 50,
    }
    
    cat, created = Category.objects.get_or_create(
        slug=cafe_category['slug'],
        defaults=cafe_category
    )
    if created:
        print(f"  [+] Created: {cat.name}")
        created_count += 1
    else:
        print(f"  [=] Exists: {cat.name}")
        existing_count += 1
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"  Categories created: {created_count}")
    print(f"  Categories already existed: {existing_count}")
    print(f"  Total categories processed: {created_count + existing_count}")
    print("\n[OK] All missing categories have been created!\n")



if __name__ == '__main__':
    create_missing_categories()
