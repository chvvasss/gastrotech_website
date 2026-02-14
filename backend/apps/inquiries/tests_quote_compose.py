"""
Tests for quote compose endpoint.
"""

from django.core.cache import cache
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, Series, SpecKey, Variant


class QuoteComposeTest(TestCase):
    """Test POST /api/v1/quote/compose endpoint."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        
        # Clear rate limit cache
        cache.clear()
        
        # Create hierarchy
        self.category = Category.objects.create(
            name="Pişirme Üniteleri",
            slug="pisirme-uniteleri",
        )
        self.series = Series.objects.create(
            category=self.category,
            name="600 Serisi",
            slug="600",
        )
        self.product = Product.objects.create(
            name="600 Serisi Gazlı Ocaklar",
            slug="600-serisi-gazli-ocaklar",
            title_tr="Gazlı Ocaklar",
            series=self.series,
            spec_layout=["goz-adedi", "guc-kw"],
        )
        
        # Create spec keys
        self.spec_key1 = SpecKey.objects.create(
            slug="goz-adedi",
            label_tr="Göz Adedi",
            sort_order=1,
        )
        self.spec_key2 = SpecKey.objects.create(
            slug="guc-kw",
            label_tr="Güç",
            unit="kW",
            sort_order=2,
        )
        
        # Create variants
        self.variant1 = Variant.objects.create(
            product=self.product,
            model_code="GKO6010",
            name_tr="Gazlı Ocak 2 Gözlü",
            dimensions="400x600x280",
            specs={"goz-adedi": 2, "guc-kw": "8.0"},
        )
        self.variant2 = Variant.objects.create(
            product=self.product,
            model_code="GKO6030",
            name_tr="Gazlı Ocak 6 Gözlü",
            dimensions="1200x600x280",
            specs={"goz-adedi": 6, "guc-kw": "24.0"},
        )
    
    def test_compose_returns_message_with_model_codes_and_qty(self):
        """Test that message_tr contains each model_code and qty."""
        url = "/api/v1/quote/compose"
        data = {
            "items": [
                {"model_code": "GKO6010", "qty": 2},
                {"model_code": "GKO6030", "qty": 3},
            ],
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        message = response.data["message_tr"]
        
        # Check model codes are in message
        self.assertIn("GKO6010", message)
        self.assertIn("GKO6030", message)
        
        # Check quantities are in message
        self.assertIn("2x", message)
        self.assertIn("3x", message)
        
        # Check header
        self.assertIn("Teklif Talebi", message)
    
    def test_compose_includes_customer_info_in_message(self):
        """Test that customer info is included in message."""
        url = "/api/v1/quote/compose"
        data = {
            "full_name": "Ahmet Yılmaz",
            "company": "Grand Hotel",
            "items": [
                {"model_code": "GKO6010", "qty": 1},
            ],
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        message = response.data["message_tr"]
        self.assertIn("Ahmet Yılmaz", message)
        self.assertIn("Grand Hotel", message)
    
    def test_compose_includes_note_in_message(self):
        """Test that note is included in message."""
        url = "/api/v1/quote/compose"
        data = {
            "note": "Kurulum dahil mi?",
            "items": [
                {"model_code": "GKO6010", "qty": 1},
            ],
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        message = response.data["message_tr"]
        self.assertIn("Kurulum dahil mi?", message)
    
    def test_compose_handles_not_found_items(self):
        """Test that not found items are handled and mentioned in message."""
        url = "/api/v1/quote/compose"
        data = {
            "items": [
                {"model_code": "GKO6010", "qty": 1},
                {"model_code": "INVALID123", "qty": 2},
            ],
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check items_resolved
        items = response.data["items_resolved"]
        self.assertEqual(len(items), 2)
        
        # First item should be valid
        self.assertIsNone(items[0]["error"])
        self.assertEqual(items[0]["name_tr"], "Gazlı Ocak 2 Gözlü")
        
        # Second item should have error
        self.assertEqual(items[1]["error"], "not_found")
        
        # Message should mention not found
        message = response.data["message_tr"]
        self.assertIn("INVALID123", message)
        self.assertIn("Bulunamayan", message)
    
    def test_compose_returns_resolved_items_with_full_info(self):
        """Test that resolved items include full hierarchy info."""
        url = "/api/v1/quote/compose"
        data = {
            "items": [
                {"model_code": "GKO6010", "qty": 1},
            ],
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        items = response.data["items_resolved"]
        self.assertEqual(len(items), 1)
        
        item = items[0]
        self.assertEqual(item["model_code"], "GKO6010")
        self.assertEqual(item["qty"], 1)
        self.assertEqual(item["name_tr"], "Gazlı Ocak 2 Gözlü")
        self.assertEqual(item["product_slug"], "600-serisi-gazli-ocaklar")
        self.assertEqual(item["product_title_tr"], "Gazlı Ocaklar")
        self.assertEqual(item["series_slug"], "600")
        self.assertEqual(item["category_slug"], "pisirme-uniteleri")
        self.assertEqual(item["dimensions"], "400x600x280")
    
    def test_compose_includes_spec_row(self):
        """Test that spec_row is included with resolved specs."""
        url = "/api/v1/quote/compose"
        data = {
            "items": [
                {"model_code": "GKO6010", "qty": 1},
            ],
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        item = response.data["items_resolved"][0]
        spec_row = item["spec_row"]
        
        self.assertIsNotNone(spec_row)
        self.assertEqual(len(spec_row), 2)
        
        # Check first spec
        self.assertEqual(spec_row[0]["key"], "goz-adedi")
        self.assertEqual(spec_row[0]["label_tr"], "Göz Adedi")
        self.assertEqual(spec_row[0]["value"], "2")
    
    def test_compose_honeypot_rejects_spam(self):
        """Test that honeypot field rejects spam submissions."""
        url = "/api/v1/quote/compose"
        data = {
            "website": "spam-website.com",  # Honeypot filled
            "items": [
                {"model_code": "GKO6010", "qty": 1},
            ],
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_compose_requires_items(self):
        """Test that items are required."""
        url = "/api/v1/quote/compose"
        data = {
            "full_name": "Test User",
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_compose_requires_at_least_one_item(self):
        """Test that at least one item is required."""
        url = "/api/v1/quote/compose"
        data = {
            "items": [],
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
