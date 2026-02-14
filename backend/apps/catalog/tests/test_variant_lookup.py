"""
Tests for variant lookup by codes endpoint.
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, Series, Variant


class VariantByCodesTest(TestCase):
    """Test GET /api/v1/variants/by-codes endpoint."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        
        # Create hierarchy
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.series = Series.objects.create(
            category=self.category,
            name="600 Serisi",
            slug="600",
        )
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            title_tr="Test Ürün",
            series=self.series,
        )
        
        # Create variants
        self.variant1 = Variant.objects.create(
            product=self.product,
            model_code="CODE001",
            name_tr="Variant 1",
            name_en="Variant One",
            dimensions="400x600x280",
            weight_kg=32.0,
            list_price=4500.00,
            specs={"goz-adedi": 2, "guc-kw": "8.0"},
        )
        self.variant2 = Variant.objects.create(
            product=self.product,
            model_code="CODE002",
            name_tr="Variant 2",
            dimensions="800x600x280",
        )
        self.variant3 = Variant.objects.create(
            product=self.product,
            model_code="CODE003",
            name_tr="Variant 3",
        )
    
    def test_lookup_returns_variants_in_input_order(self):
        """Test that variants are returned in the same order as input codes."""
        url = "/api/v1/variants/by-codes/?codes=CODE003,CODE001,CODE002"
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Check order matches input
        self.assertEqual(response.data[0]["model_code"], "CODE003")
        self.assertEqual(response.data[1]["model_code"], "CODE001")
        self.assertEqual(response.data[2]["model_code"], "CODE002")
    
    def test_lookup_includes_not_found_entries(self):
        """Test that unknown codes return error entries."""
        url = "/api/v1/variants/by-codes/?codes=CODE001,UNKNOWN,CODE002"
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # First and third should be valid
        self.assertIsNone(response.data[0]["error"])
        self.assertIsNone(response.data[2]["error"])
        
        # Second should have error
        self.assertEqual(response.data[1]["model_code"], "UNKNOWN")
        self.assertEqual(response.data[1]["error"], "not_found")
        self.assertIsNone(response.data[1]["name_tr"])
    
    def test_lookup_returns_full_hierarchy_info(self):
        """Test that response includes full hierarchy information."""
        url = "/api/v1/variants/by-codes/?codes=CODE001"
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        item = response.data[0]
        self.assertEqual(item["model_code"], "CODE001")
        self.assertEqual(item["name_tr"], "Variant 1")
        self.assertEqual(item["name_en"], "Variant One")
        self.assertEqual(item["product_slug"], "test-product")
        self.assertEqual(item["product_title_tr"], "Test Ürün")
        self.assertEqual(item["series_slug"], "600")
        self.assertEqual(item["series_name"], "600 Serisi")
        self.assertEqual(item["category_slug"], "test-category")
        self.assertEqual(item["category_name"], "Test Category")
        self.assertEqual(item["dimensions"], "400x600x280")
        self.assertEqual(float(item["weight_kg"]), 32.0)
        self.assertEqual(float(item["list_price"]), 4500.00)
        self.assertEqual(item["specs"], {"goz-adedi": 2, "guc-kw": "8.0"})
    
    def test_lookup_deduplicates_codes(self):
        """Test that duplicate codes are deduplicated."""
        url = "/api/v1/variants/by-codes/?codes=CODE001,CODE001,CODE001"
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["model_code"], "CODE001")
    
    def test_lookup_limits_to_50_codes(self):
        """Test that codes are limited to 50."""
        codes = ",".join([f"CODE{i:03d}" for i in range(100)])
        url = f"/api/v1/variants/by-codes/?codes={codes}"
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 50)
    
    def test_lookup_requires_codes_param(self):
        """Test that codes parameter is required."""
        url = "/api/v1/variants/by-codes/"
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
    
    def test_lookup_handles_empty_codes(self):
        """Test empty codes parameter returns error."""
        url = "/api/v1/variants/by-codes/?codes="
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_lookup_trims_whitespace(self):
        """Test that whitespace is trimmed from codes."""
        url = "/api/v1/variants/by-codes/?codes= CODE001 , CODE002 "
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["model_code"], "CODE001")
        self.assertEqual(response.data[1]["model_code"], "CODE002")
