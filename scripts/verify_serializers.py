import os
import django
from django.conf import settings

import sys
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.catalog.serializers import SeriesWithCountsSerializer, NavSeriesSerializer
from apps.catalog.models import Series, Product, Category

def test_serializers():
    print("Testing Serializers...")
    
    # Check fields in SeriesWithCountsSerializer
    s_fields = SeriesWithCountsSerializer().get_fields().keys()
    print(f"SeriesWithCountsSerializer fields: {list(s_fields)}")
    assert 'single_product_name' in s_fields
    assert 'single_product_image_url' in s_fields
    
    # Check fields in NavSeriesSerializer
    n_fields = NavSeriesSerializer().get_fields().keys()
    print(f"NavSeriesSerializer fields: {list(n_fields)}")
    assert 'single_product_name' in n_fields
    assert 'single_product_image_url' in n_fields

    print("SUCCESS: Serializers have the required fields.")

if __name__ == "__main__":
    test_serializers()
