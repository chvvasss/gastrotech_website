
import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.common.models import SiteSetting
from apps.common.utils import get_show_prices, invalidate_show_prices_cache
from apps.catalog.serializers import VariantSerializer
from apps.catalog.models import Variant, Product
from django.core.cache import cache

def test_toggle():
    print("--- Starting Price Toggle Verification ---")
    
    # 1. Reset state
    SiteSetting.objects.filter(key="show_prices").delete()
    invalidate_show_prices_cache()
    
    # 2. Check Default (Should be True)
    print(f"Default get_show_prices(): {get_show_prices()}")
    assert get_show_prices() == True, "Default should be True"
    
    # 3. Create Variant for testing
    # Find existing or mock
    variant = Variant.objects.first()
    if not variant:
        print("No variant found to test serializer. Skipping serializer test.")
    else:
        print(f"Testing with variant: {variant.model_code}")
        
    # 4. Test Serializer with Show Prices = True
    if variant:
        data = VariantSerializer(variant).data
        print(f"Show Prices=True, Price in data: {'list_price' in data}")
        assert 'list_price' in data, "Price should be present when show_prices=True"
        
    # 5. Toggle OFF
    print("Toggling OFF...")
    setting, _ = SiteSetting.objects.get_or_create(key="show_prices")
    setting.value = {"value": False}
    setting.save()
    invalidate_show_prices_cache()
    
    print(f"OFF get_show_prices(): {get_show_prices()}")
    assert get_show_prices() == False, "Should be False after toggle"
    
    # 6. Test Serializer with Show Prices = False
    if variant:
        data = VariantSerializer(variant).data
        print(f"Show Prices=False, Price in data: {'list_price' in data}")
        assert 'list_price' not in data, "Price should NOT be present when show_prices=False"
        
    # 7. Toggle ON
    print("Toggling ON...")
    setting.value = {"value": True}
    setting.save()
    invalidate_show_prices_cache()
    
    print(f"ON get_show_prices(): {get_show_prices()}")
    assert get_show_prices() == True, "Should be True after toggle ON"
    
    print("--- Verification PASSED ---")

if __name__ == "__main__":
    try:
        test_toggle()
    except AssertionError as e:
        print(f"FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
