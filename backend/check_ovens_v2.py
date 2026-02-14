
import os
import sys
import django

# Add backend to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
try:
    django.setup()
except Exception as e:
    print(f"Setup failed: {e}")
    sys.exit(1)

from apps.catalog.models import Category, Product, Brand, Series, BrandCategory

def check_category_data(category_slug):
    try:
        category = Category.objects.get(slug=category_slug)
        print(f"Category found: {category.name} ({category.slug})")
        if category.parent:
            print(f"Parent: {category.parent.name}")
    except Category.DoesNotExist:
        print(f"Category with slug '{category_slug}' not found.")
        return

    # Check products directly in this category
    products = Product.objects.filter(category=category)
    print(f"\nTotal Products in Category: {products.count()}")
    
    active_products = products.filter(status='active')
    print(f"Active Products: {active_products.count()}")

    # Check Series in this category
    series_list = Series.objects.filter(category=category)
    print(f"\nSeries in Category ({series_list.count()}):")
    for s in series_list:
        p_count = s.products.count() # Total products
        visible_p_count = s.products.filter(status='active').count()
        print(f" - {s.name} (slug: {s.slug})") 
        print(f"   Total Prods: {p_count}, Active Prods: {visible_p_count}")
        print(f"   Visible rule (>=2 active): {visible_p_count >= 2}")

    # Check Brands linked to this category
    brand_categories = BrandCategory.objects.filter(category=category)
    print(f"\nBrands linked to Category via BrandCategory ({brand_categories.count()}):")
    for bc in brand_categories:
        print(f" - {bc.brand.name} (slug: {bc.brand.slug})")

    # Check validation of product links
    print("\n--- Product Link Analysis ---")
    missing_brand = 0
    missing_series = 0
    brand_not_in_cat = 0
    series_not_in_cat = 0

    for p in active_products:
        if not p.brand:
            missing_brand += 1
        else:
            # Check if brand is linked to category
            if not BrandCategory.objects.filter(brand=p.brand, category=category).exists():
                brand_not_in_cat += 1
        
        if not p.series:
            missing_series += 1
        else:
            if p.series.category != category:
                series_not_in_cat += 1

    print(f"Products with Missing Brand: {missing_brand}")
    print(f"Products with Brand NOT linked to Category: {brand_not_in_cat}")
    print(f"Products with Missing Series: {missing_series}")
    print(f"Products with Series NOT in Category: {series_not_in_cat}")

if __name__ == "__main__":
    check_category_data("firinlar")
