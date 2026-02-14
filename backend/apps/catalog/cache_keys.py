"""
Cache key functions for catalog views.

Provides consistent cache key generation for all cached endpoints.
"""

# Cache TTL constants (in seconds)
NAV_CACHE_TTL = 300  # 5 minutes
TREE_CACHE_TTL = 300  # 5 minutes
SPEC_KEYS_CACHE_TTL = 300  # 5 minutes


def nav_key() -> str:
    """Cache key for navigation (categories with series)."""
    return "catalog:nav:v1"


def categories_tree_key() -> str:
    """Cache key for categories tree."""
    return "catalog:categories_tree:v1"


def series_tree_key(category_slug: str) -> str:
    """Cache key for series list by category."""
    return f"catalog:series_tree:{category_slug}:v1"


def taxonomy_tree_key(series_slug: str) -> str:
    """Cache key for taxonomy tree by series."""
    return f"catalog:taxonomy_tree:{series_slug}:v1"


def spec_keys_key() -> str:
    """Cache key for spec keys list."""
    return "catalog:spec_keys:v1"


def clear_nav_cache():
    """Clear navigation-related caches."""
    from django.core.cache import cache
    cache.delete(nav_key())
    cache.delete(categories_tree_key())


def clear_taxonomy_cache(series_slug: str = None):
    """Clear taxonomy tree cache for a specific series or all."""
    from django.core.cache import cache
    if series_slug:
        cache.delete(taxonomy_tree_key(series_slug))
    # Also clear nav as taxonomy changes may affect navigation
    cache.delete(nav_key())


def clear_spec_keys_cache():
    """Clear spec keys cache."""
    from django.core.cache import cache
    cache.delete(spec_keys_key())


def clear_all_catalog_cache():
    """Clear all catalog-related caches."""
    from django.core.cache import cache
    # Clear known keys
    cache.delete(nav_key())
    cache.delete(categories_tree_key())
    cache.delete(spec_keys_key())
    # Note: Taxonomy keys are per-series, so we can't easily clear all of them
    # without knowing all series slugs. This is handled in signals.
