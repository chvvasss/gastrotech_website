"""
Tests for Product.spec_layout validation.
"""

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.catalog.models import Category, Product, Series, SpecKey


class ProductSpecLayoutValidationTest(TestCase):
    """Test that Product.spec_layout contains valid SpecKey slugs."""
    
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
        
        # Create some spec keys
        self.spec_key1 = SpecKey.objects.create(
            slug="goz-adedi",
            label_tr="Göz Adedi",
            value_type="int",
        )
        self.spec_key2 = SpecKey.objects.create(
            slug="guc-kw",
            label_tr="Güç",
            unit="kW",
            value_type="decimal",
        )
        self.spec_key3 = SpecKey.objects.create(
            slug="boyutlar",
            label_tr="Boyutlar",
            value_type="text",
        )
    
    def test_valid_spec_layout(self):
        """Valid spec_layout with existing SpecKey slugs should pass."""
        product = Product(
            name="Test Product",
            slug="test-product",
            title_tr="Test Ürün",
            series=self.series,
            spec_layout=["goz-adedi", "guc-kw", "boyutlar"],
        )
        
        # Should not raise
        product.clean()
        product.save()
        
        self.assertEqual(product.spec_layout, ["goz-adedi", "guc-kw", "boyutlar"])
    
    def test_invalid_spec_layout(self):
        """Invalid spec_layout with non-existent SpecKey slugs should fail."""
        product = Product(
            name="Test Product",
            slug="test-product-invalid",
            title_tr="Test Ürün",
            series=self.series,
            spec_layout=["goz-adedi", "nonexistent-key", "another-bad-key"],
        )
        
        with self.assertRaises(ValidationError) as context:
            product.clean()
        
        self.assertIn("spec_layout", context.exception.message_dict)
        error_msg = context.exception.message_dict["spec_layout"][0]
        self.assertIn("nonexistent-key", error_msg)
        self.assertIn("another-bad-key", error_msg)
    
    def test_empty_spec_layout(self):
        """Empty spec_layout should be valid."""
        product = Product(
            name="Test Product",
            slug="test-product-empty",
            title_tr="Test Ürün",
            series=self.series,
            spec_layout=[],
        )
        
        # Should not raise
        product.clean()
        product.save()
        
        self.assertEqual(product.spec_layout, [])
    
    def test_partial_valid_spec_layout(self):
        """Partial valid spec_layout should fail for invalid items."""
        product = Product(
            name="Test Product",
            slug="test-product-partial",
            title_tr="Test Ürün",
            series=self.series,
            spec_layout=["goz-adedi", "invalid-key"],
        )
        
        with self.assertRaises(ValidationError) as context:
            product.clean()
        
        error_msg = context.exception.message_dict["spec_layout"][0]
        self.assertIn("invalid-key", error_msg)
        self.assertNotIn("goz-adedi", error_msg)
    
    def test_get_spec_keys_method(self):
        """Test that get_spec_keys returns ordered SpecKey objects."""
        product = Product.objects.create(
            name="Test Product",
            slug="test-product-get-keys",
            title_tr="Test Ürün",
            series=self.series,
            spec_layout=["boyutlar", "goz-adedi", "guc-kw"],
        )
        
        spec_keys = product.get_spec_keys()
        
        self.assertEqual(len(spec_keys), 3)
        # Should be in the order specified in spec_layout
        self.assertEqual(spec_keys[0].slug, "boyutlar")
        self.assertEqual(spec_keys[1].slug, "goz-adedi")
        self.assertEqual(spec_keys[2].slug, "guc-kw")
    
    def test_get_spec_keys_empty_layout(self):
        """Test get_spec_keys with empty layout."""
        product = Product.objects.create(
            name="Test Product",
            slug="test-product-empty-keys",
            title_tr="Test Ürün",
            series=self.series,
            spec_layout=[],
        )
        
        self.assertEqual(product.get_spec_keys(), [])


class SpecKeyModelTest(TestCase):
    """Test SpecKey model functionality."""
    
    def test_spec_key_str(self):
        """Test SpecKey __str__ method."""
        sk1 = SpecKey.objects.create(
            slug="power",
            label_tr="Güç",
            unit="kW",
        )
        self.assertEqual(str(sk1), "Güç (kW)")
        
        sk2 = SpecKey.objects.create(
            slug="count",
            label_tr="Adet",
        )
        self.assertEqual(str(sk2), "Adet")
    
    def test_spec_key_unique_slug(self):
        """Test that SpecKey slugs are unique."""
        from django.db import IntegrityError
        
        SpecKey.objects.create(
            slug="test-spec",
            label_tr="Test Spec",
        )
        
        with self.assertRaises(IntegrityError):
            SpecKey.objects.create(
                slug="test-spec",
                label_tr="Another Test Spec",
            )
