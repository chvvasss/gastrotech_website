
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Category, Product

def list_all_firinlar_categories():
    print("=== All Categories containing 'firin' ===\n")
    
    firin_cats = Category.objects.filter(slug__icontains='firin')
    
    for cat in firin_cats:
        products_count = Product.objects.filter(category=cat).count()
        series_count = cat.series.count()
        
        print(f"Category: {cat.name}")
        print(f"  Slug: {cat.slug}")
        print(f"  ID: {cat.id}")
        print(f"  Products: {products_count}")
        print(f"  Series: {series_count}")
        print(f"  Parent: {cat.parent.name if cat.parent else 'None'}")
        print()
    
    print("=== All Categories containing 'hazirlik' ===\n")
    
    hazirlik_cats = Category.objects.filter(slug__icontains='hazirlik')
    
    for cat in hazirlik_cats:
        products_count = Product.objects.filter(category=cat).count()
        series_count = cat.series.count()
        
        print(f"Category: {cat.name}")
        print(f"  Slug: {cat.slug}")
        print(f"  ID: {cat.id}")
        print(f"  Products: {products_count}")
        print(f"  Series: {series_count}")
        print(f"  Parent: {cat.parent.name if cat.parent else 'None'}")
        print()

if __name__ == "__main__":
    list_all_firinlar_categories()
