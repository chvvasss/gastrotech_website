"""
Tests for admin ViewSets and endpoints.

Tests cover:
- Taxonomy generate-products endpoint
- SpecTemplate apply endpoint
- Product patch validation
- Variant bulk update
"""

from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import (
    Category,
    Product,
    Series,
    SpecKey,
    SpecTemplate,
    TaxonomyNode,
    Variant,
)


class AdminViewSetTestCase(TestCase):
    """Base test case with common setup for admin tests."""
    
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="testpassword123",
            role="admin",
        )
        
        # Create client and authenticate
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Create basic catalog structure
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        
        self.series = Series.objects.create(
            name="600",
            slug="600",
            category=self.category,
        )
        
        # Create taxonomy nodes
        self.parent_node = TaxonomyNode.objects.create(
            series=self.series,
            name="Ocaklar",
            slug="ocaklar",
            order=1,
        )
        
        self.leaf_node = TaxonomyNode.objects.create(
            series=self.series,
            name="Gazlı Ocaklar",
            slug="gazli-ocaklar",
            parent=self.parent_node,
            order=1,
        )
        
        self.leaf_node2 = TaxonomyNode.objects.create(
            series=self.series,
            name="Elektrikli Ocaklar",
            slug="elektrikli-ocaklar",
            parent=self.parent_node,
            order=2,
        )
        
        # Create spec keys
        self.spec_key_1 = SpecKey.objects.create(
            slug="boyutlar",
            label_tr="Boyutlar",
            unit="mm",
            sort_order=1,
        )
        
        self.spec_key_2 = SpecKey.objects.create(
            slug="agirlik",
            label_tr="Ağırlık",
            unit="kg",
            sort_order=2,
        )


class TaxonomyGenerateProductsTest(AdminViewSetTestCase):
    """Tests for POST /api/v1/admin/taxonomy/generate-products/"""
    
    def test_generate_products_from_leaf_nodes(self):
        """Test that products are created for valid leaf nodes."""
        response = self.client.post(
            "/api/v1/admin/taxonomy/generate-products/",
            {
                "series": "600",
                "leaf_slugs": ["gazli-ocaklar", "elektrikli-ocaklar"],
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 2)
        self.assertEqual(response.data["skipped_existing"], 0)
        self.assertEqual(response.data["skipped_non_leaf"], 0)
        self.assertEqual(len(response.data["created_slugs"]), 2)
        
        # Verify products were created
        self.assertTrue(
            Product.objects.filter(primary_node=self.leaf_node).exists()
        )
        self.assertTrue(
            Product.objects.filter(primary_node=self.leaf_node2).exists()
        )
    
    def test_non_leaf_nodes_skipped(self):
        """Test that non-leaf nodes are skipped."""
        response = self.client.post(
            "/api/v1/admin/taxonomy/generate-products/",
            {
                "series": "600",
                "leaf_slugs": ["ocaklar"],  # Parent node, not a leaf
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 0)
        self.assertEqual(response.data["skipped_non_leaf"], 1)
    
    def test_existing_products_skipped(self):
        """Test that nodes with existing products are skipped."""
        # First create a product for the node
        Product.objects.create(
            name="Existing Product",
            slug="existing-product",
            title_tr="Existing Product",
            series=self.series,
            primary_node=self.leaf_node,
        )
        
        response = self.client.post(
            "/api/v1/admin/taxonomy/generate-products/",
            {
                "series": "600",
                "leaf_slugs": ["gazli-ocaklar"],
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 0)
        self.assertEqual(response.data["skipped_existing"], 1)
    
    def test_unknown_slug_returns_error(self):
        """Test that unknown node slugs are reported in errors."""
        response = self.client.post(
            "/api/v1/admin/taxonomy/generate-products/",
            {
                "series": "600",
                "leaf_slugs": ["unknown-node"],
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 0)
        self.assertEqual(len(response.data["errors"]), 1)
        self.assertEqual(response.data["errors"][0]["slug"], "unknown-node")
    
    def test_invalid_series_returns_404(self):
        """Test that invalid series returns 404."""
        response = self.client.post(
            "/api/v1/admin/taxonomy/generate-products/",
            {
                "series": "nonexistent-series",
                "leaf_slugs": ["gazli-ocaklar"],
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SpecTemplateApplyTest(AdminViewSetTestCase):
    """Tests for POST /api/v1/admin/products/{slug}/apply-template/"""
    
    def setUp(self):
        super().setUp()
        
        # Create a product
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            title_tr="Test Product",
            series=self.series,
        )
        
        # Create a spec template
        self.template = SpecTemplate.objects.create(
            name="Test Template",
            spec_layout=["boyutlar", "agirlik"],
            default_general_features=["Feature 1", "Feature 2"],
            default_notes=["Note 1"],
        )
    
    def test_apply_template_sets_spec_layout(self):
        """Test that applying template sets spec_layout on product."""
        response = self.client.post(
            f"/api/v1/admin/products/{self.product.slug}/apply-template/",
            {
                "template_id": str(self.template.id),
                "overwrite": False,
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("spec_layout", response.data["updated_fields"])
        
        # Refresh product and verify
        self.product.refresh_from_db()
        self.assertEqual(self.product.spec_layout, ["boyutlar", "agirlik"])
        self.assertEqual(self.product.general_features, ["Feature 1", "Feature 2"])
    
    def test_apply_template_overwrite_false_does_not_replace(self):
        """Test that overwrite=False does not replace existing values."""
        # Set existing spec_layout
        self.product.spec_layout = ["existing-key"]
        self.product.save()
        
        response = self.client.post(
            f"/api/v1/admin/products/{self.product.slug}/apply-template/",
            {
                "template_id": str(self.template.id),
                "overwrite": False,
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # spec_layout should NOT be in updated_fields (not overwritten)
        self.assertNotIn("spec_layout", response.data["updated_fields"])
        
        # Verify original value preserved
        self.product.refresh_from_db()
        self.assertEqual(self.product.spec_layout, ["existing-key"])
    
    def test_apply_template_overwrite_true_replaces(self):
        """Test that overwrite=True replaces existing values."""
        # Set existing spec_layout
        self.product.spec_layout = ["existing-key"]
        self.product.save()
        
        response = self.client.post(
            f"/api/v1/admin/products/{self.product.slug}/apply-template/",
            {
                "template_id": str(self.template.id),
                "overwrite": True,
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("spec_layout", response.data["updated_fields"])
        
        # Verify replaced
        self.product.refresh_from_db()
        self.assertEqual(self.product.spec_layout, ["boyutlar", "agirlik"])
    
    def test_apply_template_nonexistent_returns_404(self):
        """Test that nonexistent template returns 404."""
        import uuid
        response = self.client.post(
            f"/api/v1/admin/products/{self.product.slug}/apply-template/",
            {
                "template_id": str(uuid.uuid4()),
                "overwrite": False,
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProductPatchValidationTest(AdminViewSetTestCase):
    """Tests for PATCH /api/v1/admin/products/{slug}/"""
    
    def setUp(self):
        super().setUp()
        
        # Create a product
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            title_tr="Test Product",
            series=self.series,
        )
    
    def test_patch_title_tr_works(self):
        """Test that patching title_tr works."""
        response = self.client.patch(
            f"/api/v1/admin/products/{self.product.slug}/",
            {"title_tr": "Updated Title"},
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.title_tr, "Updated Title")
    
    def test_patch_status_works(self):
        """Test that patching status works."""
        response = self.client.patch(
            f"/api/v1/admin/products/{self.product.slug}/",
            {"status": "active"},
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, "active")
    
    def test_patch_invalid_spec_layout_rejected(self):
        """Test that invalid spec_layout slugs are rejected."""
        response = self.client.patch(
            f"/api/v1/admin/products/{self.product.slug}/",
            {"spec_layout": ["invalid-slug", "another-invalid"]},
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("spec_layout", response.data)
    
    def test_patch_valid_spec_layout_accepted(self):
        """Test that valid spec_layout slugs are accepted."""
        response = self.client.patch(
            f"/api/v1/admin/products/{self.product.slug}/",
            {"spec_layout": ["boyutlar", "agirlik"]},
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.spec_layout, ["boyutlar", "agirlik"])
    
    def test_patch_general_features_works(self):
        """Test that patching general_features works."""
        response = self.client.patch(
            f"/api/v1/admin/products/{self.product.slug}/",
            {"general_features": ["Feature A", "Feature B"]},
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.general_features, ["Feature A", "Feature B"])
    
    def test_product_lookup_by_uuid_works(self):
        """Test that product can be looked up by UUID."""
        response = self.client.patch(
            f"/api/v1/admin/products/{self.product.id}/",
            {"title_tr": "Updated via UUID"},
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.title_tr, "Updated via UUID")


class VariantBulkUpdateTest(AdminViewSetTestCase):
    """Tests for POST /api/v1/admin/variants/bulk/"""
    
    def setUp(self):
        super().setUp()
        
        # Create a product
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            title_tr="Test Product",
            series=self.series,
        )
        
        # Create variants
        self.variant1 = Variant.objects.create(
            product=self.product,
            model_code="GKO6010",
            name_tr="Variant 1",
            dimensions="400x600x280",
            weight_kg=Decimal("50.000"),
            list_price=Decimal("1000.00"),
        )
        
        self.variant2 = Variant.objects.create(
            product=self.product,
            model_code="GKO6020",
            name_tr="Variant 2",
            dimensions="600x600x280",
            weight_kg=Decimal("75.000"),
            list_price=Decimal("1500.00"),
        )
    
    def test_bulk_update_multiple_variants(self):
        """Test that bulk update updates multiple variants."""
        response = self.client.post(
            "/api/v1/admin/variants/bulk/",
            {
                "updates": [
                    {"model_code": "GKO6010", "name_tr": "Updated Variant 1", "list_price": "1100.00"},
                    {"model_code": "GKO6020", "dimensions": "800x600x280"},
                ]
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated"], 2)
        
        # Verify updates
        self.variant1.refresh_from_db()
        self.assertEqual(self.variant1.name_tr, "Updated Variant 1")
        self.assertEqual(self.variant1.list_price, Decimal("1100.00"))
        
        self.variant2.refresh_from_db()
        self.assertEqual(self.variant2.dimensions, "800x600x280")
    
    def test_bulk_update_invalid_model_code_tracked(self):
        """Test that invalid model_code is tracked in not_found."""
        response = self.client.post(
            "/api/v1/admin/variants/bulk/",
            {
                "updates": [
                    {"model_code": "INVALID", "name_tr": "Not Found"},
                    {"model_code": "GKO6010", "name_tr": "Valid Update"},
                ]
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated"], 1)
        self.assertIn("INVALID", response.data["not_found"])
    
    def test_bulk_update_specs(self):
        """Test that specs JSON field can be updated."""
        response = self.client.post(
            "/api/v1/admin/variants/bulk/",
            {
                "updates": [
                    {
                        "model_code": "GKO6010",
                        "specs": {"power": "5kW", "burners": 2},
                    },
                ]
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated"], 1)
        
        self.variant1.refresh_from_db()
        self.assertEqual(self.variant1.specs["power"], "5kW")
        self.assertEqual(self.variant1.specs["burners"], 2)


class AdminViewSetsCRUDTest(AdminViewSetTestCase):
    """Tests for CRUD operations on admin viewsets."""
    
    def test_list_categories(self):
        """Test listing categories."""
        response = self.client.get("/api/v1/admin/categories/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertTrue(len(response.data) >= 1)
    
    def test_list_series(self):
        """Test listing series."""
        response = self.client.get("/api/v1/admin/series/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_list_taxonomy_nodes(self):
        """Test listing taxonomy nodes."""
        response = self.client.get("/api/v1/admin/taxonomy-nodes/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_list_taxonomy_nodes_by_series(self):
        """Test filtering taxonomy nodes by series."""
        response = self.client.get("/api/v1/admin/taxonomy-nodes/?series=600")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for node in response.data:
            self.assertEqual(node["series"], str(self.series.id))
    
    def test_list_taxonomy_nodes_leaf_only(self):
        """Test filtering to leaf nodes only."""
        response = self.client.get("/api/v1/admin/taxonomy-nodes/?leaf_only=true")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for node in response.data:
            self.assertTrue(node["is_leaf"])
    
    def test_list_spec_templates(self):
        """Test listing spec templates."""
        response = self.client.get("/api/v1/admin/spec-templates/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_list_spec_keys(self):
        """Test listing spec keys."""
        response = self.client.get("/api/v1/admin/spec-keys/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_list_products(self):
        """Test listing products."""
        # Create a product first
        Product.objects.create(
            name="Test Product",
            slug="test-product",
            title_tr="Test Product",
            series=self.series,
        )
        
        response = self.client.get("/api/v1/admin/products/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_list_variants(self):
        """Test listing variants."""
        response = self.client.get("/api/v1/admin/variants/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_create_product(self):
        """Test creating a product."""
        response = self.client.post(
            "/api/v1/admin/products/",
            {
                "name": "New Product",
                "title_tr": "Yeni Ürün",
                "series_slug": "600",
                "status": "draft",
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title_tr"], "Yeni Ürün")
        self.assertTrue(Product.objects.filter(title_tr="Yeni Ürün").exists())
    
    def test_create_variant(self):
        """Test creating a variant."""
        product = Product.objects.create(
            name="Test Product",
            slug="test-product-for-variant",
            title_tr="Test Product",
            series=self.series,
        )
        
        response = self.client.post(
            "/api/v1/admin/variants/",
            {
                "product_slug": product.slug,
                "model_code": "NEW001",
                "name_tr": "New Variant",
                "dimensions": "500x500x300",
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["model_code"], "NEW001")
        self.assertTrue(Variant.objects.filter(model_code="NEW001").exists())


class AdminAuthenticationTest(TestCase):
    """Tests for admin endpoint authentication."""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_unauthenticated_request_rejected(self):
        """Test that unauthenticated requests are rejected."""
        response = self.client.get("/api/v1/admin/categories/")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_non_admin_user_rejected(self):
        """Test that non-admin users are rejected."""
        # Create a regular user (no role or role != admin/editor)
        regular_user = User.objects.create_user(
            email="regular@test.com",
            password="testpassword123",
            role=None,  # No role
        )
        
        self.client.force_authenticate(user=regular_user)
        response = self.client.get("/api/v1/admin/categories/")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_editor_user_allowed(self):
        """Test that editor users are allowed."""
        editor_user = User.objects.create_user(
            email="editor@test.com",
            password="testpassword123",
            role="editor",
        )
        
        self.client.force_authenticate(user=editor_user)
        response = self.client.get("/api/v1/admin/categories/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CapabilitiesEndpointsExistTest(TestCase):
    """Test that capability check endpoints return not-404."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="testpassword123",
            role="admin",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_products_endpoint_exists(self):
        """Test that products list endpoint exists."""
        response = self.client.options("/api/v1/admin/products/")
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_variants_endpoint_exists(self):
        """Test that variants list endpoint exists."""
        response = self.client.options("/api/v1/admin/variants/")
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_spec_templates_endpoint_exists(self):
        """Test that spec-templates list endpoint exists."""
        response = self.client.options("/api/v1/admin/spec-templates/")
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_variants_bulk_endpoint_exists(self):
        """Test that variants bulk endpoint exists."""
        response = self.client.options("/api/v1/admin/variants/bulk/")
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_generate_products_endpoint_exists(self):
        """Test that taxonomy generate-products endpoint exists."""
        response = self.client.options("/api/v1/admin/taxonomy/generate-products/")
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class StatsAPITest(AdminViewSetTestCase):
    """Tests for GET /api/v1/admin/stats/"""
    
    def test_stats_returns_required_keys(self):
        """Test that stats endpoint returns all required keys."""
        response = self.client.get("/api/v1/admin/stats/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check catalog metrics
        self.assertIn("categories_total", response.data)
        self.assertIn("series_total", response.data)
        self.assertIn("taxonomy_nodes_total", response.data)
        self.assertIn("products_total", response.data)
        self.assertIn("products_active", response.data)
        self.assertIn("products_draft", response.data)
        self.assertIn("products_archived", response.data)
        self.assertIn("variants_total", response.data)
        
        # Check media metrics
        self.assertIn("media_total", response.data)
        self.assertIn("media_unreferenced_total", response.data)
        
        # Check inquiry metrics
        self.assertIn("inquiries_total", response.data)
        self.assertIn("inquiries_new_range", response.data)
        self.assertIn("inquiries_open", response.data)
        self.assertIn("inquiries_closed", response.data)
        self.assertIn("inquiry_items_total", response.data)
        
        # Check chart data
        self.assertIn("inquiries_by_day", response.data)
        self.assertIn("products_by_status", response.data)
        self.assertIn("top_requested_variants", response.data)
        
        # Check activity lists
        self.assertIn("recently_updated_products", response.data)
        self.assertIn("recently_updated_inquiries", response.data)
    
    def test_stats_counts_are_correct(self):
        """Test that stats counts match actual data."""
        # Create some products
        Product.objects.create(
            name="Product 1", slug="product-1", title_tr="Product 1",
            series=self.series, status="active"
        )
        Product.objects.create(
            name="Product 2", slug="product-2", title_tr="Product 2",
            series=self.series, status="draft"
        )
        
        response = self.client.get("/api/v1/admin/stats/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["categories_total"], 1)
        self.assertEqual(response.data["series_total"], 1)
        self.assertEqual(response.data["products_total"], 2)
        self.assertEqual(response.data["products_active"], 1)
        self.assertEqual(response.data["products_draft"], 1)
    
    def test_stats_range_parameter(self):
        """Test that range parameter affects results."""
        response_7d = self.client.get("/api/v1/admin/stats/?range=7d")
        response_30d = self.client.get("/api/v1/admin/stats/?range=30d")
        
        self.assertEqual(response_7d.status_code, status.HTTP_200_OK)
        self.assertEqual(response_30d.status_code, status.HTTP_200_OK)
        
        # Both should have the same structure
        self.assertIn("inquiries_new_range", response_7d.data)
        self.assertIn("inquiries_new_range", response_30d.data)
    
    def test_stats_requires_authentication(self):
        """Test that stats endpoint requires authentication."""
        self.client.logout()
        response = self.client.get("/api/v1/admin/stats/")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaxonomyDryRunTest(AdminViewSetTestCase):
    """Tests for dry_run mode in taxonomy generate-products."""
    
    def test_dry_run_returns_preview_without_creating(self):
        """Test that dry_run returns preview but doesn't create products."""
        initial_count = Product.objects.count()
        
        response = self.client.post(
            "/api/v1/admin/taxonomy/generate-products/",
            {
                "series": "600",
                "leaf_slugs": ["gazli-ocaklar", "elektrikli-ocaklar"],
                "dry_run": True,
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["dry_run"])
        self.assertEqual(response.data["created"], 2)
        self.assertEqual(len(response.data["preview"]), 2)
        
        # Verify NO products were actually created
        self.assertEqual(Product.objects.count(), initial_count)
    
    def test_dry_run_preview_shows_correct_status(self):
        """Test that preview correctly identifies existing vs new products."""
        # Create one product
        Product.objects.create(
            name="Existing",
            slug="600-serisi-gazli-ocaklar",
            title_tr="Existing",
            series=self.series,
            primary_node=self.leaf_node,
        )
        
        response = self.client.post(
            "/api/v1/admin/taxonomy/generate-products/",
            {
                "series": "600",
                "leaf_slugs": ["gazli-ocaklar", "elektrikli-ocaklar"],
                "dry_run": True,
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # One should show "exists", one should show "will_create"
        exists_items = [p for p in response.data["preview"] if p["status"] == "exists"]
        create_items = [p for p in response.data["preview"] if p["status"] == "will_create"]
        
        self.assertEqual(len(exists_items), 1)
        self.assertEqual(len(create_items), 1)
    
    def test_status_parameter_affects_created_products(self):
        """Test that status parameter sets correct status on created products."""
        response = self.client.post(
            "/api/v1/admin/taxonomy/generate-products/",
            {
                "series": "600",
                "leaf_slugs": ["gazli-ocaklar"],
                "dry_run": False,
                "status": "draft",
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 1)
        
        # Verify product was created with draft status
        product = Product.objects.get(primary_node=self.leaf_node)
        self.assertEqual(product.status, "draft")


class VariantCRUDTest(AdminViewSetTestCase):
    """Tests for variant CRUD operations."""
    
    def setUp(self):
        super().setUp()
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            title_tr="Test Product",
            series=self.series,
        )
    
    def test_create_variant(self):
        """Test creating a variant."""
        response = self.client.post(
            "/api/v1/admin/variants/",
            {
                "product_slug": self.product.slug,
                "model_code": "TEST001",
                "name_tr": "Test Variant",
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["model_code"], "TEST001")
    
    def test_patch_variant(self):
        """Test patching a variant."""
        variant = Variant.objects.create(
            product=self.product,
            model_code="PATCH001",
            name_tr="Original Name",
        )
        
        response = self.client.patch(
            f"/api/v1/admin/variants/{variant.model_code}/",
            {"name_tr": "Updated Name"},
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        variant.refresh_from_db()
        self.assertEqual(variant.name_tr, "Updated Name")
    
    def test_delete_variant(self):
        """Test deleting a variant."""
        variant = Variant.objects.create(
            product=self.product,
            model_code="DELETE001",
            name_tr="To Delete",
        )
        
        response = self.client.delete(f"/api/v1/admin/variants/{variant.model_code}/")
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Variant.objects.filter(model_code="DELETE001").exists())
