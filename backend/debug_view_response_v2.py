
import os
import sys
import json
import django
from django.test import RequestFactory
from rest_framework.response import Response

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

def check_api_response():
    factory = RequestFactory()
    
    path = "/api/v1/series/"
    params = {
        "category": "firinlar",
        "brand": "rational"
    }
    request = factory.get(path, data=params)
    
    view = SeriesListView.as_view()
    response = view(request)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Type: {type(response)}")
    
    if hasattr(response, 'data'):
        data = response.data
        print(f"Data Type: {type(data)}")
        
        # If it's a list, look at first item
        if isinstance(data, list):
            print(f"Data Length: {len(data)}")
            if len(data) > 0:
                print(f"First Item Type: {type(data[0])}")
                print(f"First Item: {data[0]}")
        elif isinstance(data, dict):
             # Pagination results often wrapped in 'results'
             print(f"Data Keys: {data.keys()}")
             if 'results' in data:
                 results = data['results']
                 print(f"Results Length: {len(results)}")
                 if len(results) > 0:
                     print(f"First Result Type: {type(results[0])}")
                     print(f"First Result: {results[0]}")
                     # Work with results
                     data = results 
        else:
             print(f"Data Raw: {data}")

    else:
        print("Response object has no .data attribute. Is it a Django HttpResponse?")
        print(f"Content Start: {response.content[:100]}")

if __name__ == "__main__":
    check_api_response()
