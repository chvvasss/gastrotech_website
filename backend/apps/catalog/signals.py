"""
Django signals for catalog cache invalidation.

Automatically clears relevant caches when models are saved or deleted.
"""

import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .cache_keys import (
    clear_nav_cache,
    clear_taxonomy_cache,
    clear_spec_keys_cache,
)

logger = logging.getLogger(__name__)


def is_app_ready():
    """Check if the app is ready (not during migrations)."""
    try:
        from django.apps import apps
        return apps.ready
    except Exception:
        return False


@receiver(post_save, sender="catalog.Category")
@receiver(post_delete, sender="catalog.Category")
def invalidate_category_cache(sender, instance, **kwargs):
    """Clear nav and category tree caches when Category changes."""
    if not is_app_ready():
        return
    
    try:
        clear_nav_cache()
        logger.debug(f"Cleared nav cache after Category {instance.slug} change")
    except Exception as e:
        logger.warning(f"Failed to clear cache after Category change: {e}")


@receiver(post_save, sender="catalog.Series")
@receiver(post_delete, sender="catalog.Series")
def invalidate_series_cache(sender, instance, **kwargs):
    """Clear nav cache when Series changes."""
    if not is_app_ready():
        return
    
    try:
        clear_nav_cache()
        logger.debug(f"Cleared nav cache after Series {instance.slug} change")
    except Exception as e:
        logger.warning(f"Failed to clear cache after Series change: {e}")


@receiver(post_save, sender="catalog.TaxonomyNode")
@receiver(post_delete, sender="catalog.TaxonomyNode")
def invalidate_taxonomy_cache(sender, instance, **kwargs):
    """Clear taxonomy tree cache when TaxonomyNode changes."""
    if not is_app_ready():
        return
    
    try:
        # Get series slug
        series_slug = instance.series.slug if instance.series else None
        if series_slug:
            clear_taxonomy_cache(series_slug)
            logger.debug(f"Cleared taxonomy cache for series {series_slug}")
    except Exception as e:
        logger.warning(f"Failed to clear cache after TaxonomyNode change: {e}")


@receiver(post_save, sender="catalog.SpecKey")
@receiver(post_delete, sender="catalog.SpecKey")
def invalidate_spec_keys_cache(sender, instance, **kwargs):
    """Clear spec keys cache when SpecKey changes."""
    if not is_app_ready():
        return
    
    try:
        clear_spec_keys_cache()
        logger.debug(f"Cleared spec keys cache after SpecKey {instance.slug} change")
    except Exception as e:
        logger.warning(f"Failed to clear cache after SpecKey change: {e}")


@receiver(post_save, sender="catalog.Product")
@receiver(post_delete, sender="catalog.Product")
def invalidate_product_cache(sender, instance, **kwargs):
    """Optionally clear nav cache when Product changes (for counts, etc.)."""
    if not is_app_ready():
        return
    
    # Products list is not cached, but nav might show product counts
    # Clear nav cache for consistency
    try:
        clear_nav_cache()
    except Exception as e:
        logger.warning(f"Failed to clear cache after Product change: {e}")
