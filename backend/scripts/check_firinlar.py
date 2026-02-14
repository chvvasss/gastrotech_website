
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import models
from apps.catalog.models import Category, Product

def check_firinlar():
    print("=== Checking Fırınlar Category ===\n")
    
    # Find category
    try:
        cat = Category.objects.get(slug='firinlar')
        print(f"✓ Category found: {cat.name} (ID: {cat.id})")
        print(f"  Parent: {cat.parent.name if cat.parent else 'None'}")
    except Category.DoesNotExist:
        print("✗ Category 'firinlar' NOT FOUND!")
        print("\nAvailable categories with 'firin' in slug:")
        for c in Category.objects.filter(slug__icontains='firin'):
            print(f"  - {c.slug} ({c.name})")
        return
    
    # Get descendants
    descendants = cat.get_descendants(include_self=True)
    desc_ids = [d.id for d in descendants]
    
    print(f"\nCategory tree (including descendants): {len(descendants)} categories")
    for d in descendants[:10]:
        print(f"  - {d.name} (slug: {d.slug})")
    
    # Check products
    products = Product.objects.filter(
        category_id__in=desc_ids,
        status='active'
    )
    
    series_products = Product.objects.filter(
        series__category_id__in=desc_ids,
        status='active'
    )
    
    all_products = Product.objects.filter(
        status='active'
    ).filter(
        models.Q(category_id__in=desc_ids) | models.Q(series__category_id__in=desc_ids)
    ).distinct()
    
    print(f"\nProducts linked to category: {products.count()}")
    print(f"Products linked via series: {series_products.count()}")
    print(f"Total unique products: {all_products.count()}")
    
    if all_products.exists():
        print("\nSample products:")
        for p in all_products[:5]:
            print(f"  - {p.title_tr}")
    else:
        print("\n✗ NO PRODUCTS FOUND!")

if __name__ == "__main__":
    check_firinlar()
