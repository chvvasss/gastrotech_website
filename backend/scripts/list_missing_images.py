
import os
import sys
import django

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Product

def list_missing_images():
    print("--- Products Missing Images ---")
    print(f"{'Product Name':<50} | {'Model Code':<20}")
    print("-" * 75)
    
    # Products with no product_media linked
    products_without_images = Product.objects.filter(product_media__isnull=True)
    
    count = 0
    for product in products_without_images:
        # Get first variant for model code
        first_variant = product.variants.first()
        model_code = first_variant.model_code if first_variant else "NO VARIANT"
        
        print(f"{product.title_tr:<50} | {model_code:<20}")
        count += 1
        
    print("-" * 75)
    print(f"Total Products Missing Images: {count}")

if __name__ == "__main__":
    list_missing_images()
