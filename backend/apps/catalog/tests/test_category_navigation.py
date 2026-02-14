"""
Tests for category navigation endpoints.

Tests the new category-first navigation flow:
- GET /api/v1/categories/?include_counts=true
- GET /api/v1/categories/<slug>/
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.catalog.models import Category, Series, Product


class CategoryNavigationTestCase(TestCase):
    """Test category navigation endpoints for new categories-first flow."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create test categories
        self.category1 = Category.objects.create(
            name="Pişirme Üniteleri",
            slug="pisirme",
            menu_label="Pişirme",
            description_short="Profesyonel pişirme ekipmanları",
            order=1,
            is_featured=True
        )

        self.category2 = Category.objects.create(
            name="Soğutma Sistemleri",
            slug="sogutma",
            menu_label="Soğutma",
            description_short="Profesyonel soğutma ekipmanları",
            order=2,
            is_featured=False
        )

        # Create series in category1
        self.series1 = Series.objects.create(
            category=self.category1,
            name="600 Serisi",
            slug="600",
            description_short="600 Serisi profesyonel pişirme ekipmanları",
            order=1,
            is_featured=True
        )

        self.series2 = Series.objects.create(
            category=self.category1,
            name="700 Serisi",
            slug="700",
            description_short="700 Serisi profesyonel pişirme ekipmanları",
            order=2,
            is_featured=False
        )

        # Create series in category2
        self.series3 = Series.objects.create(
            category=self.category2,
            name="Buzdolapları",
            slug="buzdolaplari",
            description_short="Profesyonel buzdolapları",
            order=1,
            is_featured=True
        )

        # Create products
        for i in range(5):
            Product.objects.create(
                series=self.series1,
                title_tr=f"Gazlı Ocak {i+1}",
                slug=f"gazli-ocak-{i+1}",
                status="active"
            )

        for i in range(3):
            Product.objects.create(
                series=self.series2,
                title_tr=f"Fırın {i+1}",
                slug=f"firin-{i+1}",
                status="active"
            )

        for i in range(2):
            Product.objects.create(
                series=self.series3,
                title_tr=f"Buzdolabı {i+1}",
                slug=f"buzdolabi-{i+1}",
                status="active"
            )

    def test_categories_list_basic(self):
        """Test basic categories list without counts."""
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # API returns paginated response
        self.assertIn("results", response.data)
        data = response.data["results"]
        self.assertEqual(len(data), 2)

        # Check basic fields
        category = data[0]
        self.assertIn("id", category)
        self.assertIn("name", category)
        self.assertIn("slug", category)
        self.assertIn("order", category)

    def test_categories_list_with_counts(self):
        """Test categories list with series and product counts."""
        response = self.client.get("/api/v1/categories/?include_counts=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # API returns paginated response
        self.assertIn("results", response.data)
        data = response.data["results"]
        self.assertEqual(len(data), 2)

        # Find category1 (Pişirme)
        pisirme = next(cat for cat in data if cat["slug"] == "pisirme")

        # Check counts are present
        self.assertIn("series_count", pisirme)
        self.assertIn("products_count", pisirme)

        # Verify counts
        self.assertEqual(pisirme["series_count"], 2)  # 600 and 700 series
        self.assertEqual(pisirme["products_count"], 8)  # 5 + 3 products

        # Find category2 (Soğutma)
        sogutma = next(cat for cat in data if cat["slug"] == "sogutma")
        self.assertEqual(sogutma["series_count"], 1)  # Buzdolapları series
        self.assertEqual(sogutma["products_count"], 2)  # 2 products

    def test_category_detail(self):
        """Test category detail endpoint with series list."""
        response = self.client.get(f"/api/v1/categories/{self.category1.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check basic fields
        self.assertEqual(response.data["name"], "Pişirme Üniteleri")
        self.assertEqual(response.data["slug"], "pisirme")

        # Check products_count
        self.assertIn("products_count", response.data)
        self.assertEqual(response.data["products_count"], 8)

        # Check series list
        self.assertIn("series", response.data)
        self.assertEqual(len(response.data["series"]), 2)

        # Check first series
        series600 = next(s for s in response.data["series"] if s["slug"] == "600")
        self.assertEqual(series600["name"], "600 Serisi")
        self.assertIn("products_count", series600)
        self.assertEqual(series600["products_count"], 5)

        # Check second series
        series700 = next(s for s in response.data["series"] if s["slug"] == "700")
        self.assertEqual(series700["products_count"], 3)

    def test_category_detail_not_found(self):
        """Test category detail with non-existent slug."""
        response = self.client.get("/api/v1/categories/non-existent/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_category_detail_performance(self):
        """Test that category detail uses efficient queries."""
        # This test verifies no N+1 queries
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(f"/api/v1/categories/{self.category1.slug}/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should be ~3-4 queries max (category + series with counts + annotations)
        # Not 1 query per series (N+1 problem)
        self.assertLessEqual(
            len(queries),
            5,
            f"Too many queries ({len(queries)}). Possible N+1 issue."
        )

    def test_category_with_inactive_products(self):
        """Test that inactive products are not counted."""
        # Add inactive products
        for i in range(3):
            Product.objects.create(
                series=self.series1,
                title_tr=f"Inactive Product {i+1}",
                slug=f"inactive-{i+1}",
                status="draft"  # Not active
            )

        response = self.client.get(f"/api/v1/categories/{self.category1.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should still be 8 active products (not 11)
        self.assertEqual(response.data["products_count"], 8)

        # Series should also only count active products
        series600 = next(s for s in response.data["series"] if s["slug"] == "600")
        self.assertEqual(series600["products_count"], 5)  # Not 8

    def test_categories_ordering(self):
        """Test that categories are ordered by order field."""
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # API returns paginated response
        data = response.data["results"]
        # First category should be Pişirme (order=1)
        self.assertEqual(data[0]["slug"], "pisirme")
        # Second category should be Soğutma (order=2)
        self.assertEqual(data[1]["slug"], "sogutma")

    def test_series_ordering_in_category_detail(self):
        """Test that series are ordered by order field in category detail."""
        response = self.client.get(f"/api/v1/categories/{self.category1.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        series_list = response.data["series"]
        # First series should be 600 (order=1)
        self.assertEqual(series_list[0]["slug"], "600")
        # Second series should be 700 (order=2)
        self.assertEqual(series_list[1]["slug"], "700")
