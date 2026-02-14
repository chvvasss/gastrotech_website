
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Category, Product

def debug_empty_categories():
    print("--- Debug Empty Categories ---\n")
    
    # Check Fırınlar
    print("=== Fırınlar Category ===")
    firinlar = Category.objects.filter(slug__icontains='firin').first()
    if firinlar:
        print(f"Found: {firinlar.name} (slug: {firinlar.slug})")
        print(f"ID: {firinlar.id}")
        products = Product.objects.filter(category=firinlar)
        print(f"Products directly linked to this category: {products.count()}")
        
        # Check via series
        series_count = firinlar.series.count()
        print(f"Series under this category: {series_count}")
        
        if series_count > 0:
            print("\nSeries details:")
            for s in firinlar.series.all()[:5]:
                prod_count = Product.objects.filter(series=s).count()
                print(f"  - {s.name}: {prod_count} products")
    else:
        print("NOT FOUND")
    
    print("\n=== Hazırlık Ekipmanları Category ===")
    hazirlik = Category.objects.filter(slug__icontains='hazirlik').first()
    if hazirlik:
        print(f"Found: {hazirlik.name} (slug: {hazirlik.slug})")
        print(f"ID: {hazirlik.id}")
        products = Product.objects.filter(category=hazirlik)
        print(f"Products directly linked to this category: {products.count()}")
        
        series_count = hazirlik.series.count()
        print(f"Series under this category: {series_count}")
        
        if series_count > 0:
            print("\nSeries details:")
            for s in hazirlik.series.all()[:5]:
                prod_count = Product.objects.filter(series=s).count()
                print(f"  - {s.name}: {prod_count} products")
    else:
        print("NOT FOUND")
    
    # Check for products with NULL category
    print("\n=== Products with NULL category ===")
    null_cat_products = Product.objects.filter(category__isnull=True)
    print(f"Total: {null_cat_products.count()}")
    if null_cat_products.exists():
        print("Sample products:")
        for p in null_cat_products[:10]:
            series_name = p.series.name if p.series else "NO SERIES"
            print(f"  - {p.title_tr} (Series: {series_name})")

if __name__ == "__main__":
    debug_empty_categories()
