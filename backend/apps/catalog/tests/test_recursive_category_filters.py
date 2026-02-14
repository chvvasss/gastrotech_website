"""
Tests for category descendant filtering across products, series, and brands.
"""

from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Brand, Category, Product, Series


class RecursiveCategoryFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.root = Category.objects.create(name="Root", slug="root")
        self.child = Category.objects.create(
            name="Child", slug="child", parent=self.root
        )

        self.brand = Brand.objects.create(name="Brand A", slug="brand-a")
        self.series = Series.objects.create(
            name="Child Series", slug="child-series", category=self.child
        )
        Product.objects.create(
            name="Test Product",
            slug="test-product",
            title_tr="Test Product",
            series=self.series,
            brand=self.brand,
            status="active",
        )

    def test_products_include_descendants_by_default(self):
        response = self.client.get("/api/v1/products/?category=root")
        assert response.status_code == 200
        data = response.json()
        if isinstance(data, dict):
            results = data.get("results", [])
            count = data.get("count", len(results))
        else:
            count = len(data)
        assert count == 1

    def test_products_exclude_descendants_when_disabled(self):
        response = self.client.get("/api/v1/products/?category=root&include_descendants=false")
        assert response.status_code == 200
        data = response.json()
        if isinstance(data, dict):
            results = data.get("results", [])
            count = data.get("count", len(results))
        else:
            count = len(data)
        assert count == 0

    def test_series_include_descendants_when_enabled(self):
        response = self.client.get("/api/v1/series/?category=root&include_descendants=true")
        assert response.status_code == 200
        data = response.json()
        results = data.get("results") if isinstance(data, dict) else data
        assert len(results) == 1
        assert results[0]["slug"] == "child-series"

    def test_series_exclude_descendants_by_default(self):
        response = self.client.get("/api/v1/series/?category=root")
        assert response.status_code == 200
        data = response.json()
        results = data.get("results") if isinstance(data, dict) else data
        assert len(results) == 0

    def test_brands_include_descendants_when_enabled(self):
        response = self.client.get("/api/v1/brands/?category=root&include_descendants=true")
        assert response.status_code == 200
        data = response.json()
        results = data.get("results") if isinstance(data, dict) else data
        assert len(results) == 1
        assert results[0]["slug"] == "brand-a"

    def test_brands_exclude_descendants_by_default(self):
        response = self.client.get("/api/v1/brands/?category=root")
        assert response.status_code == 200
        data = response.json()
        results = data.get("results") if isinstance(data, dict) else data
        assert len(results) == 0
