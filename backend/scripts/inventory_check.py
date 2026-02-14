import os
import sys
import django

sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Category, Series, Brand, Product

def print_tree():
    print("--- ROOT CATEGORIES ---")
    roots = Category.objects.filter(parent__isnull=True).order_by('order', 'name')
    for root in roots:
        print(f"[CAT] {root.name} ({root.slug})")
        children = root.children.all().order_by('order', 'name')
        for child in children:
            print(f"  └── [SUB] {child.name} ({child.slug})")
            series_list = child.series.all().order_by('order', 'name')
            brands = child.brands.all()
            
            print(f"      [BRANDS]: {', '.join([b.name for b in brands])}")
            
            for s in series_list:
                prod_count = s.products.count()
                print(f"      └── [SERIES] {s.name} ({s.slug}) [{prod_count} products]")

    print("\n--- ALL BRANDS ---")
    for b in Brand.objects.all().order_by('name'):
        print(f"[BRAND] {b.name} ({b.slug})")

if __name__ == "__main__":
    print_tree()
