"""
Tests for PLP (Product Listing Page) endpoint.

Tests faceted filtering, sorting, and pagination functionality.
"""

from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Brand, Category, Product, Series, Variant


class PLPEndpointTests(TestCase):
    """Tests for /api/v1/plp/ endpoint."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create category hierarchy
        self.root = Category.objects.create(name="Pişirme Ekipmanları", slug="pisirme-ekipmanlari")
        self.child1 = Category.objects.create(name="Ocaklar", slug="ocaklar", parent=self.root)
        self.child2 = Category.objects.create(name="Fırınlar", slug="firinlar", parent=self.root)
        
        # Create brands
        self.brand_vital = Brand.objects.create(name="VITAL", slug="vital", is_active=True)
        self.brand_cgf = Brand.objects.create(name="CGF", slug="cgf", is_active=True)
        self.brand_inactive = Brand.objects.create(name="Inactive", slug="inactive", is_active=False)
        
        # Create series
        self.series_ocak = Series.objects.create(name="Gazlı Ocaklar", slug="gazli-ocaklar", category=self.child1)
        self.series_firin = Series.objects.create(name="Konveksiyonel Fırınlar", slug="konveksiyonel-firinlar", category=self.child2)
        
        # Create products
        self.product1 = Product.objects.create(
            name="Gazlı Ocak 6010",
            slug="gazli-ocak-6010",
            title_tr="Gazlı Ocak 6010",
            series=self.series_ocak,
            category=self.child1,
            brand=self.brand_vital,
            status="active",
        )
        self.product2 = Product.objects.create(
            name="Gazlı Ocak 6020",
            slug="gazli-ocak-6020",
            title_tr="Gazlı Ocak 6020",
            series=self.series_ocak,
            category=self.child1,
            brand=self.brand_cgf,
            status="active",
        )
        self.product3 = Product.objects.create(
            name="Konveksiyonel Fırın",
            slug="konveksiyonel-firin",
            title_tr="Konveksiyonel Fırın",
            series=self.series_firin,
            category=self.child2,
            brand=self.brand_vital,
            status="active",
        )
        self.product_draft = Product.objects.create(
            name="Draft Product",
            slug="draft-product",
            title_tr="Draft Product",
            series=self.series_ocak,
            category=self.child1,
            brand=self.brand_vital,
            status="draft",
        )
        
        # Create variants with prices and stock
        Variant.objects.create(
            product=self.product1,
            model_code="GKO6010",
            name_tr="Gazlı Ocak 6010",
            list_price=Decimal("15000.00"),
            stock_qty=5,
        )
        Variant.objects.create(
            product=self.product2,
            model_code="GKO6020",
            name_tr="Gazlı Ocak 6020",
            list_price=Decimal("25000.00"),
            stock_qty=0,  # Out of stock
        )
        Variant.objects.create(
            product=self.product3,
            model_code="KF001",
            name_tr="Konveksiyonel Fırın",
            list_price=Decimal("50000.00"),
            stock_qty=None,  # Unlimited stock
        )
    
    def test_plp_requires_category(self):
        """Test that category parameter is required."""
        response = self.client.get("/api/v1/plp/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "MISSING_CATEGORY")
    
    def test_plp_returns_404_for_invalid_category(self):
        """Test 404 for non-existent category."""
        response = self.client.get("/api/v1/plp/?category=nonexistent")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "CATEGORY_NOT_FOUND")
    
    def test_plp_returns_products_in_category_subtree(self):
        """Test that products from all descendant categories are returned."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return all 3 active products (draft excluded)
        self.assertEqual(data["pagination"]["total"], 3)
        self.assertEqual(len(data["products"]), 3)
        
        # Verify product slugs
        product_slugs = [p["slug"] for p in data["products"]]
        self.assertIn("gazli-ocak-6010", product_slugs)
        self.assertIn("gazli-ocak-6020", product_slugs)
        self.assertIn("konveksiyonel-firin", product_slugs)
        self.assertNotIn("draft-product", product_slugs)
    
    def test_plp_returns_products_in_leaf_category(self):
        """Test filtering to a specific leaf category."""
        response = self.client.get("/api/v1/plp/?category=ocaklar")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return only 2 products from Ocaklar
        self.assertEqual(data["pagination"]["total"], 2)
        product_slugs = [p["slug"] for p in data["products"]]
        self.assertIn("gazli-ocak-6010", product_slugs)
        self.assertIn("gazli-ocak-6020", product_slugs)
        self.assertNotIn("konveksiyonel-firin", product_slugs)
    
    def test_plp_brand_filter(self):
        """Test brand filtering."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari&brands=vital")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return only VITAL products
        self.assertEqual(data["pagination"]["total"], 2)
        for product in data["products"]:
            self.assertEqual(product["brand"]["slug"], "vital")
    
    def test_plp_multiple_brands_filter(self):
        """Test filtering by multiple brands (OR logic)."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari&brands=vital,cgf")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return all 3 products
        self.assertEqual(data["pagination"]["total"], 3)
    
    def test_plp_brand_facets(self):
        """Test that brand facets have correct counts."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        brand_facets = {b["slug"]: b for b in data["facets"]["brands"]}
        
        # VITAL has 2 products
        self.assertEqual(brand_facets["vital"]["count"], 2)
        # CGF has 1 product
        self.assertEqual(brand_facets["cgf"]["count"], 1)
        # Inactive brand should not appear
        self.assertNotIn("inactive", brand_facets)
    
    def test_plp_price_facet(self):
        """Test price range facet."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        price_facet = data["facets"]["price"]
        self.assertEqual(price_facet["min"], 15000.0)
        self.assertEqual(price_facet["max"], 50000.0)
    
    def test_plp_price_filter_min(self):
        """Test minimum price filtering."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari&price_min=20000")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should exclude product1 (15000)
        self.assertEqual(data["pagination"]["total"], 2)
        product_slugs = [p["slug"] for p in data["products"]]
        self.assertNotIn("gazli-ocak-6010", product_slugs)
    
    def test_plp_price_filter_max(self):
        """Test maximum price filtering."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari&price_max=30000")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should exclude product3 (50000)
        self.assertEqual(data["pagination"]["total"], 2)
        product_slugs = [p["slug"] for p in data["products"]]
        self.assertNotIn("konveksiyonel-firin", product_slugs)
    
    def test_plp_in_stock_filter(self):
        """Test in-stock filtering."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari&in_stock=true")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should exclude product2 (stock_qty=0)
        self.assertEqual(data["pagination"]["total"], 2)
        product_slugs = [p["slug"] for p in data["products"]]
        self.assertIn("gazli-ocak-6010", product_slugs)  # stock_qty=5
        self.assertIn("konveksiyonel-firin", product_slugs)  # stock_qty=None (unlimited)
        self.assertNotIn("gazli-ocak-6020", product_slugs)  # stock_qty=0
    
    def test_plp_sorting_name_asc(self):
        """Test sorting by name ascending."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari&sort=name_asc")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        titles = [p["title_tr"] for p in data["products"]]
        self.assertEqual(titles, sorted(titles))
    
    def test_plp_sorting_name_desc(self):
        """Test sorting by name descending."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari&sort=name_desc")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        titles = [p["title_tr"] for p in data["products"]]
        self.assertEqual(titles, sorted(titles, reverse=True))
    
    def test_plp_pagination(self):
        """Test pagination."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari&page_size=2&page=1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(len(data["products"]), 2)
        self.assertEqual(data["pagination"]["total"], 3)
        self.assertEqual(data["pagination"]["page"], 1)
        self.assertEqual(data["pagination"]["page_size"], 2)
        self.assertEqual(data["pagination"]["total_pages"], 2)
        self.assertTrue(data["pagination"]["has_next"])
        self.assertFalse(data["pagination"]["has_prev"])
        
        # Get page 2
        response2 = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari&page_size=2&page=2")
        data2 = response2.json()
        
        self.assertEqual(len(data2["products"]), 1)
        self.assertEqual(data2["pagination"]["page"], 2)
        self.assertFalse(data2["pagination"]["has_next"])
        self.assertTrue(data2["pagination"]["has_prev"])
    
    def test_plp_selected_filters(self):
        """Test selected_filters response."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari&brands=vital&price_min=10000&in_stock=true")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        selected = data["selected_filters"]
        self.assertEqual(selected["brands"], ["vital"])
        self.assertEqual(selected["price_min"], 10000.0)
        self.assertIsNone(selected["price_max"])
        self.assertTrue(selected["in_stock"])
    
    def test_plp_category_facets(self):
        """Test subcategory facets."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        cat_facets = {c["slug"]: c for c in data["facets"]["categories"]}
        
        # Ocaklar has 2 products
        self.assertEqual(cat_facets["ocaklar"]["count"], 2)
        # Fırınlar has 1 product
        self.assertEqual(cat_facets["firinlar"]["count"], 1)
    
    def test_plp_sort_options_returned(self):
        """Test that sort options are included in response."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("sort_options", data)
        sort_keys = [opt["key"] for opt in data["sort_options"]]
        self.assertIn("name_asc", sort_keys)
        self.assertIn("name_desc", sort_keys)
        self.assertIn("price_asc", sort_keys)
        self.assertIn("price_desc", sort_keys)
        self.assertIn("newest", sort_keys)
    
    def test_plp_product_has_price_info(self):
        """Test that products include price info from variants."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        for product in data["products"]:
            self.assertIn("price", product)
            if product["price"]:
                self.assertIn("min", product["price"])
                self.assertIn("max", product["price"])
                self.assertIn("currency", product["price"])
    
    def test_plp_max_page_size_enforced(self):
        """Test that page_size is capped at MAX_PAGE_SIZE."""
        response = self.client.get("/api/v1/plp/?category=pisirme-ekipmanlari&page_size=500")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should be capped at 100
        self.assertLessEqual(data["pagination"]["page_size"], 100)
