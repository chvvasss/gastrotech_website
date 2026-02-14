"""
Tests for inquiries app.
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, Series, Variant
from .models import Inquiry, InquiryItem


class InquiryCreationTest(TestCase):
    """Test inquiry creation via API."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        
        # Clear rate limit cache for testing
        from django.core.cache import cache
        cache.clear()
        
        # Create product and variant for testing
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.series = Series.objects.create(
            category=self.category,
            name="Test Series",
            slug="test-series",
        )
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            title_tr="Test Ürün",
            series=self.series,
            status=Product.Status.ACTIVE,
        )
        self.variant = Variant.objects.create(
            product=self.product,
            model_code="GKO6010",
            name_tr="Test Variant",
        )
    
    def test_inquiry_creation_basic(self):
        """Test basic inquiry creation."""
        url = "/api/v1/inquiries"
        data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "+90 555 123 4567",
            "company": "Test Company",
            "message": "I want to order 5 units.",
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["status"], "received")
        
        # Check inquiry was created
        inquiry = Inquiry.objects.get(id=response.data["id"])
        self.assertEqual(inquiry.full_name, "Test User")
        self.assertEqual(inquiry.email, "test@example.com")
        self.assertEqual(inquiry.company, "Test Company")
        self.assertEqual(inquiry.status, Inquiry.Status.NEW)
    
    def test_inquiry_with_product_slug(self):
        """Test inquiry with product reference."""
        url = "/api/v1/inquiries"
        data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "product_slug": "test-product",
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        inquiry = Inquiry.objects.get(id=response.data["id"])
        self.assertEqual(inquiry.product, self.product)
        self.assertEqual(inquiry.product_slug_snapshot, "test-product")
    
    def test_inquiry_with_model_code(self):
        """Test inquiry with variant reference."""
        url = "/api/v1/inquiries"
        data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "model_code": "GKO6010",
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        inquiry = Inquiry.objects.get(id=response.data["id"])
        self.assertEqual(inquiry.variant, self.variant)
        self.assertEqual(inquiry.model_code_snapshot, "GKO6010")
        # Product should also be set from variant
        self.assertEqual(inquiry.product, self.product)
    
    def test_inquiry_with_nonexistent_product(self):
        """Test inquiry with non-existent product slug still works."""
        url = "/api/v1/inquiries"
        data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "product_slug": "nonexistent-product",
            "model_code": "FAKE123",
        }
        
        response = self.client.post(url, data, format="json")
        
        # Should still create inquiry with snapshot values
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        inquiry = Inquiry.objects.get(id=response.data["id"])
        self.assertIsNone(inquiry.product)
        self.assertIsNone(inquiry.variant)
        self.assertEqual(inquiry.product_slug_snapshot, "nonexistent-product")
        self.assertEqual(inquiry.model_code_snapshot, "FAKE123")
    
    def test_honeypot_rejects_spam(self):
        """Test that honeypot field blocks spam submissions."""
        url = "/api/v1/inquiries"
        data = {
            "full_name": "Spam Bot",
            "email": "spam@example.com",
            "website": "http://spam-site.com",  # Honeypot filled = spam
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("website", response.data)
    
    def test_honeypot_allows_empty(self):
        """Test that empty honeypot field allows submission."""
        url = "/api/v1/inquiries"
        data = {
            "full_name": "Real User",
            "email": "real@example.com",
            "website": "",  # Empty honeypot is OK
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_inquiry_validation_errors(self):
        """Test inquiry validation."""
        url = "/api/v1/inquiries"
        
        # Missing required fields
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("full_name", response.data)
        self.assertIn("email", response.data)
        
        # Invalid email
        data = {
            "full_name": "Test User",
            "email": "not-an-email",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
    
    def test_inquiry_with_utm_params(self):
        """Test inquiry with UTM tracking parameters."""
        url = "/api/v1/inquiries"
        data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "source_url": "https://gastrotech.com/products/test-product",
            "utm_source": "google",
            "utm_medium": "cpc",
            "utm_campaign": "summer-sale",
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        inquiry = Inquiry.objects.get(id=response.data["id"])
        self.assertEqual(inquiry.source_url, "https://gastrotech.com/products/test-product")
        self.assertEqual(inquiry.utm_source, "google")
        self.assertEqual(inquiry.utm_medium, "cpc")
        self.assertEqual(inquiry.utm_campaign, "summer-sale")


class MultiItemInquiryTest(TestCase):
    """Test multi-item quote request functionality."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        
        # Clear rate limit cache for testing
        from django.core.cache import cache
        cache.clear()
        
        # Create product and variants
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.series = Series.objects.create(
            category=self.category,
            name="Test Series",
            slug="test-series",
        )
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            title_tr="Test Ürün",
            series=self.series,
            status=Product.Status.ACTIVE,
        )
        
        # Create multiple variants
        self.variant1 = Variant.objects.create(
            product=self.product,
            model_code="TEST001",
            name_tr="Test Variant 1",
        )
        self.variant2 = Variant.objects.create(
            product=self.product,
            model_code="TEST002",
            name_tr="Test Variant 2",
        )
        self.variant3 = Variant.objects.create(
            product=self.product,
            model_code="TEST003",
            name_tr="Test Variant 3",
        )
    
    def test_multi_item_inquiry_creates_inquiry_items(self):
        """Test that multi-item inquiry creates InquiryItem records."""
        url = "/api/v1/inquiries"
        data = {
            "full_name": "Multi Item User",
            "email": "multi@example.com",
            "company": "Big Hotel",
            "message": "Need quote for kitchen upgrade",
            "items": [
                {"model_code": "TEST001", "qty": 2},
                {"model_code": "TEST002", "qty": 1},
                {"model_code": "TEST003", "qty": 5},
            ],
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["items_count"], 3)
        
        # Verify inquiry was created
        inquiry = Inquiry.objects.get(id=response.data["id"])
        self.assertEqual(inquiry.full_name, "Multi Item User")
        self.assertEqual(inquiry.items.count(), 3)
        
        # Verify each InquiryItem
        items = inquiry.items.all()
        model_codes = [item.model_code_snapshot for item in items]
        self.assertIn("TEST001", model_codes)
        self.assertIn("TEST002", model_codes)
        self.assertIn("TEST003", model_codes)
        
        # Verify quantities
        item1 = inquiry.items.get(model_code_snapshot="TEST001")
        self.assertEqual(item1.qty, 2)
        self.assertEqual(item1.variant, self.variant1)
        
        item3 = inquiry.items.get(model_code_snapshot="TEST003")
        self.assertEqual(item3.qty, 5)
    
    def test_multi_item_with_invalid_model_code_stores_snapshot(self):
        """Test that invalid model codes are stored as snapshots."""
        url = "/api/v1/inquiries"
        data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "items": [
                {"model_code": "TEST001", "qty": 1},
                {"model_code": "INVALID123", "qty": 3},
            ],
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["items_count"], 2)
        
        inquiry = Inquiry.objects.get(id=response.data["id"])
        
        # Valid variant should be linked
        item1 = inquiry.items.get(model_code_snapshot="TEST001")
        self.assertEqual(item1.variant, self.variant1)
        
        # Invalid variant should have snapshot but no link
        item2 = inquiry.items.get(model_code_snapshot="INVALID123")
        self.assertIsNone(item2.variant)
        self.assertEqual(item2.qty, 3)
    
    def test_inquiry_items_snapshot_product_info(self):
        """Test that InquiryItem snapshots product information."""
        url = "/api/v1/inquiries"
        data = {
            "full_name": "Snapshot Test",
            "email": "snapshot@example.com",
            "items": [
                {"model_code": "TEST001", "qty": 1},
            ],
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        inquiry = Inquiry.objects.get(id=response.data["id"])
        item = inquiry.items.first()
        
        # Check snapshots
        self.assertEqual(item.model_code_snapshot, "TEST001")
        self.assertEqual(item.model_name_tr_snapshot, "Test Variant 1")
        self.assertEqual(item.product_slug_snapshot, "test-product")
        self.assertEqual(item.product_title_tr_snapshot, "Test Ürün")
        self.assertEqual(item.series_slug_snapshot, "test-series")
    
    def test_inquiry_items_summary_property(self):
        """Test inquiry items_summary property."""
        url = "/api/v1/inquiries"
        data = {
            "full_name": "Summary Test",
            "email": "summary@example.com",
            "items": [
                {"model_code": "TEST001", "qty": 1},
                {"model_code": "TEST002", "qty": 1},
                {"model_code": "TEST003", "qty": 1},
            ],
        }
        
        response = self.client.post(url, data, format="json")
        inquiry = Inquiry.objects.get(id=response.data["id"])
        
        # Summary should show first 3 codes
        summary = inquiry.items_summary
        self.assertIn("TEST001", summary)
        self.assertIn("TEST002", summary)
        self.assertIn("TEST003", summary)


class QuoteValidationTest(TestCase):
    """Test quote validation endpoint."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.series = Series.objects.create(
            category=self.category,
            name="Test Series",
            slug="test-series",
        )
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            title_tr="Test Ürün",
            series=self.series,
        )
        self.variant = Variant.objects.create(
            product=self.product,
            model_code="VALID001",
            name_tr="Valid Variant",
        )
    
    def test_quote_validate_valid_items(self):
        """Test validation returns correct data for valid items."""
        url = "/api/v1/quote/validate"
        data = {
            "items": [
                {"model_code": "VALID001", "qty": 2},
            ],
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        item = response.data[0]
        self.assertTrue(item["valid"])
        self.assertEqual(item["model_code"], "VALID001")
        self.assertEqual(item["qty"], 2)
        self.assertEqual(item["model_name_tr"], "Valid Variant")
        self.assertEqual(item["product_title_tr"], "Test Ürün")
        self.assertIsNone(item["error"])
    
    def test_quote_validate_invalid_items(self):
        """Test validation returns errors for invalid items."""
        url = "/api/v1/quote/validate"
        data = {
            "items": [
                {"model_code": "INVALID999", "qty": 1},
            ],
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        item = response.data[0]
        self.assertFalse(item["valid"])
        self.assertEqual(item["model_code"], "INVALID999")
        self.assertIsNone(item["model_name_tr"])
        self.assertIn("not found", item["error"])
    
    def test_quote_validate_mixed_items(self):
        """Test validation handles mix of valid and invalid items."""
        url = "/api/v1/quote/validate"
        data = {
            "items": [
                {"model_code": "VALID001", "qty": 1},
                {"model_code": "INVALID999", "qty": 2},
            ],
        }
        
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # First should be valid
        self.assertTrue(response.data[0]["valid"])
        # Second should be invalid
        self.assertFalse(response.data[1]["valid"])
