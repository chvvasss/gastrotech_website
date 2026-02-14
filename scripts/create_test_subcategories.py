"""
Create test subcategories for demonstration.

Creates a complete hierarchy:
- Fırınlar (root)
  - Pizza Fırını (subcategory)
  - Elektrikli Fırın (subcategory)
- Soğutma (root)
  - Buzdolabı (subcategory)
  - Derin Dondurucu (subcategory)
"""

import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.catalog.models import Category, Series, Brand, Product, Variant


def create_test_hierarchy():
    print("Creating test subcategory hierarchy...")

    # Create or get root category: Fırınlar
    firinlar, created = Category.objects.get_or_create(
        slug='firinlar',
        defaults={
            'name': 'Fırınlar',
            'description_short': 'Profesyonel fırın çözümleri',
            'order': 1,
        }
    )
    if created:
        print(f"[+] Created root category: {firinlar.name}")
    else:
        print(f"[+] Found existing category: {firinlar.name}")

    # Create subcategories under Fırınlar
    pizza_firini, created = Category.objects.get_or_create(
        slug='pizza-firini',
        defaults={
            'name': 'Pizza Fırını',
            'description_short': 'Pizza pişirme için özel tasarlanmış fırınlar',
            'parent': firinlar,
            'order': 1,
        }
    )
    if created:
        print(f"  [+] Created subcategory: {pizza_firini.name}")
    else:
        print(f"  [+] Found existing subcategory: {pizza_firini.name}")

    elektrikli_firin, created = Category.objects.get_or_create(
        slug='elektrikli-firin',
        defaults={
            'name': 'Elektrikli Fırın',
            'description_short': 'Elektrikli konveksiyonlu fırınlar',
            'parent': firinlar,
            'order': 2,
        }
    )
    if created:
        print(f"  [+] Created subcategory: {elektrikli_firin.name}")
    else:
        print(f"  [+] Found existing subcategory: {elektrikli_firin.name}")

    # Create or get root category: Soğutma
    sogutma, created = Category.objects.get_or_create(
        slug='sogutma',
        defaults={
            'name': 'Soğutma Üniteleri',
            'description_short': 'Profesyonel soğutma çözümleri',
            'order': 2,
        }
    )
    if created:
        print(f"[+] Created root category: {sogutma.name}")
    else:
        print(f"[+] Found existing category: {sogutma.name}")

    # Create subcategories under Soğutma
    buzdolabi, created = Category.objects.get_or_create(
        slug='buzdolabi',
        defaults={
            'name': 'Buzdolabı',
            'description_short': 'Profesyonel buzdolapları',
            'parent': sogutma,
            'order': 1,
        }
    )
    if created:
        print(f"  [+] Created subcategory: {buzdolabi.name}")
    else:
        print(f"  [+] Found existing subcategory: {buzdolabi.name}")

    derin_dondurucu, created = Category.objects.get_or_create(
        slug='derin-dondurucu',
        defaults={
            'name': 'Derin Dondurucu',
            'description_short': 'Derin dondurma çözümleri',
            'parent': sogutma,
            'order': 2,
        }
    )
    if created:
        print(f"  [+] Created subcategory: {derin_dondurucu.name}")
    else:
        print(f"  [+] Found existing subcategory: {derin_dondurucu.name}")

    print("\n" + "="*50)
    print("Creating test brands, series, and products...")
    print("="*50 + "\n")

    # Create brands
    gastrotech, _ = Brand.objects.get_or_create(
        slug='gastrotech',
        defaults={
            'name': 'Gastrotech',
            'description': 'Premium mutfak ekipmanları üreticisi',
            'order': 1,
            'is_active': True,
        }
    )
    print(f"[+] Brand: {gastrotech.name}")

    partner_a, _ = Brand.objects.get_or_create(
        slug='partner-a',
        defaults={
            'name': 'Partner A',
            'description': 'Partner marka A',
            'order': 2,
            'is_active': True,
        }
    )
    print(f"[+] Brand: {partner_a.name}")

    # Create series for Pizza Fırını
    series_pizza_600, created = Series.objects.get_or_create(
        slug='pizza-600',
        category=pizza_firini,  # Point to LEAF category
        defaults={
            'name': '600 Series',
            'description_short': 'Profesyonel pizza fırınları 600 serisi',
            'order': 1,
        }
    )
    if created:
        print(f"[+] Series: {series_pizza_600.name} (under {pizza_firini.name})")
    else:
        # Update category if series exists but points to wrong category
        if series_pizza_600.category != pizza_firini:
            series_pizza_600.category = pizza_firini
            series_pizza_600.save()
            print(f"[+] Updated series: {series_pizza_600.name} -> {pizza_firini.name}")
        else:
            print(f"[+] Series: {series_pizza_600.name}")

    # Create product for Pizza 600 Series
    product_pizza, created = Product.objects.get_or_create(
        slug='pizza-oven-600',
        defaults={
            'name': 'Pizza Oven 600',
            'title_tr': 'Pizza Fırını 600',
            'title_en': 'Pizza Oven 600',
            'series': series_pizza_600,
            'brand': gastrotech,
            'status': 'active',
        }
    )
    if created:
        print(f"  [+] Product: {product_pizza.title_tr}")
    else:
        print(f"  [+] Found product: {product_pizza.title_tr}")

    # Create variants
    variant_1, created = Variant.objects.get_or_create(
        model_code='PO-600-1',
        defaults={
            'product': product_pizza,
            'name_tr': 'Pizza Fırını 600 - Tek Hazneli',
            'name_en': 'Pizza Oven 600 - Single Chamber',
            'list_price': 45000,
        }
    )
    if created:
        print(f"    [+] Variant: {variant_1.model_code}")

    variant_2, created = Variant.objects.get_or_create(
        model_code='PO-600-2',
        defaults={
            'product': product_pizza,
            'name_tr': 'Pizza Fırını 600 - Çift Hazneli',
            'name_en': 'Pizza Oven 600 - Double Chamber',
            'list_price': 75000,
        }
    )
    if created:
        print(f"    [+] Variant: {variant_2.model_code}")

    # Create series for Elektrikli Fırın
    series_elektrik_700, created = Series.objects.get_or_create(
        slug='elektrik-700',
        category=elektrikli_firin,  # Point to LEAF category
        defaults={
            'name': '700 Series',
            'description_short': 'Elektrikli konveksiyonlu fırınlar 700 serisi',
            'order': 1,
        }
    )
    if created:
        print(f"[+] Series: {series_elektrik_700.name} (under {elektrikli_firin.name})")
    else:
        if series_elektrik_700.category != elektrikli_firin:
            series_elektrik_700.category = elektrikli_firin
            series_elektrik_700.save()
            print(f"[+] Updated series: {series_elektrik_700.name} -> {elektrikli_firin.name}")
        else:
            print(f"[+] Series: {series_elektrik_700.name}")

    # Create product for Elektrik 700 Series
    product_elektrik, created = Product.objects.get_or_create(
        slug='electric-oven-700',
        defaults={
            'name': 'Electric Oven 700',
            'title_tr': 'Elektrikli Fırın 700',
            'title_en': 'Electric Convection Oven 700',
            'series': series_elektrik_700,
            'brand': partner_a,
            'status': 'active',
        }
    )
    if created:
        print(f"  [+] Product: {product_elektrik.title_tr}")
    else:
        print(f"  [+] Found product: {product_elektrik.title_tr}")

    variant_3, created = Variant.objects.get_or_create(
        model_code='EO-700-4',
        defaults={
            'product': product_elektrik,
            'name_tr': 'Elektrikli Fırın 700 - 4 Tepsi',
            'name_en': 'Electric Oven 700 - 4 Tray',
            'list_price': 55000,
        }
    )
    if created:
        print(f"    [+] Variant: {variant_3.model_code}")

    print("\n" + "="*50)
    print("HIERARCHY SUMMARY")
    print("="*50)

    # Print hierarchy
    for root in Category.objects.filter(parent__isnull=True).order_by('order'):
        print(f"\n[-] {root.name} (root)")
        print(f"   is_root: {root.is_root}, is_leaf: {root.is_leaf}, depth: {root.depth}")

        for sub in root.children.all().order_by('order'):
            print(f"     |- [>] {sub.name} (subcategory)")
            print(f"      is_root: {sub.is_root}, is_leaf: {sub.is_leaf}, depth: {sub.depth}")

            series_list = Series.objects.filter(category=sub)
            for ser in series_list:
                print(f"           |- [S] {ser.name}")
                products = Product.objects.filter(series=ser, status='active')
                for prod in products:
                    variants = prod.variants.all()
                    print(f"              |- [P] {prod.title_tr} ({variants.count()} variants)")

    print("\n" + "="*50)
    print("[OK] Test data created successfully!")
    print("="*50)
    print("\nTest the following URLs:")
    print("- http://localhost:8000/api/v1/categories/tree/")
    print("- http://localhost:8000/api/v1/categories/firinlar/children/")
    print("- http://localhost:8000/api/v1/brands?category=pizza-firini")
    print("- http://localhost:8000/api/v1/series?category=pizza-firini&brand=gastrotech")
    print("- http://localhost:8000/api/v1/products?category=pizza-firini")
    print("\nFrontend:")
    print("- http://localhost:3000/kategori/firinlar")
    print("- http://localhost:3000/kategori/firinlar?subcategory=pizza-firini")
    print("- http://localhost:3000/kategori/firinlar?subcategory=pizza-firini&brand=gastrotech")


if __name__ == '__main__':
    create_test_hierarchy()
