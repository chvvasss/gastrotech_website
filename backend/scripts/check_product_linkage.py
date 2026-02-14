
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Product, Series

def check_product_linkage():
    print("=== Checking Product Linkage ===\n")
    
    # Sample some products
    products = Product.objects.all()[:20]
    
    null_series = 0
    null_category = 0
    
    print("Sample Products:")
    for p in products:
        series_name = p.series.name if p.series else "NULL"
        category_name = p.category.name if p.category else "NULL"
        
        if not p.series:
            null_series += 1
        if not p.category:
            null_category += 1
            
        print(f"- {p.title_tr[:40]:<40} | Series: {series_name[:30]:<30} | Category: {category_name[:30]}")
    
    print(f"\nOut of {products.count()} sampled products:")
    print(f"  - NULL series: {null_series}")
    print(f"  - NULL category: {null_category}")
    
    # Check total counts
    total_products = Product.objects.count()
    total_null_series = Product.objects.filter(series__isnull=True).count()
    total_null_category = Product.objects.filter(category__isnull=True).count()
    
    print(f"\nTotal in database:")
    print(f"  - Total products: {total_products}")
    print(f"  - NULL series: {total_null_series}")
    print(f"  - NULL category: {total_null_category}")
    
    # Check if series_id exists but products aren't showing up
    hazirlik_series = Series.objects.filter(category__slug='hazirlik-ekipmanlari').first()
    if hazirlik_series:
        print(f"\n=== Sample Series: {hazirlik_series.name} ===")
        print(f"ID: {hazirlik_series.id}")
        
        # Direct query
        products_in_series = Product.objects.filter(series_id=hazirlik_series.id)
        print(f"Products with this series_id: {products_in_series.count()}")
        
        if products_in_series.exists():
            print("Sample products:")
            for p in products_in_series[:5]:
                print(f"  - {p.title_tr}")

if __name__ == "__main__":
    check_product_linkage()
