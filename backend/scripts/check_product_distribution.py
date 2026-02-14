
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import models
from apps.catalog.models import Category, Product, Series

def check_product_distribution():
    print("=== Product Distribution by Category ===\n")
    
    # Get all categories with product counts
    categories = Category.objects.annotate(
        direct_products=models.Count(
            'products',
            filter=models.Q(products__status='active'),
            distinct=True
        ),
        series_products=models.Count(
            'series__products',
            filter=models.Q(series__products__status='active'),
            distinct=True
        )
    ).filter(
        models.Q(direct_products__gt=0) | models.Q(series_products__gt=0)
    ).order_by('-direct_products', '-series_products')
    
    print(f"Categories with products: {categories.count()}\n")
    
    for cat in categories[:20]:
        total = cat.direct_products + cat.series_products
        print(f"{cat.slug:<40} | Direct: {cat.direct_products:3} | Via Series: {cat.series_products:3} | Total: ~{total}")
        if 'firin' in cat.slug.lower() or 'firin' in cat.name.lower():
            print(f"  ^ THIS ONE HAS 'FIRIN' IN NAME!")
    
    # Check specific products
    print("\n\n=== Sample Products ===")
    sample_prods = Product.objects.filter(status='active').select_related('category', 'series', 'series__category')[:10]
    for p in sample_prods:
        cat_name = p.category.name if p.category else "NULL"
        series_cat = p.series.category.name if (p.series and p.series.category) else "NULL"
        print(f"  - {p.title_tr[:40]:<40} | Category: {cat_name:<30} | Series.Category: {series_cat}")

if __name__ == "__main__":
    check_product_distribution()
