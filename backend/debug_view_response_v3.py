
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

def check_all_series():
    factory = RequestFactory()
    
    path = "/api/v1/series/"
    params = {
        "category": "firinlar",
        "brand": "rational"
    }
    request = factory.get(path, data=params)
    
    view = SeriesListView.as_view()
    response = view(request)
    
    if hasattr(response, 'data'):
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
            print(f"Total Results: {len(results)}")
            for s in results:
                print(f"Slug: {s.get('slug'):<30} | Products: {s.get('products_count')} | Visible: {s.get('is_visible')} | Single: {s.get('single_product_slug')}")
        else:
            print("Layout unexpected")

if __name__ == "__main__":
    check_all_series()
