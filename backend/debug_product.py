
from apps.catalog.models import Product, Series, Category

def debug_product(name_part):
    print(f"Searching for products containing: '{name_part}'")
    products = Product.objects.filter(title_tr__icontains=name_part)
    
    if not products.exists():
        print("No products found.")
        return

    for p in products:
        print(f"\n--- Product: {p.title_tr} (Slug: {p.slug}) ---")
        print(f"ID: {p.id}")
        print(f"Status: {p.status}")
        
        # Series Info
        series = p.series
        print(f"Series: {series.name} (Slug: {series.slug})")
        
        # Series Category Info
        cat = series.category
        print(f"Series Category: {cat.name} (Slug: {cat.slug})")
        print(f"Series Category Parent: {cat.parent.name if cat.parent else 'None (ROOT)'}")
        
        # Product Direct Category (if any)
        p_cat = p.category
        if p_cat:
            print(f"Product.category: {p_cat.name} (Slug: {p_cat.slug})")
        else:
            print("Product.category: None")

        # Check visibility logic match
        print("Is Series Visible (>=2 products)?", series.is_visible)
        print("Series Product Count:", series.product_count)

debug_product("Elektrikli Buharlı Konveksiyonlu Dijital Fırın")
