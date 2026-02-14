
import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.catalog.services.json_import_service import JsonImportService

def test_service():
    print("Testing JsonImportService...")
    data = [
        {
            "slug": "sanity-check-product",
            "name": "Sanity Check",
            "category": "firinlar", # specific slug might need adjusting if DB is empty/reset
            "brand": "gastrotech"
        }
    ]
    
    # We need to make sure Category/Brand exist since we reset DB.
    # But wait, Categories/Brands were PRESERVED.
    # Let's hope 'firinlar' and 'gastrotech' exist. 
    # If not, the service should raise an error, which is also a valid test result (service running).
    
    try:
        from apps.catalog.models import Category, Brand
        if not Category.objects.exists():
            print("WARNING: No categories found! Service will fail.")
        else:
            print(f"Categories count: {Category.objects.count()}")

        # Pick first category/brand to be safe
        cat = Category.objects.first()
        brand = Brand.objects.first()
        
        if cat and brand:
            data[0]["category"] = cat.slug
            data[0]["brand"] = brand.slug
            print(f"Using Category: {cat.slug}, Brand: {brand.slug}")
        
        result = JsonImportService.preview(data)
        print("Service Result:", result)
        
        if result['success']:
            print("SUCCESS: Service is working.")
        else:
            print("FAILURE: Service returned errors (but is running).")
            print(result['stats']['errors'])

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_service()
