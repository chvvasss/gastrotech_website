"""
Tests for admin leaf taxonomy product generation.
"""

from django.test import TestCase

from apps.catalog.models import (
    Category,
    Product,
    ProductNode,
    Series,
    SpecTemplate,
    TaxonomyNode,
)
from apps.catalog.services import (
    create_product_for_leaf_node,
    generate_product_slug,
    generate_products_from_leaf_nodes,
)


class LeafGenerationTest(TestCase):
    """Test leaf taxonomy product generation."""
    
    def setUp(self):
        """Create test data."""
        self.category = Category.objects.create(
            name="Pişirme Üniteleri",
            slug="pisirme-uniteleri",
        )
        self.series = Series.objects.create(
            category=self.category,
            name="600 Serisi",
            slug="600",
        )
        
        # Create taxonomy structure
        # Parent: Ocaklar
        self.parent_node = TaxonomyNode.objects.create(
            series=self.series,
            name="Ocaklar",
            slug="ocaklar",
            order=1,
        )
        
        # Leaf: Gazlı Ocaklar (under Ocaklar)
        self.leaf_node = TaxonomyNode.objects.create(
            series=self.series,
            parent=self.parent_node,
            name="Gazlı Ocaklar",
            slug="gazli-ocaklar",
            order=1,
        )
        
        # Another leaf for testing
        self.leaf_node2 = TaxonomyNode.objects.create(
            series=self.series,
            parent=self.parent_node,
            name="Elektrikli Ocaklar",
            slug="elektrikli-ocaklar",
            order=2,
        )
    
    def test_create_product_for_leaf_node(self):
        """Test that a product is created for a leaf node."""
        product = create_product_for_leaf_node(self.leaf_node)
        
        self.assertIsNotNone(product)
        self.assertEqual(product.series, self.series)
        self.assertEqual(product.primary_node, self.leaf_node)
        self.assertEqual(product.title_tr, "Gazlı Ocaklar")
        self.assertEqual(product.status, Product.Status.ACTIVE)
    
    def test_product_slug_for_numeric_series(self):
        """Test slug generation for numeric series (e.g., 600)."""
        slug = generate_product_slug(self.series, self.leaf_node)
        
        # Should be "600-serisi-gazli-ocaklar"
        self.assertEqual(slug, "600-serisi-gazli-ocaklar")
    
    def test_product_slug_for_non_numeric_series(self):
        """Test slug generation for non-numeric series."""
        series = Series.objects.create(
            category=self.category,
            name="Drop-in",
            slug="drop-in",
        )
        node = TaxonomyNode.objects.create(
            series=series,
            name="Test Node",
            slug="test-node",
        )
        
        slug = generate_product_slug(series, node)
        
        # Should be "drop-in-test-node"
        self.assertEqual(slug, "drop-in-test-node")
    
    def test_product_nodes_include_ancestors(self):
        """Test that ProductNode relationships include ancestors."""
        product = create_product_for_leaf_node(self.leaf_node)
        
        # Should have both leaf node and parent node
        nodes = list(product.nodes.all())
        node_slugs = [n.slug for n in nodes]
        
        self.assertIn("gazli-ocaklar", node_slugs)
        self.assertIn("ocaklar", node_slugs)
    
    def test_generate_skips_non_leaf_nodes(self):
        """Test that non-leaf nodes are skipped."""
        # parent_node has children, so it's not a leaf
        nodes = TaxonomyNode.objects.filter(pk=self.parent_node.pk)
        
        result = generate_products_from_leaf_nodes(nodes)
        
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["skipped_non_leaf"], 1)
    
    def test_generate_skips_existing_products(self):
        """Test that existing products are skipped."""
        # Create a product first
        Product.objects.create(
            name="Existing Product",
            slug="existing-product",
            title_tr="Existing",
            series=self.series,
            primary_node=self.leaf_node,
        )
        
        nodes = TaxonomyNode.objects.filter(pk=self.leaf_node.pk)
        
        result = generate_products_from_leaf_nodes(nodes)
        
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["skipped_existing"], 1)
    
    def test_generate_creates_multiple_products(self):
        """Test generating products for multiple leaf nodes."""
        nodes = TaxonomyNode.objects.filter(
            pk__in=[self.leaf_node.pk, self.leaf_node2.pk]
        )
        
        result = generate_products_from_leaf_nodes(nodes)
        
        self.assertEqual(result["created"], 2)
        
        # Verify products were created
        product1 = Product.objects.get(primary_node=self.leaf_node)
        product2 = Product.objects.get(primary_node=self.leaf_node2)
        
        self.assertEqual(product1.title_tr, "Gazlı Ocaklar")
        self.assertEqual(product2.title_tr, "Elektrikli Ocaklar")
    
    def test_spec_template_applied_when_matching(self):
        """Test that SpecTemplate is applied when matching."""
        # Create a template for this series
        template = SpecTemplate.objects.create(
            name="600 Series Template",
            spec_layout=["goz-adedi", "guc-kw"],
            default_general_features=["Feature 1", "Feature 2"],
            applies_to_series=self.series,
        )
        
        product = create_product_for_leaf_node(self.leaf_node)
        
        # Template should be applied
        self.assertEqual(product.spec_layout, ["goz-adedi", "guc-kw"])
        self.assertEqual(product.general_features, ["Feature 1", "Feature 2"])
    
    def test_spec_template_with_parent_slug_takes_priority(self):
        """Test that template with parent slug match takes priority."""
        # General template for series
        template1 = SpecTemplate.objects.create(
            name="600 Series General",
            spec_layout=["generic-spec"],
            applies_to_series=self.series,
        )
        
        # Specific template for parent "ocaklar"
        template2 = SpecTemplate.objects.create(
            name="600 Ocaklar Template",
            spec_layout=["goz-adedi", "guc-kw"],
            applies_to_series=self.series,
            applies_to_parent_taxonomy_slug="ocaklar",
        )
        
        product = create_product_for_leaf_node(self.leaf_node)
        
        # The more specific template should be applied
        self.assertEqual(product.spec_layout, ["goz-adedi", "guc-kw"])
    
    def test_slug_uniqueness_ensured(self):
        """Test that slug uniqueness is enforced."""
        # Create first product
        product1 = create_product_for_leaf_node(self.leaf_node)
        slug1 = product1.slug
        
        # Delete product
        product1.delete()
        
        # Create new category and series with same slug pattern
        another_category = Category.objects.create(
            name="Another Category",
            slug="another-category",
        )
        another_series = Series.objects.create(
            category=another_category,
            name="600 Series",
            slug="600",
        )
        another_node = TaxonomyNode.objects.create(
            series=another_series,
            name="Gazlı Ocaklar",
            slug="gazli-ocaklar",
        )
        
        # Create products - should generate unique slugs
        product2 = create_product_for_leaf_node(self.leaf_node)
        product3 = create_product_for_leaf_node(another_node)
        
        # Both should succeed and have unique slugs
        self.assertIsNotNone(product2)
        self.assertIsNotNone(product3)
        self.assertNotEqual(product2.slug, product3.slug)
