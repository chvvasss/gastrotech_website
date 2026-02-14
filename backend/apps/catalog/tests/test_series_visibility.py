"""
Tests for Series visibility rule: single-product series should be hidden.

Business rule:
- Series with 0 products = orphan, not visible
- Series with 1 product = single-product, not visible in navigation
- Series with 2+ products = visible as a grouping

The series record is preserved but hidden from navigation.
"""

import pytest
from django.test import TestCase
from django.db.models import Count, Q

from apps.catalog.models import Category, Series, Product, Brand
from apps.common.slugify_tr import slugify_tr


class SeriesVisibilityTestCase(TestCase):
    """Test series visibility rules."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests."""
        # Create a brand
        cls.brand = Brand.objects.create(
            name="Test Brand",
            slug="test-brand",
            is_active=True,
        )

        # Create a category
        cls.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
            series_mode="optional",
        )

        # Create series with 0, 1, and 2+ products
        cls.series_0_products = Series.objects.create(
            category=cls.category,
            name="Empty Series",
            slug="empty-series",
        )

        cls.series_1_product = Series.objects.create(
            category=cls.category,
            name="Single Product Series",
            slug="single-product-series",
        )

        cls.series_2_products = Series.objects.create(
            category=cls.category,
            name="Multi Product Series",
            slug="multi-product-series",
        )

        # Create products
        cls.product_single = Product.objects.create(
            series=cls.series_1_product,
            brand=cls.brand,
            name="Single Product",
            slug="single-product",
            title_tr="Tek Ürün",
            status="active",
        )

        cls.product_multi_1 = Product.objects.create(
            series=cls.series_2_products,
            brand=cls.brand,
            name="Multi Product 1",
            slug="multi-product-1",
            title_tr="Çoklu Ürün 1",
            status="active",
        )

        cls.product_multi_2 = Product.objects.create(
            series=cls.series_2_products,
            brand=cls.brand,
            name="Multi Product 2",
            slug="multi-product-2",
            title_tr="Çoklu Ürün 2",
            status="active",
        )

    def test_series_with_0_products_not_visible(self):
        """Series with 0 products should not be visible."""
        self.assertEqual(self.series_0_products.product_count, 0)
        self.assertFalse(self.series_0_products.is_visible)

    def test_series_with_1_product_not_visible(self):
        """Series with 1 product should not be visible."""
        self.assertEqual(self.series_1_product.product_count, 1)
        self.assertFalse(self.series_1_product.is_visible)

    def test_series_with_2_products_visible(self):
        """Series with 2+ products should be visible."""
        self.assertEqual(self.series_2_products.product_count, 2)
        self.assertTrue(self.series_2_products.is_visible)

    def test_visible_series_queryset(self):
        """visible_series() should only return series with 2+ products."""
        visible = Series.visible_series()
        self.assertEqual(visible.count(), 1)
        self.assertEqual(visible.first(), self.series_2_products)

    def test_annotate_visibility(self):
        """annotate_visibility should add _product_count and _is_visible."""
        qs = Series.annotate_visibility(Series.objects.filter(category=self.category))

        for series in qs:
            self.assertTrue(hasattr(series, '_product_count'))
            self.assertTrue(hasattr(series, '_is_visible'))

        # Check specific values
        series_0 = qs.get(slug="empty-series")
        self.assertEqual(series_0._product_count, 0)
        self.assertFalse(series_0._is_visible)

        series_1 = qs.get(slug="single-product-series")
        self.assertEqual(series_1._product_count, 1)
        self.assertFalse(series_1._is_visible)

        series_2 = qs.get(slug="multi-product-series")
        self.assertEqual(series_2._product_count, 2)
        self.assertTrue(series_2._is_visible)

    def test_visibility_only_counts_active_products(self):
        """Visibility should only count active products."""
        # Archive one product
        self.product_multi_1.status = "archived"
        self.product_multi_1.save()

        # Now series should have only 1 active product
        self.series_2_products.refresh_from_db()
        self.assertEqual(self.series_2_products.product_count, 1)
        self.assertFalse(self.series_2_products.is_visible)

        # Restore
        self.product_multi_1.status = "active"
        self.product_multi_1.save()

    def test_adding_product_changes_visibility(self):
        """Adding a second product should make series visible."""
        # Initially single-product series is not visible
        self.assertFalse(self.series_1_product.is_visible)

        # Add a second product
        product_new = Product.objects.create(
            series=self.series_1_product,
            brand=self.brand,
            name="New Product",
            slug="new-product",
            title_tr="Yeni Ürün",
            status="active",
        )

        # Now it should be visible
        self.series_1_product.refresh_from_db()
        self.assertEqual(self.series_1_product.product_count, 2)
        self.assertTrue(self.series_1_product.is_visible)

        # Clean up
        product_new.delete()


class SlugifyTRTestCase(TestCase):
    """Test Turkish-safe slugify function."""

    def test_turkish_characters(self):
        """Test Turkish character transliteration."""
        test_cases = [
            ("Gazlı Ocaklar", "gazli-ocaklar"),
            ("Pişirme Üniteleri", "pisirme-uniteleri"),
            ("Çorba Kazanları", "corba-kazanlari"),
            ("İçecek Makineleri", "icecek-makineleri"),
            ("Soğutma Sistemleri", "sogutma-sistemleri"),
            ("BÜYÜK HARFLER", "buyuk-harfler"),
            ("Şef Masaları", "sef-masalari"),
        ]

        for input_text, expected_slug in test_cases:
            with self.subTest(input=input_text):
                result = slugify_tr(input_text)
                self.assertEqual(result, expected_slug)

    def test_empty_string(self):
        """Test empty string returns empty."""
        self.assertEqual(slugify_tr(""), "")

    def test_multiple_dashes(self):
        """Test multiple dashes are collapsed."""
        self.assertEqual(slugify_tr("test---string"), "test-string")

    def test_leading_trailing_dashes(self):
        """Test leading/trailing dashes are stripped."""
        self.assertEqual(slugify_tr("-test-"), "test")

    def test_special_characters(self):
        """Test special characters are removed."""
        self.assertEqual(slugify_tr("Test! @#$% String"), "test-string")


class CategoryHierarchyTestCase(TestCase):
    """Test category hierarchy and ancestor validation."""

    @classmethod
    def setUpTestData(cls):
        """Set up test category hierarchy."""
        # Root -> Level1 -> Level2
        cls.root = Category.objects.create(
            name="Root Category",
            slug="root-category",
            series_mode="optional",
        )

        cls.level1 = Category.objects.create(
            name="Level 1",
            slug="level-1",
            parent=cls.root,
            series_mode="optional",
        )

        cls.level2 = Category.objects.create(
            name="Level 2",
            slug="level-2",
            parent=cls.level1,
            series_mode="optional",
        )

    def test_root_category_is_root(self):
        """Root category should have no parent."""
        self.assertTrue(self.root.is_root)
        self.assertIsNone(self.root.parent)

    def test_child_category_not_root(self):
        """Child categories should not be root."""
        self.assertFalse(self.level1.is_root)
        self.assertFalse(self.level2.is_root)

    def test_leaf_category(self):
        """Deepest category should be a leaf."""
        self.assertTrue(self.level2.is_leaf)
        self.assertFalse(self.root.is_leaf)

    def test_depth_calculation(self):
        """Test depth calculation."""
        self.assertEqual(self.root.depth, 0)
        self.assertEqual(self.level1.depth, 1)
        self.assertEqual(self.level2.depth, 2)

    def test_breadcrumbs(self):
        """Test breadcrumb path."""
        breadcrumbs = self.level2.breadcrumbs
        self.assertEqual(len(breadcrumbs), 3)
        self.assertEqual(breadcrumbs[0], self.root)
        self.assertEqual(breadcrumbs[1], self.level1)
        self.assertEqual(breadcrumbs[2], self.level2)

    def test_get_descendants(self):
        """Test getting all descendants."""
        descendants = list(self.root.get_descendants())
        self.assertIn(self.level1, descendants)
        self.assertIn(self.level2, descendants)

    def test_get_leaf_categories(self):
        """Test getting only leaf categories."""
        leaves = list(self.root.get_leaf_categories())
        self.assertEqual(len(leaves), 1)
        self.assertEqual(leaves[0], self.level2)


class IdempotencyTestCase(TestCase):
    """Test that audit operations are idempotent."""

    def test_running_audit_twice_no_changes(self):
        """Running the audit twice should produce no extra changes."""
        from apps.ops.management.commands.catalog_audit_fix import CatalogAuditor

        # First run
        auditor1 = CatalogAuditor(dry_run=True, verbose=False)
        report1 = auditor1.run_full_audit()

        # Second run
        auditor2 = CatalogAuditor(dry_run=True, verbose=False)
        report2 = auditor2.run_full_audit()

        # Issues should be the same
        self.assertEqual(
            report1['summary']['total_issues'],
            report2['summary']['total_issues']
        )
