"""
Tests for slug uniqueness constraints in catalog models.
"""

from django.db import IntegrityError
from django.test import TestCase

from apps.catalog.models import Category, Product, Series


class ProductSlugUniquenessTest(TestCase):
    """Test that product slugs are globally unique."""
    
    def setUp(self):
        """Create test category and series."""
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.series = Series.objects.create(
            category=self.category,
            name="Test Series",
            slug="test-series",
        )
    
    def test_product_slug_unique(self):
        """Products must have globally unique slugs."""
        Product.objects.create(
            name="Product One",
            slug="unique-product-slug",
            title_tr="Ürün Bir",
            series=self.series,
        )
        
        # Attempting to create another product with the same slug should fail
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name="Product Two",
                slug="unique-product-slug",
                title_tr="Ürün İki",
                series=self.series,
            )
    
    def test_product_slug_unique_across_series(self):
        """Product slugs must be unique across different series."""
        series2 = Series.objects.create(
            category=self.category,
            name="Another Series",
            slug="another-series",
        )
        
        Product.objects.create(
            name="Product One",
            slug="cross-series-slug",
            title_tr="Ürün Bir",
            series=self.series,
        )
        
        # Same slug in different series should still fail
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name="Product Two",
                slug="cross-series-slug",
                title_tr="Ürün İki",
                series=series2,
            )
    
    def test_different_slugs_allowed(self):
        """Products with different slugs should be allowed."""
        p1 = Product.objects.create(
            name="Product One",
            slug="product-one",
            title_tr="Ürün Bir",
            series=self.series,
        )
        p2 = Product.objects.create(
            name="Product Two",
            slug="product-two",
            title_tr="Ürün İki",
            series=self.series,
        )
        
        self.assertEqual(Product.objects.count(), 2)
        self.assertNotEqual(p1.slug, p2.slug)


class CategorySlugUniquenessTest(TestCase):
    """Test that category slugs are globally unique."""
    
    def test_category_slug_unique(self):
        """Categories must have unique slugs."""
        Category.objects.create(
            name="Category One",
            slug="category-slug",
        )
        
        with self.assertRaises(IntegrityError):
            Category.objects.create(
                name="Category Two",
                slug="category-slug",
            )


class SeriesSlugUniquenessTest(TestCase):
    """Test that series slugs are unique within category."""
    
    def setUp(self):
        """Create test categories."""
        self.category1 = Category.objects.create(
            name="Category One",
            slug="category-one",
        )
        self.category2 = Category.objects.create(
            name="Category Two",
            slug="category-two",
        )
    
    def test_series_slug_unique_within_category(self):
        """Series slugs must be unique within the same category."""
        Series.objects.create(
            category=self.category1,
            name="Series One",
            slug="series-slug",
        )
        
        with self.assertRaises(IntegrityError):
            Series.objects.create(
                category=self.category1,
                name="Series Two",
                slug="series-slug",
            )
    
    def test_series_slug_allowed_in_different_categories(self):
        """Same slug can be used in different categories."""
        s1 = Series.objects.create(
            category=self.category1,
            name="Series One",
            slug="series-slug",
        )
        s2 = Series.objects.create(
            category=self.category2,
            name="Series Two",
            slug="series-slug",
        )
        
        self.assertEqual(s1.slug, s2.slug)
        self.assertNotEqual(s1.category, s2.category)
