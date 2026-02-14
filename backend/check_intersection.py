
import os
import sys
import django
from django.db.models import Q

# Add backend to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
try:
    django.setup()
except Exception as e:
    print(f"Setup failed: {e}")
    sys.exit(1)

from apps.catalog.models import Category, Product, Brand, Series

def check_intersection():
    cat_slug = "firinlar"
    brand_slug = "rational"
    series_slug = "i-combi-classic-serisi"

    print(f"Checking filters for:")
    print(f"Category: {cat_slug}")
    print(f"Brand: {brand_slug}")
    print(f"Series: {series_slug}")

    # 1. Category Only (via series__category)
    qs_cat = Product.objects.filter(
        status='active',
        series__category__slug=cat_slug
    )
    print(f"\nCategory Only count: {qs_cat.count()}")

    # 2. Brand Only
    qs_brand = Product.objects.filter(
        status='active',
        brand__slug=brand_slug
    )
    print(f"Brand Only count: {qs_brand.count()}")

    # 3. Category + Brand
    qs_cat_brand = Product.objects.filter(
        status='active',
        series__category__slug=cat_slug,
        brand__slug=brand_slug
    )
    print(f"Category + Brand count: {qs_cat_brand.count()}")

    # 4. Series Only
    qs_series = Product.objects.filter(
        status='active',
        series__slug=series_slug
    )
    print(f"Series Only count: {qs_series.count()}")

    # 5. Category + Series
    qs_cat_series = Product.objects.filter(
        status='active',
        series__category__slug=cat_slug,
        series__slug=series_slug
    )
    print(f"Category + Series count: {qs_cat_series.count()}")
    
    # 6. Check a product that SHOULD be there
    if qs_cat_brand.count() == 0:
        print("\nInvestigating why Cat + Brand is 0...")
        # Find products in Brand
        prods = qs_brand.all()
        for p in prods:
             print(f"Product: {p.name}")
             print(f"  Brand: {p.brand.slug}")
             print(f"  Series: {p.series.slug if p.series else 'None'}")
             if p.series:
                 print(f"  Series Cat: {p.series.category.slug}")
             else:
                 print("  No Series")


if __name__ == "__main__":
    check_intersection()
