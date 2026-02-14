
import os
import sys
import django
from django.conf import settings
from django.test import RequestFactory, override_settings

# Add backend to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
try:
    django.setup()
except Exception as e:
    print(f"Setup failed: {e}")
    sys.exit(1)

from apps.catalog.models import Category, Product
from apps.catalog.views import ProductListView

@override_settings(ALLOWED_HOSTS=['testserver', '127.0.0.1', 'localhost'])
def test_recursive_filtering():
    # 1. Check Hierarchy
    try:
        firinlar = Category.objects.get(slug='firinlar')
        print(f"Category 'firinlar' found. Parent: {firinlar.parent}")
        if firinlar.parent:
            parent_slug = firinlar.parent.slug
            print(f"Parent Slug: {parent_slug}")
            
            # 2. Test Filtering by Parent
            print(f"\nTesting ProductListView with category='{parent_slug}'...")
            
            factory = RequestFactory()
            path = "/api/v1/products/"
            params = {
                "category": parent_slug,
                "status": "active"
            }
            request = factory.get(path, data=params)
            
            view = ProductListView.as_view()
            response = view(request)
            
            print(f"Status Code: {response.status_code}")
            if hasattr(response, 'data') and 'results' in response.data:
                count = len(response.data['results'])
                print(f"Products Found via Parent: {count}")
                if count > 0:
                    print("SUCCESS: Recursive filtering is working.")
                else:
                    print("FAILURE: No products returned for parent category.")
            else:
                 print("Error parsing response data.")
                 
        else:
            print("Category 'firinlar' has no parent. Cannot test recursive filtering.")

    except Category.DoesNotExist:
        print("Category 'firinlar' not found.")

if __name__ == "__main__":
    test_recursive_filtering()
