
from apps.catalog.models import Category, Product, Brand, Series, BrandCategory

def check_category_data(category_slug):
    try:
        category = Category.objects.get(slug=category_slug)
        print(f"Category found: {category.name} ({category.slug})")
        print(f"Parent: {category.parent.name if category.parent else 'None'}")
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
        p_count = s.products.count()
        print(f" - {s.name} (slug: {s.slug}, id: {s.id}) - Products: {p_count} (Visible rule >= 2: {p_count >= 2})")

    # Check Brands linked to this category
    brand_categories = BrandCategory.objects.filter(category=category)
    print(f"\nBrands linked to Category via BrandCategory ({brand_categories.count()}):")
    for bc in brand_categories:
        print(f" - {bc.brand.name} (slug: {bc.brand.slug})")

    # Check Products' Brands and Series
    print("\nSample Products (first 10):")
    for p in active_products[:10]:
        print(f" - {p.name}")
        brand_name = p.brand.name if p.brand else 'NONE'
        series_name = p.series.name if p.series else 'NONE'
        print(f"   Brand: {brand_name}")
        print(f"   Series: {series_name}")
        
        # Check if brand is in category
        if p.brand:
            is_linked = BrandCategory.objects.filter(brand=p.brand, category=category).exists()
            print(f"   Brand '{p.brand.name}' linked to category? {is_linked}")
        
        # Check if series is in category
        if p.series:
            is_in_cat = p.series.category == category
            print(f"   Series '{series_name}' in category? {is_in_cat}")

check_category_data("firinlar")
