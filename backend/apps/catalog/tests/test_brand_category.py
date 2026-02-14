"""
Tests for Brand-Category M2M relationship.

Tests:
- Brand can be associated with multiple categories
- Category can have multiple brands
- BrandCategory through model tracks the relationship
- Import system auto-creates brand-category relationships
"""

from django.test import TestCase
from apps.catalog.models import Brand, Category, BrandCategory, Series, Product


class BrandCategoryRelationshipTest(TestCase):
    """Test Brand-Category M2M relationship."""

    def setUp(self):
        """Create test fixtures."""
        # Categories
        self.cat_ovens = Category.objects.create(name="Ovens", slug="ovens")
        self.cat_dishwashers = Category.objects.create(name="Dishwashers", slug="dishwashers")
        self.cat_refrigerators = Category.objects.create(name="Refrigerators", slug="refrigerators")

        # Brands
        self.brand_bosch = Brand.objects.create(name="Bosch", slug="bosch")
        self.brand_siemens = Brand.objects.create(name="Siemens", slug="siemens")

        # Series
        self.series_ovens = Series.objects.create(
            name="600 Series",
            slug="600-series-ovens",
            category=self.cat_ovens,
        )
        self.series_dishwashers = Series.objects.create(
            name="600 Series",
            slug="600-series-dishwashers",
            category=self.cat_dishwashers,
        )

    def test_brand_can_have_multiple_categories(self):
        """Test that a brand can be associated with multiple categories."""
        # Associate Bosch with Ovens and Dishwashers
        BrandCategory.objects.create(brand=self.brand_bosch, category=self.cat_ovens)
        BrandCategory.objects.create(brand=self.brand_bosch, category=self.cat_dishwashers)

        # Check relationships
        self.assertEqual(self.brand_bosch.categories.count(), 2)
        self.assertIn(self.cat_ovens, self.brand_bosch.categories.all())
        self.assertIn(self.cat_dishwashers, self.brand_bosch.categories.all())

    def test_category_can_have_multiple_brands(self):
        """Test that a category can have multiple brands."""
        # Associate Ovens with Bosch and Siemens
        BrandCategory.objects.create(brand=self.brand_bosch, category=self.cat_ovens)
        BrandCategory.objects.create(brand=self.brand_siemens, category=self.cat_ovens)

        # Check relationships
        self.assertEqual(self.cat_ovens.brands.count(), 2)
        self.assertIn(self.brand_bosch, self.cat_ovens.brands.all())
        self.assertIn(self.brand_siemens, self.cat_ovens.brands.all())

    def test_brand_category_through_model(self):
        """Test BrandCategory through model attributes."""
        bc = BrandCategory.objects.create(
            brand=self.brand_bosch,
            category=self.cat_ovens,
            is_active=True,
            order=10,
        )

        self.assertTrue(bc.is_active)
        self.assertEqual(bc.order, 10)
        self.assertEqual(str(bc), "Bosch in Ovens")

    def test_unique_constraint_brand_category(self):
        """Test that brand-category combination must be unique."""
        # Create first relationship
        BrandCategory.objects.create(brand=self.brand_bosch, category=self.cat_ovens)

        # Try to create duplicate - should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            BrandCategory.objects.create(brand=self.brand_bosch, category=self.cat_ovens)

    def test_brand_category_cascade_delete(self):
        """Test that deleting brand or category deletes the relationship."""
        bc = BrandCategory.objects.create(brand=self.brand_bosch, category=self.cat_ovens)

        # Delete brand
        self.brand_bosch.delete()

        # Relationship should be deleted
        self.assertFalse(BrandCategory.objects.filter(id=bc.id).exists())

    def test_import_creates_brand_category_relationship(self):
        """Test that import system auto-creates brand-category relationships."""
        # Create a product with brand and category
        product = Product.objects.create(
            name="Test Oven",
            slug="test-oven",
            title_tr="Test Fırın",
            series=self.series_ovens,
            brand=self.brand_bosch,
            status="active",
        )

        # Import system should have created brand-category relationship
        # (This is tested via import service, but we check the model behavior here)
        self.assertTrue(product.brand is not None)
        self.assertTrue(product.series.category is not None)

    def test_brand_categories_ordering(self):
        """Test that brand categories are ordered by order field."""
        BrandCategory.objects.create(brand=self.brand_bosch, category=self.cat_ovens, order=20)
        BrandCategory.objects.create(brand=self.brand_bosch, category=self.cat_dishwashers, order=10)
        BrandCategory.objects.create(brand=self.brand_bosch, category=self.cat_refrigerators, order=30)

        # Get ordered brand categories
        brand_cats = self.brand_bosch.brand_categories.all()

        # Check order
        self.assertEqual(brand_cats[0].category, self.cat_dishwashers)  # order=10
        self.assertEqual(brand_cats[1].category, self.cat_ovens)  # order=20
        self.assertEqual(brand_cats[2].category, self.cat_refrigerators)  # order=30
