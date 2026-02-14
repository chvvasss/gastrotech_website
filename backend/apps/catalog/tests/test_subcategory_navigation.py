"""
Tests for subcategory navigation system.

Tests the complete subcategory feature:
- Category model helper properties
- Category children endpoint
- Brand/Series filtering by subcategory
- Product filtering by subcategory
- Taxonomy parsing for imports
"""

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Brand, Category, Product, Series, Variant
from apps.ops.services.taxonomy_parser import (
    parse_taxonomy_path,
    resolve_taxonomy_category,
    validate_series_category_match,
)


class CategoryHierarchyTestCase(TestCase):
    """Test Category model hierarchy features."""

    def setUp(self):
        # Create root category
        self.root = Category.objects.create(
            name="Fırınlar",
            slug="firinlar",
            order=1,
        )

        # Create subcategories
        self.pizza = Category.objects.create(
            name="Pizza Fırını",
            slug="pizza-firini",
            parent=self.root,
            order=1,
        )

        self.electric = Category.objects.create(
            name="Elektrikli Fırın",
            slug="elektrikli-firin",
            parent=self.root,
            order=2,
        )

    def test_is_root_property(self):
        """Test is_root property."""
        assert self.root.is_root is True
        assert self.pizza.is_root is False
        assert self.electric.is_root is False

    def test_is_leaf_property(self):
        """Test is_leaf property."""
        assert self.root.is_leaf is False  # Has children
        assert self.pizza.is_leaf is True  # No children
        assert self.electric.is_leaf is True  # No children

    def test_depth_property(self):
        """Test depth calculation."""
        assert self.root.depth == 0
        assert self.pizza.depth == 1
        assert self.electric.depth == 1

    def test_breadcrumbs_property(self):
        """Test breadcrumb path generation."""
        root_breadcrumbs = self.root.breadcrumbs
        assert len(root_breadcrumbs) == 1
        assert root_breadcrumbs[0] == self.root

        pizza_breadcrumbs = self.pizza.breadcrumbs
        assert len(pizza_breadcrumbs) == 2
        assert pizza_breadcrumbs[0] == self.root
        assert pizza_breadcrumbs[1] == self.pizza

    def test_breadcrumb_path_string(self):
        """Test breadcrumb_path string representation."""
        assert self.root.breadcrumb_path == "Fırınlar"
        assert self.pizza.breadcrumb_path == "Fırınlar > Pizza Fırını"

    def test_str_representation(self):
        """Test __str__ method."""
        assert str(self.root) == "Fırınlar"
        assert str(self.pizza) == "Fırınlar > Pizza Fırını"

    def test_prevent_self_parent(self):
        """Test validation prevents self-parenting."""
        category = Category(name="Test", slug="test", parent=None)
        category.save()

        # Try to set self as parent
        category.parent = category
        with pytest.raises(ValidationError, match="cannot be its own parent"):
            category.clean()

    def test_prevent_circular_reference(self):
        """Test validation prevents circular references."""
        cat_a = Category.objects.create(name="A", slug="a")
        cat_b = Category.objects.create(name="B", slug="b", parent=cat_a)

        # Try to make A a child of B (circular)
        cat_a.parent = cat_b
        with pytest.raises(ValidationError, match="Circular category reference"):
            cat_a.clean()

    def test_max_depth_enforcement(self):
        """Test maximum depth of 2 levels is enforced."""
        # Try to create a third level (should fail)
        deep_cat = Category(
            name="Too Deep",
            slug="too-deep",
            parent=self.pizza,  # pizza is already depth 1
        )

        with pytest.raises(ValidationError, match="Maximum category depth"):
            deep_cat.clean()


class CategoryChildrenAPITestCase(TestCase):
    """Test category children endpoint."""

    def setUp(self):
        self.client = APIClient()

        # Create hierarchy
        self.root = Category.objects.create(name="Fırınlar", slug="firinlar")
        self.pizza = Category.objects.create(
            name="Pizza Fırını",
            slug="pizza-firini",
            parent=self.root,
        )
        self.electric = Category.objects.create(
            name="Elektrikli Fırın",
            slug="elektrikli-firin",
            parent=self.root,
        )

        # Create series and products for counts
        self.series_pizza = Series.objects.create(
            name="600 Series",
            slug="600-series",
            category=self.pizza,
        )

        self.brand = Brand.objects.create(name="Gastrotech", slug="gastrotech")

        self.product = Product.objects.create(
            name="Pizza Oven",
            slug="pizza-oven",
            title_tr="Pizza Fırını",
            series=self.series_pizza,
            brand=self.brand,
            status="active",
        )

    def test_get_category_children(self):
        """Test GET /api/v1/categories/<slug>/children/."""
        response = self.client.get(f"/api/v1/categories/firinlar/children/")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        slugs = [cat["slug"] for cat in data]
        assert "pizza-firini" in slugs
        assert "elektrikli-firin" in slugs

    def test_children_include_product_counts(self):
        """Test children endpoint includes product counts."""
        response = self.client.get(f"/api/v1/categories/firinlar/children/")

        assert response.status_code == 200
        data = response.json()

        pizza_data = next(cat for cat in data if cat["slug"] == "pizza-firini")
        assert pizza_data["products_count"] == 1

        electric_data = next(cat for cat in data if cat["slug"] == "elektrikli-firin")
        assert electric_data["products_count"] == 0

    def test_category_tree_includes_is_leaf(self):
        """Test category tree endpoint includes is_leaf flag."""
        response = self.client.get("/api/v1/categories/tree/")

        assert response.status_code == 200
        data = response.json()

        root_cat = next(cat for cat in data if cat["slug"] == "firinlar")
        assert root_cat["is_leaf"] is False
        assert root_cat["subcategory_count"] == 2

        # Check children
        pizza_child = next(
            child for child in root_cat["children"] if child["slug"] == "pizza-firini"
        )
        assert pizza_child["is_leaf"] is True
        assert pizza_child["subcategory_count"] == 0


class BrandSeriesFilteringTestCase(TestCase):
    """Test brand and series filtering by subcategory."""

    def setUp(self):
        self.client = APIClient()

        # Create hierarchy
        self.root = Category.objects.create(name="Fırınlar", slug="firinlar")
        self.pizza = Category.objects.create(
            name="Pizza Fırını",
            slug="pizza-firini",
            parent=self.root,
        )
        self.electric = Category.objects.create(
            name="Elektrikli Fırın",
            slug="elektrikli-firin",
            parent=self.root,
        )

        # Create brands
        self.brand_a = Brand.objects.create(name="Brand A", slug="brand-a")
        self.brand_b = Brand.objects.create(name="Brand B", slug="brand-b")

        # Create series
        self.series_pizza_a = Series.objects.create(
            name="Pizza 600",
            slug="pizza-600",
            category=self.pizza,
        )

        self.series_electric_b = Series.objects.create(
            name="Electric 700",
            slug="electric-700",
            category=self.electric,
        )

        # Create products
        self.product_pizza_a = Product.objects.create(
            name="Pizza Oven A",
            slug="pizza-oven-a",
            title_tr="Pizza Fırını A",
            series=self.series_pizza_a,
            brand=self.brand_a,
            status="active",
        )

        self.product_electric_b = Product.objects.create(
            name="Electric Oven B",
            slug="electric-oven-b",
            title_tr="Elektrikli Fırın B",
            series=self.series_electric_b,
            brand=self.brand_b,
            status="active",
        )

    def test_brands_filtered_by_subcategory(self):
        """Test GET /api/v1/brands/?category=<subcategory>."""
        # Brands in pizza subcategory
        response = self.client.get("/api/v1/brands/?category=pizza-firini")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["slug"] == "brand-a"

        # Brands in electric subcategory
        response = self.client.get("/api/v1/brands/?category=elektrikli-firin")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["slug"] == "brand-b"

    def test_series_filtered_by_subcategory(self):
        """Test GET /api/v1/series/?category=<subcategory>."""
        # Series in pizza subcategory
        response = self.client.get("/api/v1/series/?category=pizza-firini")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["slug"] == "pizza-600"

        # Series in electric subcategory
        response = self.client.get("/api/v1/series/?category=elektrikli-firin")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["slug"] == "electric-700"

    def test_series_filtered_by_subcategory_and_brand(self):
        """Test GET /api/v1/series/?category=<subcategory>&brand=<brand>."""
        response = self.client.get("/api/v1/series/?category=pizza-firini&brand=brand-a")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["slug"] == "pizza-600"

        # Different brand should return empty
        response = self.client.get("/api/v1/series/?category=pizza-firini&brand=brand-b")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 0

    def test_products_filtered_by_subcategory(self):
        """Test GET /api/v1/products/?category=<subcategory>."""
        response = self.client.get("/api/v1/products/?category=pizza-firini")

        assert response.status_code == 200
        data = response.json()

        assert data["count"] == 1
        assert data["results"][0]["slug"] == "pizza-oven-a"


class TaxonomyParserTestCase(TestCase):
    """Test taxonomy path parsing for imports."""

    def test_parse_single_level(self):
        """Test parsing root category only."""
        root_slug, sub_slug = parse_taxonomy_path("Fırınlar")

        assert root_slug == "firinlar"
        assert sub_slug is None

    def test_parse_two_levels(self):
        """Test parsing root > subcategory."""
        root_slug, sub_slug = parse_taxonomy_path("Fırınlar > Pizza Fırını")

        assert root_slug == "firinlar"
        assert sub_slug == "pizza-firini"

    def test_parse_with_extra_spaces(self):
        """Test parsing handles whitespace correctly."""
        root_slug, sub_slug = parse_taxonomy_path("  Fırınlar  >  Pizza Fırını  ")

        assert root_slug == "firinlar"
        assert sub_slug == "pizza-firini"

    def test_parse_too_deep_raises_error(self):
        """Test parsing > 2 levels raises validation error."""
        with pytest.raises(ValidationError, match="Maximum depth is 2"):
            parse_taxonomy_path("Level 1 > Level 2 > Level 3")

    def test_parse_empty_string(self):
        """Test parsing empty/whitespace returns None."""
        root_slug, sub_slug = parse_taxonomy_path("")

        assert root_slug is None
        assert sub_slug is None

    def test_resolve_existing_root(self):
        """Test resolving existing root category."""
        Category.objects.create(name="Fırınlar", slug="firinlar")

        result = resolve_taxonomy_category("Fırınlar", mode="strict")

        assert "category" in result
        assert result["category"].slug == "firinlar"

    def test_resolve_existing_subcategory(self):
        """Test resolving existing subcategory."""
        root = Category.objects.create(name="Fırınlar", slug="firinlar")
        pizza = Category.objects.create(
            name="Pizza Fırını",
            slug="pizza-firini",
            parent=root,
        )

        result = resolve_taxonomy_category("Fırınlar > Pizza Fırını", mode="strict")

        assert "category" in result
        assert result["category"].slug == "pizza-firini"
        assert result["category"].parent == root

    def test_resolve_missing_strict_mode_error(self):
        """Test resolving non-existent category in strict mode returns error."""
        result = resolve_taxonomy_category("Nonexistent", mode="strict")

        assert "error" in result
        assert "not found" in result["error"]

    def test_resolve_missing_smart_mode_candidate(self):
        """Test resolving non-existent category in smart mode returns candidate."""
        result = resolve_taxonomy_category("New Category", mode="smart")

        assert "candidate" in result
        candidate = result["candidate"]
        assert candidate["type"] == "category"
        assert candidate["slug"] == "new-category"
        assert candidate["name"] == "New Category"
        assert candidate["parent"] is None

    def test_validate_series_category_match(self):
        """Test series category validation."""
        cat_pizza = Category.objects.create(name="Pizza", slug="pizza")
        cat_electric = Category.objects.create(name="Electric", slug="electric")

        series_pizza = Series.objects.create(
            name="600",
            slug="600",
            category=cat_pizza,
        )

        # Matching category - should be valid
        error = validate_series_category_match(series_pizza, cat_pizza)
        assert error is None

        # Mismatched category - should return error
        error = validate_series_category_match(series_pizza, cat_electric)
        assert error is not None
        assert "belongs to category" in error
        assert "Pizza" in error
        assert "Electric" in error


@pytest.mark.django_db
class IntegrationTestCase:
    """Integration tests for complete navigation flow."""

    def test_complete_navigation_flow(self, client):
        """Test complete user navigation flow through subcategory system."""
        # Setup data
        root = Category.objects.create(name="Fırınlar", slug="firinlar")
        pizza = Category.objects.create(
            name="Pizza Fırını",
            slug="pizza-firini",
            parent=root,
        )

        brand = Brand.objects.create(name="Gastrotech", slug="gastrotech")

        series = Series.objects.create(
            name="600 Series",
            slug="600-series",
            category=pizza,
        )

        product = Product.objects.create(
            name="Pizza Oven",
            slug="pizza-oven",
            title_tr="Pizza Fırını",
            series=series,
            brand=brand,
            status="active",
        )

        Variant.objects.create(
            product=product,
            model_code="PO-600",
            name_tr="Pizza Oven 600",
        )

        # Step 1: Get category tree
        response = client.get("/api/v1/categories/tree/")
        assert response.status_code == 200
        tree = response.json()

        root_cat = next(cat for cat in tree if cat["slug"] == "firinlar")
        assert root_cat["is_leaf"] is False

        # Step 2: Get subcategories
        response = client.get("/api/v1/categories/firinlar/children/")
        assert response.status_code == 200
        subcategories = response.json()

        assert len(subcategories) == 1
        assert subcategories[0]["slug"] == "pizza-firini"

        # Step 3: Get brands for subcategory
        response = client.get("/api/v1/brands/?category=pizza-firini")
        assert response.status_code == 200
        brands = response.json()

        assert len(brands) == 1
        assert brands[0]["slug"] == "gastrotech"

        # Step 4: Get series for subcategory + brand
        response = client.get("/api/v1/series/?category=pizza-firini&brand=gastrotech")
        assert response.status_code == 200
        series_list = response.json()

        assert len(series_list) == 1
        assert series_list[0]["slug"] == "600-series"

        # Step 5: Get products for subcategory + brand + series
        response = client.get(
            "/api/v1/products/?category=pizza-firini&brand=gastrotech&series=600-series"
        )
        assert response.status_code == 200
        products = response.json()

        assert products["count"] == 1
        assert products["results"][0]["slug"] == "pizza-oven"
