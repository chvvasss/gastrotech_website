"""
Tests for catalog public API endpoints.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.catalog.models import (
    Category,
    Media,
    Product,
    ProductMedia,
    Series,
    SpecKey,
    TaxonomyNode,
    Variant,
)


class MediaFileEndpointTest(TestCase):
    """Test media file streaming endpoint with ETag caching."""
    
    def setUp(self):
        """Create test media."""
        self.client = APIClient()
        self.media = Media.objects.create(
            kind="image",
            filename="test.jpg",
            content_type="image/jpeg",
            bytes=b"fake image binary data",
            width=800,
            height=600,
        )
    
    def test_media_file_returns_200_with_etag(self):
        """Media file endpoint returns 200 with ETag header."""
        url = f"/api/v1/media/{self.media.id}/file/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertEqual(int(response["Content-Length"]), self.media.size_bytes)
        self.assertIn("ETag", response)
        self.assertEqual(response["ETag"], f'"{self.media.checksum_sha256}"')
        self.assertEqual(response["Cache-Control"], "public, max-age=604800")
        self.assertEqual(response.content, self.media.bytes)
    
    def test_media_file_returns_304_when_etag_matches(self):
        """Media file endpoint returns 304 when If-None-Match matches ETag."""
        url = f"/api/v1/media/{self.media.id}/file/"
        
        # First request to get ETag
        response1 = self.client.get(url)
        etag = response1["ETag"]
        
        # Second request with If-None-Match
        response2 = self.client.get(url, HTTP_IF_NONE_MATCH=etag)
        
        self.assertEqual(response2.status_code, 304)
        self.assertEqual(response2["ETag"], etag)
    
    def test_media_file_returns_304_without_quotes(self):
        """Media file endpoint returns 304 when ETag sent without quotes."""
        url = f"/api/v1/media/{self.media.id}/file/"
        
        # Request with If-None-Match (no quotes)
        response = self.client.get(
            url,
            HTTP_IF_NONE_MATCH=self.media.checksum_sha256,
        )
        
        self.assertEqual(response.status_code, 304)
    
    def test_media_file_returns_200_when_etag_mismatches(self):
        """Media file endpoint returns 200 when ETag doesn't match."""
        url = f"/api/v1/media/{self.media.id}/file/"
        
        response = self.client.get(url, HTTP_IF_NONE_MATCH='"wrong-etag"')
        
        self.assertEqual(response.status_code, 200)
    
    def test_media_file_404_for_nonexistent(self):
        """Media file endpoint returns 404 for non-existent media."""
        import uuid
        url = f"/api/v1/media/{uuid.uuid4()}/file/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_media_metadata_excludes_bytes(self):
        """Media metadata endpoint returns metadata without bytes."""
        url = f"/api/v1/media/{self.media.id}/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["id"], str(self.media.id))
        self.assertEqual(data["kind"], "image")
        self.assertEqual(data["filename"], "test.jpg")
        self.assertEqual(data["file_url"], f"/api/v1/media/{self.media.id}/file")
        self.assertNotIn("bytes", data)


class NavEndpointTest(TestCase):
    """Test navigation endpoint returns categories with series."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        
        self.category1 = Category.objects.create(
            name="Pişirme Üniteleri",
            slug="pisirme-uniteleri",
            order=1,
        )
        self.category2 = Category.objects.create(
            name="Soğutma Üniteleri",
            slug="sogutma-uniteleri",
            order=2,
        )
        
        self.series1 = Series.objects.create(
            category=self.category1,
            name="600 Serisi",
            slug="600",
            order=1,
        )
        self.series2 = Series.objects.create(
            category=self.category1,
            name="700 Serisi",
            slug="700",
            order=2,
        )
    
    def test_nav_returns_categories_with_series(self):
        """Nav endpoint returns categories with nested series."""
        url = "/api/v1/nav/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have 2 categories
        self.assertEqual(len(data), 2)
        
        # First category should have 2 series
        cat1 = data[0]
        self.assertEqual(cat1["name"], "Pişirme Üniteleri")
        self.assertEqual(cat1["slug"], "pisirme-uniteleri")
        self.assertEqual(len(cat1["series"]), 2)
        
        # Series should be ordered
        self.assertEqual(cat1["series"][0]["name"], "600 Serisi")
        self.assertEqual(cat1["series"][1]["name"], "700 Serisi")
        
        # Second category should have no series
        cat2 = data[1]
        self.assertEqual(cat2["name"], "Soğutma Üniteleri")
        self.assertEqual(len(cat2["series"]), 0)
    
    def test_nav_is_public(self):
        """Nav endpoint is accessible without authentication."""
        url = "/api/v1/nav/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)


class ProductListEndpointTest(TestCase):
    """Test product list endpoint defaults to active only."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.series = Series.objects.create(
            category=self.category,
            name="Test Series",
            slug="test-series",
        )
        
        # Create products with different statuses
        self.active_product = Product.objects.create(
            name="Active Product",
            slug="active-product",
            title_tr="Aktif Ürün",
            series=self.series,
            status=Product.Status.ACTIVE,
        )
        self.draft_product = Product.objects.create(
            name="Draft Product",
            slug="draft-product",
            title_tr="Taslak Ürün",
            series=self.series,
            status=Product.Status.DRAFT,
        )
        self.archived_product = Product.objects.create(
            name="Archived Product",
            slug="archived-product",
            title_tr="Arşiv Ürün",
            series=self.series,
            status=Product.Status.ARCHIVED,
        )
    
    def test_products_list_defaults_to_active_only(self):
        """Products list endpoint defaults to active status only."""
        url = "/api/v1/products/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should only return active product
        results = data.get("results", data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["slug"], "active-product")
    
    def test_products_list_filter_by_status(self):
        """Products list can filter by status."""
        url = "/api/v1/products/?status=draft"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        results = data.get("results", data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["slug"], "draft-product")
    
    def test_products_list_filter_by_series(self):
        """Products list can filter by series slug."""
        url = "/api/v1/products/?series=test-series"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        results = data.get("results", data)
        self.assertEqual(len(results), 1)  # Only active
    
    def test_products_list_is_public(self):
        """Products list endpoint is accessible without authentication."""
        url = "/api/v1/products/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_products_list_search(self):
        """Products list can search by title."""
        # Create a variant for search
        Variant.objects.create(
            product=self.active_product,
            model_code="GKO6010",
            name_tr="Gazlı Ocak",
        )
        
        url = "/api/v1/products/?search=GKO"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        results = data.get("results", data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["slug"], "active-product")


class ProductDetailEndpointTest(TestCase):
    """Test product detail endpoint."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.series = Series.objects.create(
            category=self.category,
            name="Test Series",
            slug="test-series",
        )
        
        # Create spec keys
        self.spec_key = SpecKey.objects.create(
            slug="goz-adedi",
            label_tr="Göz Adedi",
            value_type="int",
        )
        
        # Create product
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            title_tr="Test Ürün",
            series=self.series,
            status=Product.Status.ACTIVE,
            general_features=["Feature 1", "Feature 2"],
            spec_layout=["goz-adedi"],
        )
        
        # Create variant
        self.variant = Variant.objects.create(
            product=self.product,
            model_code="GKO6010",
            name_tr="Test Variant",
            specs={"goz-adedi": 2},
        )
    
    def test_product_detail_returns_full_data(self):
        """Product detail endpoint returns full catalog page data."""
        url = f"/api/v1/products/{self.product.slug}/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["title_tr"], "Test Ürün")
        self.assertEqual(data["series_slug"], "test-series")
        self.assertEqual(data["category_slug"], "test-category")
        self.assertEqual(data["general_features"], ["Feature 1", "Feature 2"])
        self.assertEqual(data["spec_layout"], ["goz-adedi"])
        
        # Spec keys should be resolved
        self.assertEqual(len(data["spec_keys_resolved"]), 1)
        self.assertEqual(data["spec_keys_resolved"][0]["slug"], "goz-adedi")
        
        # Variants should be included
        self.assertEqual(len(data["variants"]), 1)
        self.assertEqual(data["variants"][0]["model_code"], "GKO6010")
    
    def test_product_detail_404_for_inactive(self):
        """Product detail returns 404 for non-active products."""
        self.product.status = Product.Status.DRAFT
        self.product.save()
        
        url = f"/api/v1/products/{self.product.slug}/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_product_detail_is_public(self):
        """Product detail endpoint is accessible without authentication."""
        url = f"/api/v1/products/{self.product.slug}/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)


class TaxonomyTreeEndpointTest(TestCase):
    """Test taxonomy tree endpoint."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.series = Series.objects.create(
            category=self.category,
            name="Test Series",
            slug="test-series",
        )
        
        self.root_node = TaxonomyNode.objects.create(
            series=self.series,
            name="Root Node",
            slug="root-node",
        )
        self.child_node = TaxonomyNode.objects.create(
            series=self.series,
            name="Child Node",
            slug="child-node",
            parent=self.root_node,
        )
    
    def test_taxonomy_tree_returns_tree(self):
        """Taxonomy tree endpoint returns hierarchical tree."""
        url = "/api/v1/taxonomy/tree/?series=test-series"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have 1 root node
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Root Node")
        
        # Root should have 1 child
        self.assertEqual(len(data[0]["children"]), 1)
        self.assertEqual(data[0]["children"][0]["name"], "Child Node")
    
    def test_taxonomy_tree_requires_series(self):
        """Taxonomy tree endpoint requires series parameter."""
        url = "/api/v1/taxonomy/tree/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 400)


class SpecKeyListEndpointTest(TestCase):
    """Test spec keys list endpoint."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        
        self.spec_key1 = SpecKey.objects.create(
            slug="spectest-key-high",
            label_tr="Key High",
            sort_order=200,
        )
        self.spec_key2 = SpecKey.objects.create(
            slug="spectest-key-low",
            label_tr="Key Low",
            sort_order=100,
        )
    
    def test_spec_keys_ordered_by_sort_order(self):
        """Spec keys are returned ordered by sort_order."""
        url = "/api/v1/spec-keys/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Handle both paginated and non-paginated responses
        results = data.get("results", data) if isinstance(data, dict) else data
        
        # Get slugs in order returned
        slugs = [item["slug"] for item in results]
        
        # Find positions of our test keys
        low_pos = slugs.index("spectest-key-low")
        high_pos = slugs.index("spectest-key-high")
        
        # Low sort_order (100) should come before high sort_order (200)
        self.assertLess(low_pos, high_pos)
