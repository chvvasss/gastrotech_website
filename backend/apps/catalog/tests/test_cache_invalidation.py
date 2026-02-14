"""
Tests for cache invalidation.
"""

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.cache_keys import nav_key, categories_tree_key
from apps.catalog.models import Category, Series


class CacheInvalidationTest(TestCase):
    """Test cache invalidation on model changes."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Clear cache before each test
        cache.clear()
        
        # Create initial category
        self.category = Category.objects.create(
            name="Initial Category",
            slug="initial-category",
            order=1,
        )
    
    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()
    
    def test_nav_cache_invalidation_on_series_create(self):
        """Test that nav cache is invalidated when a series is created."""
        # First request - should cache the response
        response1 = self.client.get("/api/v1/nav/")
        self.assertEqual(response1.status_code, 200)
        
        # Check cache is set
        cached_data = cache.get(nav_key())
        self.assertIsNotNone(cached_data)
        
        # Verify no series in response
        data1 = response1.json()
        self.assertEqual(len(data1), 1)
        self.assertEqual(len(data1[0]["series"]), 0)
        
        # Create a new series
        Series.objects.create(
            category=self.category,
            name="New Series",
            slug="new-series",
            order=1,
        )
        
        # Cache should be invalidated by signal
        cached_after = cache.get(nav_key())
        self.assertIsNone(cached_after)
        
        # Second request should show new data
        response2 = self.client.get("/api/v1/nav/")
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        
        # Now category should have the new series
        self.assertEqual(len(data2), 1)
        self.assertEqual(len(data2[0]["series"]), 1)
        self.assertEqual(data2[0]["series"][0]["name"], "New Series")
    
    def test_nav_cache_invalidation_on_category_update(self):
        """Test that nav cache is invalidated when a category is updated."""
        # First request - should cache
        response1 = self.client.get("/api/v1/nav/")
        self.assertEqual(response1.status_code, 200)
        
        # Verify cache is set
        self.assertIsNotNone(cache.get(nav_key()))
        
        # Update category
        self.category.name = "Updated Category"
        self.category.save()
        
        # Cache should be invalidated
        self.assertIsNone(cache.get(nav_key()))
        
        # Second request should show updated data
        response2 = self.client.get("/api/v1/nav/")
        data2 = response2.json()
        self.assertEqual(data2[0]["name"], "Updated Category")
    
    def test_category_tree_cache_invalidation(self):
        """Test that category tree cache is invalidated on category change."""
        # First request
        response1 = self.client.get("/api/v1/categories/tree/")
        self.assertEqual(response1.status_code, 200)
        
        # Verify cache is set
        self.assertIsNotNone(cache.get(categories_tree_key()))
        
        # Create new category
        Category.objects.create(
            name="Second Category",
            slug="second-category",
            order=2,
        )
        
        # Cache should be invalidated
        self.assertIsNone(cache.get(categories_tree_key()))
        
        # Second request should show new category
        response2 = self.client.get("/api/v1/categories/tree/")
        data2 = response2.json()
        self.assertEqual(len(data2), 2)
