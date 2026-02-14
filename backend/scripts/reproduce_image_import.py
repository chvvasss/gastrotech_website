
import os
import sys
import django
import uuid

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.catalog.models import Product, Brand, Category, Series
from apps.catalog.services.json_import_service import JsonImportService

def reproduce_issue():
    print("Starting Reproduction Script...")
    
    # Setup Data
    brand, _ = Brand.objects.get_or_create(slug="test-brand", defaults={"name": "Test Brand"})
    category, _ = Category.objects.get_or_create(slug="test-cat", defaults={"name": "Test Cat"})
    series, _ = Series.objects.get_or_create(slug="test-series", category=category, defaults={"name": "Test Series"})
    
    slug = f"test-product-{uuid.uuid4().hex[:6]}"
    
    product_data = {
        "slug": slug,
        "name": "Test Product",
        "category": "test-cat",
        "series": "test-series",
        "brand": "test-brand",
        "variants": [{"model_code": "TEST-01"}],
        "images": []
    }
    
    # 1. Create Product WITHOUT images
    print(f"\n1. Creating product {slug} without images...")
    service = JsonImportService([product_data], dry_run=False) # Direct commit
    result = service.process()
    print(f"Result: {result['success']}")
    
    p = Product.objects.get(slug=slug)
    print(f"Product Created. Media count: {p.product_media.count()}")
    
    # 2. Update Product WITH images
    print("\n2. Updating product WITH images...")
    product_data["images"] = [
        "https://vital.b-cdn.net/01VTL-GKO7010/P0001VTL-GKO70101.png"
    ]
    
    service = JsonImportService([product_data], dry_run=False)
    result = service.process()
    print(f"Result: {result['success']}")
    
    p.refresh_from_db()
    count = p.product_media.count()
    print(f"Product Updated. Media count: {count}")
    
    if count == 0:
        print("FAIL: Images were NOT added on update.")
    else:
        print("SUCCESS: Images were added.")
        
    # Cleanup
    p.delete()
    print("\nCleanup done.")

if __name__ == "__main__":
    reproduce_issue()
