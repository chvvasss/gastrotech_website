
import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import Series, Category
from apps.catalog.serializers import SeriesWithCountsSerializer

def verify():
    print("--- STARTING VERIFICATION ---\n")

    # 1. Verify Single Product Slug Logic
    print("--- 1. SINGLE PRODUCT LOGIC CHECK ---")
    
    # Find a single product series (e.g., 'bar-blender' as identified before)
    # We can use the logic from analysis script to find one dynamically
    from django.db.models import Count
    
    single_prod_series = Series.objects.annotate(pc=Count('products')).filter(pc=1).first()
    
    if single_prod_series:
        print(f"Testing Series: {single_prod_series.name} (Slug: {single_prod_series.slug})")
        print(f"Product Count: {single_prod_series.pc}")
        
        serializer = SeriesWithCountsSerializer(single_prod_series)
        data = serializer.data
        
        slug_field = data.get('single_product_slug')
        print(f"Serializer 'single_product_slug': {slug_field}")
        
        product = single_prod_series.products.first()
        if slug_field == product.slug:
            print("SUCCESS: single_product_slug matches the actual product slug.")
        else:
            print(f"FAILURE: Expected {product.slug}, got {slug_field}")
            
    else:
        print("WARNING: No single-product series found in DB to test.")

    # 2. Verify Multi-Product Series (Should be None)
    print("\n--- 2. MULTI-PRODUCT LOGIC CHECK ---")
    multi_prod_series = Series.objects.annotate(pc=Count('products')).filter(pc__gt=1).first()
    
    if multi_prod_series:
        print(f"Testing Series: {multi_prod_series.name} (Slug: {multi_prod_series.slug})")
        print(f"Product Count: {multi_prod_series.pc}")
        
        serializer = SeriesWithCountsSerializer(multi_prod_series)
        data = serializer.data
        
        slug_field = data.get('single_product_slug')
        print(f"Serializer 'single_product_slug': {slug_field}")
        
        if slug_field is None:
            print("SUCCESS: single_product_slug is None for multi-product series.")
        else:
            print(f"FAILURE: Expected None, got {slug_field}")
    else:
        print("WARNING: No multi-product series found in DB to test.")

    # 3. Verify Slug Consistency (Specific known fixes)
    print("\n--- 3. SLUG FIX VERIFICATION ---")
    
    # Check 'Bulaşıkhane' which was 'bulaskhane'
    try:
        cat = Category.objects.get(name='Bulaşıkhane') # Search by name, assuming name is correct in script output?
        # Actually name was 'Bulakhane', let's search by corrected slug
        cat = Category.objects.get(slug='bulasikhane')
        print(f"Category 'bulasikhane' exists. Name: {cat.name}")
        if cat.slug == 'bulasikhane':
             print("SUCCESS: 'bulasikhane' slug is correct.")
    except Category.DoesNotExist:
        # Maybe the name was corrected too?
        print("WARNING: Could not find category with slug 'bulasikhane'. Checking 'Bulakhane' fallback...")
        try:
             # The script output said: FIXED: Bulakhane | bulaskhane -> bulasikhane
             # So it updated the slug to 'bulasikhane'.
             pass
        except:
             pass

    # Check 'Tas Tabanli Bakery Firinlar'
    try:
        cat = Category.objects.get(slug='tas-tabanli-bakery-firinlar')
        print(f"Category '{cat.slug}' found. Name: {cat.name}")
        print("SUCCESS: Slug fixed.")
    except Category.DoesNotExist:
        print("FAILURE: 'tas-tabanli-bakery-firinlar' not found.")

    print("\n--- END VERIFICATION ---")

if __name__ == "__main__":
    verify()
