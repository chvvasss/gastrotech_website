"""
Tests for Admin Global Search API.

Tests the GET /api/v1/admin/search endpoint for:
- Authentication requirements
- Role enforcement (admin/editor only)
- Search functionality across entities
- Limit parameter handling
- Empty/short query handling
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import Category, Product, Series, TaxonomyNode, Variant


class AdminSearchTestCase(TestCase):
    """Tests for the admin global search endpoint."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for search tests."""
        # Create users with different roles
        cls.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123",
            role="admin",
        )
        cls.editor_user = User.objects.create_user(
            email="editor@test.com",
            password="testpass123",
            role="editor",
        )
        cls.regular_user = User.objects.create_user(
            email="user@test.com",
            password="testpass123",
            role="user",  # Not admin or editor
        )
        
        # Create test catalog data
        cls.category = Category.objects.create(
            name="Pişirme Üniteleri",
            slug="pisirme-uniteleri",
        )
        
        cls.series = Series.objects.create(
            category=cls.category,
            name="600 Series",
            slug="600-series",
        )
        
        cls.taxonomy_node = TaxonomyNode.objects.create(
            series=cls.series,
            name="Gazlı Ocaklar",
            slug="gazli-ocaklar",
        )
        
        cls.product = Product.objects.create(
            series=cls.series,
            primary_node=cls.taxonomy_node,
            name="Test Gazlı Ocak",
            slug="test-gazli-ocak",
            title_tr="Gazlı Ocak 600",
            status=Product.Status.ACTIVE,
        )
        
        cls.variant = Variant.objects.create(
            product=cls.product,
            model_code="GKO6010",
            name_tr="Gazlı Ocak 6010 Model",
        )
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.url = reverse("api_v1:catalog_admin:search")
    
    def _get_auth_header(self, user):
        """Get JWT auth header for user."""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}
    
    # ==========================================================================
    # Authentication Tests
    # ==========================================================================
    
    def test_requires_authentication(self):
        """Test that unauthenticated requests are rejected."""
        response = self.client.get(self.url, {"q": "test"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_admin_user_can_access(self):
        """Test that admin users can access the search endpoint."""
        response = self.client.get(
            self.url,
            {"q": "ocak"},
            **self._get_auth_header(self.admin_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_editor_user_can_access(self):
        """Test that editor users can access the search endpoint."""
        response = self.client.get(
            self.url,
            {"q": "ocak"},
            **self._get_auth_header(self.editor_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_regular_user_cannot_access(self):
        """Test that regular users are denied access."""
        response = self.client.get(
            self.url,
            {"q": "test"},
            **self._get_auth_header(self.regular_user),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # ==========================================================================
    # Search Functionality Tests
    # ==========================================================================
    
    def test_search_returns_products(self):
        """Test that search returns matching products."""
        response = self.client.get(
            self.url,
            {"q": "Gazlı Ocak"},
            **self._get_auth_header(self.admin_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data["query"], "Gazlı Ocak")
        self.assertIsInstance(data["results"], list)
        
        # Should find the product
        product_results = [r for r in data["results"] if r["type"] == "product"]
        self.assertGreater(len(product_results), 0)
        
        # Check result structure
        result = product_results[0]
        self.assertIn("id", result)
        self.assertIn("title", result)
        self.assertIn("subtitle", result)
        self.assertIn("href", result)
        self.assertIn("score", result)
        self.assertIsInstance(result["score"], float)
    
    def test_search_returns_categories(self):
        """Test that search returns matching categories."""
        response = self.client.get(
            self.url,
            {"q": "Pişirme"},
            **self._get_auth_header(self.admin_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        category_results = [r for r in data["results"] if r["type"] == "category"]
        self.assertGreater(len(category_results), 0)
    
    def test_search_returns_series(self):
        """Test that search returns matching series."""
        response = self.client.get(
            self.url,
            {"q": "600 Series"},
            **self._get_auth_header(self.admin_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        series_results = [r for r in data["results"] if r["type"] == "series"]
        self.assertGreater(len(series_results), 0)
    
    def test_search_returns_taxonomy_nodes(self):
        """Test that search returns matching taxonomy nodes."""
        response = self.client.get(
            self.url,
            {"q": "Gazlı"},
            **self._get_auth_header(self.admin_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        taxonomy_results = [r for r in data["results"] if r["type"] == "taxonomy"]
        self.assertGreater(len(taxonomy_results), 0)
    
    def test_search_returns_variants_by_model_code(self):
        """Test that search returns variants matching model code."""
        response = self.client.get(
            self.url,
            {"q": "GKO6010"},
            **self._get_auth_header(self.admin_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        variant_results = [r for r in data["results"] if r["type"] == "variant"]
        self.assertGreater(len(variant_results), 0)
        
        # Verify the variant is in results
        found = any("GKO6010" in r["title"] for r in variant_results)
        self.assertTrue(found)
    
    def test_results_ordered_by_score(self):
        """Test that results are ordered by score descending."""
        response = self.client.get(
            self.url,
            {"q": "ocak"},
            **self._get_auth_header(self.admin_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        results = data["results"]
        
        if len(results) > 1:
            scores = [r["score"] for r in results]
            self.assertEqual(scores, sorted(scores, reverse=True))
    
    # ==========================================================================
    # Parameter Handling Tests
    # ==========================================================================
    
    def test_empty_query_returns_empty_results(self):
        """Test that empty query returns empty results."""
        response = self.client.get(
            self.url,
            {"q": ""},
            **self._get_auth_header(self.admin_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data["results"], [])
    
    def test_short_query_returns_empty_results(self):
        """Test that query with less than 2 chars returns empty results."""
        response = self.client.get(
            self.url,
            {"q": "a"},
            **self._get_auth_header(self.admin_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data["results"], [])
    
    def test_limit_parameter(self):
        """Test that limit parameter is respected."""
        response = self.client.get(
            self.url,
            {"q": "ocak", "limit": "2"},
            **self._get_auth_header(self.admin_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertLessEqual(len(data["results"]), 2)
    
    def test_limit_max_enforced(self):
        """Test that limit is capped at maximum value."""
        response = self.client.get(
            self.url,
            {"q": "test", "limit": "1000"},  # Over max
            **self._get_auth_header(self.admin_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Should be capped at MAX_LIMIT (50)
        self.assertLessEqual(len(data["results"]), 50)
    
    def test_invalid_limit_uses_default(self):
        """Test that invalid limit uses default value."""
        response = self.client.get(
            self.url,
            {"q": "ocak", "limit": "invalid"},
            **self._get_auth_header(self.admin_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should not error, uses default limit
    
    # ==========================================================================
    # Response Structure Tests
    # ==========================================================================
    
    def test_response_structure(self):
        """Test that response has correct structure."""
        response = self.client.get(
            self.url,
            {"q": "test"},
            **self._get_auth_header(self.admin_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn("query", data)
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)
    
    def test_result_item_structure(self):
        """Test that each result item has required fields."""
        response = self.client.get(
            self.url,
            {"q": "Gazlı"},
            **self._get_auth_header(self.admin_user),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        for result in data["results"]:
            self.assertIn("type", result)
            self.assertIn("id", result)
            self.assertIn("title", result)
            self.assertIn("subtitle", result)  # Can be null
            self.assertIn("href", result)
            self.assertIn("score", result)
            
            # Validate type is one of expected values
            self.assertIn(
                result["type"],
                ["product", "category", "series", "taxonomy", "variant"]
            )
            
            # Validate score is a number
            self.assertIsInstance(result["score"], float)
            self.assertGreaterEqual(result["score"], 0)
            self.assertLessEqual(result["score"], 1)
