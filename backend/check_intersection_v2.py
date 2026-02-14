
import os
import sys
import django
from django.db.models import Q, Count

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

def check_series_filtering():
    cat_slug = "firinlar"
    brand_slug = "rational"
    
    print(f"Checking Series filtering for Category='{cat_slug}' and Brand='{brand_slug}'")
    
    # Logic from SeriesListView.get_queryset
    
    # 1. Base Queryset
    queryset = Series.objects.select_related("category").order_by("order", "name")
    
    # 2. Filter by Category
    queryset = queryset.filter(category__slug=cat_slug)
    print(f"Series in Category count: {queryset.count()}")
    
    # 3. Filter by Brand
    queryset_filtered = queryset.filter(products__brand__slug=brand_slug).distinct()
    print(f"Series matching Brand '{brand_slug}': {queryset_filtered.count()}")
    
    for s in queryset_filtered:
        print(f" - {s.name} (slug: {s.slug})")
        # Check product count for this series + brand
        p_count = s.products.filter(
            status='active',
            brand__slug=brand_slug
        ).count()
        print(f"   Products in Series with Brand '{brand_slug}': {p_count}")

if __name__ == "__main__":
    check_series_filtering()
