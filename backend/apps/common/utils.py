import logging
from django.core.cache import cache
from .models import SiteSetting

logger = logging.getLogger(__name__)

CACHE_KEY_SHOW_PRICES = "site_setting:show_prices"
CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours

def get_show_prices() -> bool:
    """
    Check if prices should be displayed globally.
    
    Strategy:
    1. Check Redis cache.
    2. If miss, fetch from DB 'show_prices' key.
    3. If not in DB, default to True.
    4. Cache the result.
    """
    cached_value = cache.get(CACHE_KEY_SHOW_PRICES)
    if cached_value is not None:
        return cached_value

    try:
        # Fetch from DB
        setting = SiteSetting.objects.filter(key="show_prices").first()
        if setting:
            # Assuming value is stored like {"value": True} or direct boolean if JSONField allows simply true/false logic mapping
            # But standard is usually robust JSON. Let's assume we store simple value in JSON.
            # If value is just boolean boolean in JSON field:
            val = setting.value
            # Handle if it's wrapped or raw
            if isinstance(val, dict) and 'value' in val:
                result = bool(val['value'])
            else:
                result = bool(val)
        else:
            # Default to True if setting doesn't exist
            result = True
            
        cache.set(CACHE_KEY_SHOW_PRICES, result, CACHE_TIMEOUT)
        return result

    except Exception as e:
        logger.error(f"Error fetching show_prices setting: {e}")
        # Fail safe to True (show prices) or False (hide)? 
        # Requirement says "OFF: Public sitede fiyat görünmesin". 
        # But usually failsafe for business is SHOW prices unless explicitly hidden.
        return True

def invalidate_show_prices_cache():
    """Invalidate the show_prices cache key."""
    cache.delete(CACHE_KEY_SHOW_PRICES)


CACHE_KEY_CATALOG_MODE = "site_setting:catalog_mode"


def get_catalog_mode() -> bool:
    """
    Check if catalog mode is enabled globally.

    When ON, public site hides products and shows PDF catalogs per category.
    Default is False (normal product display).
    """
    cached_value = cache.get(CACHE_KEY_CATALOG_MODE)
    if cached_value is not None:
        return cached_value

    try:
        setting = SiteSetting.objects.filter(key="catalog_mode").first()
        if setting:
            val = setting.value
            if isinstance(val, dict) and 'value' in val:
                result = bool(val['value'])
            else:
                result = bool(val)
        else:
            result = False

        cache.set(CACHE_KEY_CATALOG_MODE, result, CACHE_TIMEOUT)
        return result

    except Exception as e:
        logger.error(f"Error fetching catalog_mode setting: {e}")
        return False


def invalidate_catalog_mode_cache():
    """Invalidate the catalog_mode cache key."""
    cache.delete(CACHE_KEY_CATALOG_MODE)
