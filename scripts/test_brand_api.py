"""Test brand API endpoint directly"""
import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.test import RequestFactory
from apps.catalog.views import BrandListView

# Create a fake request
factory = RequestFactory()
request = factory.get('/api/v1/brands/?category=pizza-firini')

# Create view instance
view = BrandListView.as_view()

# Call the view
response = view(request)

print(f"Status Code: {response.status_code}")
print(f"Response Data: {response.data}")
print(f"Data length: {len(response.data) if hasattr(response, 'data') else 'N/A'}")
