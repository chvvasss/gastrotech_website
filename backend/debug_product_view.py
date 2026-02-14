
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

from apps.catalog.views import ProductListView

def check_product_api():
    factory = RequestFactory()
    
    # Simulate: GET /api/v1/products/?category=firinlar&brand=rational&series=i-combi-classic-serisi
    path = "/api/v1/products/"
    params = {
        "category": "firinlar",
        "brand": "rational",
        "series": "i-combi-classic-serisi"
    }
    request = factory.get(path, data=params)
    
    view = ProductListView.as_view()
    response = view(request)
    
    print(f"Status Code: {response.status_code}")
    
    if hasattr(response, 'data'):
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
            print(f"Total Products Returned: {len(results)}")
            if len(results) > 0:
                print(f"First Product: {results[0].get('slug')}")
                # Print keys to compare with Schema
                print(f"Keys: {list(results[0].keys())}")
        else:
             print(f"Unexpected data format: {type(data)}")

if __name__ == "__main__":
    check_product_api()
