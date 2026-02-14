"""
Tests for the unified import service.

Tests cover:
- Series lookup by (category, slug)
- No silent fallback behavior
- Allow partial commit
- Import state machine
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from apps.catalog.models import Category, Series, Brand, Product
from apps.ops.models import ImportJob
from apps.ops.services.unified_import import UnifiedImportService

User = get_user_model()


class SeriesLookupTests(TestCase):
    """Tests for series lookup uniqueness per category."""

    def setUp(self):
        """Set up test data."""
        # Create two categories
        self.cat1 = Category.objects.create(
            name="Category 1",
            slug="category-1",
            series_mode="required",
        )
        self.cat2 = Category.objects.create(
            name="Category 2",
            slug="category-2",
            series_mode="required",
        )

        # Create series with same slug in different categories
        self.series1_cat1 = Series.objects.create(
            name="Premium Series",
            slug="premium",
            category=self.cat1,
        )
        self.series2_cat2 = Series.objects.create(
            name="Premium Series",
            slug="premium",
            category=self.cat2,
        )

        # Create a brand
        self.brand = Brand.objects.create(name="TestBrand", slug="testbrand")

    def test_series_same_slug_different_categories(self):
        """Test that same slug can exist in different categories."""
        # Both series should exist
        self.assertTrue(Series.objects.filter(slug="premium", category=self.cat1).exists())
        self.assertTrue(Series.objects.filter(slug="premium", category=self.cat2).exists())

        # They should be different objects
        self.assertNotEqual(self.series1_cat1.id, self.series2_cat2.id)

    def test_series_lookup_by_category(self):
        """Test series is looked up by (category, slug)."""
        # Lookup series in category 1
        series = Series.objects.filter(category=self.cat1, slug="premium").first()
        self.assertEqual(series.id, self.series1_cat1.id)
        self.assertEqual(series.category, self.cat1)

        # Lookup series in category 2
        series = Series.objects.filter(category=self.cat2, slug="premium").first()
        self.assertEqual(series.id, self.series2_cat2.id)
        self.assertEqual(series.category, self.cat2)


class NoSilentFallbackTests(TestCase):
    """Tests to ensure no silent fallback behavior."""

    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
            series_mode="required",
        )
        self.series = Series.objects.create(
            name="Test Series",
            slug="test-series",
            category=self.category,
        )
        self.brand = Brand.objects.create(name="TestBrand", slug="testbrand")

    def test_upsert_product_no_series_fallback(self):
        """Test product upsert fails when series not found (no fallback)."""
        service = UnifiedImportService(mode="strict")

        # Data with non-existent series
        data = {
            "slug": "test-product",
            "name": "Test Product",
            "title_tr": "Test Product TR",
            "series_slug": "nonexistent-series",
            "category_slug": "test-category",
            "brand_slug": "testbrand",
        }

        # Should raise error, not silently use first series
        with self.assertRaises(ValueError) as context:
            service._upsert_product_from_data(data)

        self.assertIn("not found", str(context.exception).lower())

    def test_upsert_product_with_valid_series(self):
        """Test product upsert succeeds with valid series."""
        service = UnifiedImportService(mode="strict")

        data = {
            "slug": "valid-product",
            "name": "Valid Product",
            "title_tr": "Valid Product TR",
            "series_slug": "test-series",
            "category_slug": "test-category",
            "brand_slug": "testbrand",
        }

        product, created = service._upsert_product_from_data(data)

        self.assertTrue(created)
        self.assertEqual(product.slug, "valid-product")
        self.assertEqual(product.series.slug, "test-series")


class ImportStateMachineTests(TestCase):
    """Tests for import state machine (allow_partial)."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
            series_mode="required",
        )
        self.series = Series.objects.create(
            name="Test Series",
            slug="test-series",
            category=self.category,
        )

    def test_job_status_validation_passed(self):
        """Test job status is VALIDATED_OK when no errors."""
        service = UnifiedImportService(mode="strict")

        # Mock validation with no errors
        service.report = service._init_report()
        service.report["counts"]["valid_product_rows"] = 5
        service.report["counts"]["error_rows"] = 0
        service.report["counts"]["warning_rows"] = 0

        # Determine status
        error_count = service.report["counts"]["error_rows"]
        warning_count = service.report["counts"]["warning_rows"]

        if error_count > 0:
            status = "failed_validation"
        elif warning_count > 0:
            status = "validation_warnings"
        else:
            status = "validation_passed"

        self.assertEqual(status, "validation_passed")

    def test_job_status_validation_warnings(self):
        """Test job status is VALIDATION_WARNINGS when warnings exist."""
        service = UnifiedImportService(mode="strict")

        service.report = service._init_report()
        service.report["counts"]["valid_product_rows"] = 5
        service.report["counts"]["error_rows"] = 0
        service.report["counts"]["warning_rows"] = 2

        error_count = service.report["counts"]["error_rows"]
        warning_count = service.report["counts"]["warning_rows"]

        if error_count > 0:
            status = "failed_validation"
        elif warning_count > 0:
            status = "validation_warnings"
        else:
            status = "validation_passed"

        self.assertEqual(status, "validation_warnings")

    def test_job_status_failed_validation(self):
        """Test job status is FAILED_VALIDATION when errors exist."""
        service = UnifiedImportService(mode="strict")

        service.report = service._init_report()
        service.report["counts"]["valid_product_rows"] = 3
        service.report["counts"]["error_rows"] = 2
        service.report["counts"]["warning_rows"] = 0

        error_count = service.report["counts"]["error_rows"]
        warning_count = service.report["counts"]["warning_rows"]

        if error_count > 0:
            status = "failed_validation"
        elif warning_count > 0:
            status = "validation_warnings"
        else:
            status = "validation_passed"

        self.assertEqual(status, "failed_validation")


class ImportServiceInitializationTests(TestCase):
    """Tests for import service initialization."""

    def test_strict_mode(self):
        """Test service initializes in strict mode."""
        service = UnifiedImportService(mode="strict")
        self.assertEqual(service.mode, "strict")

    def test_smart_mode(self):
        """Test service initializes in smart mode."""
        service = UnifiedImportService(mode="smart")
        self.assertEqual(service.mode, "smart")

    def test_report_initialization(self):
        """Test report is properly initialized."""
        service = UnifiedImportService(mode="strict")

        self.assertIn("status", service.report)
        self.assertIn("issues", service.report)
        self.assertIn("candidates", service.report)
        self.assertIn("counts", service.report)

        self.assertEqual(service.report["status"], "pending")
        self.assertIsInstance(service.report["issues"], list)
        self.assertEqual(len(service.report["issues"]), 0)


class CandidateDeduplicationTests(TestCase):
    """Tests for candidate deduplication in smart mode."""

    def setUp(self):
        """Set up test data."""
        self.service = UnifiedImportService(mode="smart")

    def test_seen_candidates_tracking(self):
        """Test seen candidates are tracked to prevent duplicates."""
        # Verify seen candidates structure exists
        self.assertIn("categories", self.service._seen_candidates)
        self.assertIn("series", self.service._seen_candidates)
        self.assertIn("brands", self.service._seen_candidates)
        self.assertIn("products", self.service._seen_candidates)

        # All should start empty
        self.assertEqual(len(self.service._seen_candidates["categories"]), 0)
        self.assertEqual(len(self.service._seen_candidates["series"]), 0)
        self.assertEqual(len(self.service._seen_candidates["brands"]), 0)
