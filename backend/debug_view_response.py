
import os
import sys
import django
from django.test import RequestFactory

# Add backend to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
try:
    django.setup()
except Exception as e:
    print(f"Setup failed: {e}")
    sys.exit(1)

from apps.catalog.views import SeriesListView
from apps.catalog.models import Category, Brand

def check_api_response():
    factory = RequestFactory()
    
    # Simulate: GET /api/v1/series/?category=firinlar&brand=rational
    path = "/api/v1/series/"
    params = {
        "category": "firinlar",
        "brand": "rational"
    }
    request = factory.get(path, data=params)
    
    view = SeriesListView.as_view()
    response = view(request)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.data
        print(f"Total Series Returned: {len(data)}")
        for item in data:
            print("-" * 40)
            print(f"Name: {item.get('name')}")
            print(f"Slug: {item.get('slug')}")
            print(f"Products Count: {item.get('products_count')}")
            print(f"Is Visible: {item.get('is_visible')}")
            print(f"Single Product Slug: {item.get('single_product_slug')}")
            
            # Additional debug for raw fields if needed
            # print(f"Raw Entry: {item}")
            
    else:
        print("Error response")

if __name__ == "__main__":
    check_api_response()
