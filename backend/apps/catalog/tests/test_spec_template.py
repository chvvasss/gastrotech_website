"""
Tests for SpecTemplate model and functionality.
"""

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.catalog.models import (
    Category,
    Product,
    Series,
    SpecKey,
    SpecTemplate,
)


class SpecTemplateModelTest(TestCase):
    """Test SpecTemplate model validation and apply functionality."""
    
    def setUp(self):
        """Create test data."""
        # Create spec keys
        self.spec_key1 = SpecKey.objects.create(
            slug="test-key-1",
            label_tr="Test Key 1",
            sort_order=1,
        )
        self.spec_key2 = SpecKey.objects.create(
            slug="test-key-2",
            label_tr="Test Key 2",
            sort_order=2,
        )
        
        # Create product
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
    
    def test_spec_template_valid_spec_layout(self):
        """Test that valid spec_layout passes validation."""
        template = SpecTemplate(
            name="Valid Template",
            spec_layout=["test-key-1", "test-key-2"],
        )
        
        # Should not raise
        template.full_clean()
        template.save()
        
        self.assertEqual(template.spec_layout, ["test-key-1", "test-key-2"])
    
    def test_spec_template_invalid_spec_layout(self):
        """Test that invalid spec_layout fails validation."""
        template = SpecTemplate(
            name="Invalid Template",
            spec_layout=["test-key-1", "invalid-key"],
        )
        
        with self.assertRaises(ValidationError) as context:
            template.full_clean()
        
        self.assertIn("spec_layout", context.exception.message_dict)
        self.assertIn("invalid-key", str(context.exception.message_dict["spec_layout"]))
    
    def test_spec_template_empty_spec_layout_valid(self):
        """Test that empty spec_layout is valid."""
        template = SpecTemplate(
            name="Empty Template",
            spec_layout=[],
        )
        
        # Should not raise
        template.full_clean()
        template.save()
    
    def test_apply_to_product_sets_spec_layout(self):
        """Test apply_to_product sets spec_layout on product."""
        template = SpecTemplate.objects.create(
            name="Apply Test Template",
            spec_layout=["test-key-1", "test-key-2"],
        )
        
        # Product has no spec_layout
        self.assertEqual(self.product.spec_layout, [])
        
        # Apply template
        updated = template.apply_to_product(self.product)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.spec_layout, ["test-key-1", "test-key-2"])
        self.assertIn("spec_layout", updated)
    
    def test_apply_to_product_sets_features_and_notes(self):
        """Test apply_to_product sets features and notes."""
        template = SpecTemplate.objects.create(
            name="Features Template",
            spec_layout=["test-key-1"],
            default_general_features=["Feature 1", "Feature 2"],
            default_notes=["Note 1"],
        )
        
        updated = template.apply_to_product(self.product)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.general_features, ["Feature 1", "Feature 2"])
        self.assertEqual(self.product.notes, ["Note 1"])
        self.assertIn("general_features", updated)
        self.assertIn("notes", updated)
    
    def test_apply_to_product_no_overwrite_by_default(self):
        """Test that apply_to_product does not overwrite existing values."""
        template = SpecTemplate.objects.create(
            name="Overwrite Test Template",
            spec_layout=["test-key-1"],
            default_general_features=["Template Feature"],
        )
        
        # Set existing values
        self.product.spec_layout = ["test-key-2"]
        self.product.general_features = ["Existing Feature"]
        self.product.save()
        
        # Apply without overwrite
        updated = template.apply_to_product(self.product, overwrite=False)
        
        self.product.refresh_from_db()
        # Should not change
        self.assertEqual(self.product.spec_layout, ["test-key-2"])
        self.assertEqual(self.product.general_features, ["Existing Feature"])
        self.assertEqual(updated, [])
    
    def test_apply_to_product_with_overwrite(self):
        """Test that apply_to_product overwrites when flag is set."""
        template = SpecTemplate.objects.create(
            name="Overwrite Template",
            spec_layout=["test-key-1"],
            default_general_features=["Template Feature"],
        )
        
        # Set existing values
        self.product.spec_layout = ["test-key-2"]
        self.product.general_features = ["Existing Feature"]
        self.product.save()
        
        # Apply with overwrite
        updated = template.apply_to_product(self.product, overwrite=True)
        
        self.product.refresh_from_db()
        # Should be overwritten
        self.assertEqual(self.product.spec_layout, ["test-key-1"])
        self.assertEqual(self.product.general_features, ["Template Feature"])
        self.assertIn("spec_layout", updated)
        self.assertIn("general_features", updated)
    
    def test_spec_template_with_series_scope(self):
        """Test SpecTemplate can be scoped to a series."""
        template = SpecTemplate.objects.create(
            name="Scoped Template",
            spec_layout=["test-key-1"],
            applies_to_series=self.series,
        )
        
        self.assertEqual(template.applies_to_series, self.series)
    
    def test_spec_template_unique_name(self):
        """Test that template names must be unique."""
        SpecTemplate.objects.create(
            name="Unique Name",
            spec_layout=[],
        )
        
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            SpecTemplate.objects.create(
                name="Unique Name",
                spec_layout=[],
            )
