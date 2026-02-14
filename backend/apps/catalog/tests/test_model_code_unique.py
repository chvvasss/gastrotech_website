"""
Tests for Variant.model_code uniqueness constraint.
"""

from django.db import IntegrityError
from django.test import TestCase

from apps.catalog.models import Category, Product, Series, Variant


class VariantModelCodeUniqueTest(TestCase):
    """Test that Variant.model_code is globally unique."""
    
    def setUp(self):
        """Create test data."""
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.series = Series.objects.create(
            category=self.category,
            name="Test Series",
            slug="test-series",
        )
        self.product1 = Product.objects.create(
            name="Product One",
            slug="product-one",
            title_tr="Ürün Bir",
            series=self.series,
        )
        self.product2 = Product.objects.create(
            name="Product Two",
            slug="product-two",
            title_tr="Ürün İki",
            series=self.series,
        )
    
    def test_model_code_unique(self):
        """Model codes must be globally unique."""
        Variant.objects.create(
            product=self.product1,
            model_code="GKO6010",
            name_tr="Test Variant 1",
        )
        
        # Same model_code on different product should fail
        with self.assertRaises(IntegrityError):
            Variant.objects.create(
                product=self.product2,
                model_code="GKO6010",
                name_tr="Test Variant 2",
            )
    
    def test_different_model_codes_allowed(self):
        """Different model codes should be allowed."""
        v1 = Variant.objects.create(
            product=self.product1,
            model_code="GKO6010",
            name_tr="Gazlı Ocak 2 Gözlü",
        )
        v2 = Variant.objects.create(
            product=self.product1,
            model_code="GKO6020",
            name_tr="Gazlı Ocak 4 Gözlü",
        )
        v3 = Variant.objects.create(
            product=self.product2,
            model_code="GKW6010",
            name_tr="Wok Ocağı Tek Gözlü",
        )
        
        self.assertEqual(Variant.objects.count(), 3)
        self.assertNotEqual(v1.model_code, v2.model_code)
        self.assertNotEqual(v2.model_code, v3.model_code)
    
    def test_variant_specs_json(self):
        """Test that specs JSON field works correctly."""
        variant = Variant.objects.create(
            product=self.product1,
            model_code="GKO6010",
            name_tr="Gazlı Ocak 2 Gözlü",
            specs={
                "goz-adedi": 2,
                "guc-kw": "8.0",
                "gaz-baglantisi": "1/2\"",
            },
        )
        
        # Reload from database
        variant.refresh_from_db()
        
        self.assertEqual(variant.specs["goz-adedi"], 2)
        self.assertEqual(variant.specs["guc-kw"], "8.0")
        self.assertEqual(variant.get_spec_value("goz-adedi"), 2)
        self.assertIsNone(variant.get_spec_value("nonexistent"))
    
    def test_variant_display_price(self):
        """Test get_display_price method."""
        from decimal import Decimal
        
        # Only list_price
        v1 = Variant.objects.create(
            product=self.product1,
            model_code="TEST001",
            name_tr="Test 1",
            list_price=Decimal("100.00"),
        )
        self.assertEqual(v1.get_display_price(), Decimal("100.00"))
        
        # Override takes precedence
        v2 = Variant.objects.create(
            product=self.product1,
            model_code="TEST002",
            name_tr="Test 2",
            list_price=Decimal("100.00"),
            price_override=Decimal("80.00"),
        )
        self.assertEqual(v2.get_display_price(), Decimal("80.00"))
        
        # No price
        v3 = Variant.objects.create(
            product=self.product1,
            model_code="TEST003",
            name_tr="Test 3",
        )
        self.assertIsNone(v3.get_display_price())
