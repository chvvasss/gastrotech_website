
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.catalog.models import Category, Brand, BrandCategory, Product, Series

class BrandVisibilityTests(APITestCase):
    def setUp(self):
        # Create Category
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category"
        )
        
        # Create Brand
        self.brand = Brand.objects.create(
            name="Test Brand",
            slug="test-brand",
            is_active=True
        )
        
    def test_brand_explicitly_assigned_is_visible_without_products(self):
        """
        Ensure a brand assigned to a category is visible in the API 
        even if it has no products.
        """
        # Assign Brand to Category
        BrandCategory.objects.create(
            brand=self.brand,
            category=self.category,
            is_active=True
        )
        
        # Call API
        url = '/api/v1/brands/'
        response = self.client.get(url, {'category': self.category.slug})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if brand is in response
        brand_slugs = [b['slug'] for b in response.data]
        self.assertIn(self.brand.slug, brand_slugs)
        
    def test_brand_not_assigned_is_not_visible(self):
        """
        Ensure a brand NOT assigned to a category is NOT visible.
        """
        # Call API without assignment
        # Call API without assignment
        url = '/api/v1/brands/'
        response = self.client.get(url, {'category': self.category.slug})
        response = self.client.get(url, {'category': self.category.slug})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if brand is NOT in response
        brand_slugs = [b['slug'] for b in response.data]
        self.assertNotIn(self.brand.slug, brand_slugs)
