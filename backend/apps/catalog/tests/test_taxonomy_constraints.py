"""
Tests for taxonomy node constraints and product-node relationships.
"""

from django.db import IntegrityError
from django.test import TestCase

from apps.catalog.models import (
    Category,
    Product,
    ProductNode,
    Series,
    TaxonomyNode,
)


class TaxonomyNodeConstraintsTest(TestCase):
    """Test taxonomy node uniqueness constraints."""
    
    def setUp(self):
        """Create test data."""
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.series = Series.objects.create(
            category=self.category,
            name="Test Series",
            slug="test-series",
        )
    
    def test_taxonomy_slug_unique_within_series_and_parent(self):
        """Taxonomy node slugs must be unique within series + parent (non-null parent)."""
        # Create root node
        root = TaxonomyNode.objects.create(
            series=self.series,
            name="Root Node",
            slug="root",
            parent=None,
        )
        
        # Create child node under root
        TaxonomyNode.objects.create(
            series=self.series,
            name="Child Node",
            slug="child-slug",
            parent=root,
        )
        
        # Same slug under same parent should fail
        from django.db import transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TaxonomyNode.objects.create(
                    series=self.series,
                    name="Another Child",
                    slug="child-slug",
                    parent=root,
                )
    
    def test_same_slug_allowed_under_different_parents(self):
        """Same slug can be used under different parents in same series."""
        root1 = TaxonomyNode.objects.create(
            series=self.series,
            name="Root One",
            slug="root-one",
        )
        root2 = TaxonomyNode.objects.create(
            series=self.series,
            name="Root Two",
            slug="root-two",
        )
        
        # Same slug under different parents should work
        child1 = TaxonomyNode.objects.create(
            series=self.series,
            name="Child",
            slug="child-slug",
            parent=root1,
        )
        child2 = TaxonomyNode.objects.create(
            series=self.series,
            name="Child",
            slug="child-slug",
            parent=root2,
        )
        
        self.assertEqual(child1.slug, child2.slug)
        self.assertNotEqual(child1.parent, child2.parent)
    
    def test_taxonomy_slug_allowed_in_different_series(self):
        """Same slug can be used in different series."""
        series2 = Series.objects.create(
            category=self.category,
            name="Another Series",
            slug="another-series",
        )
        
        n1 = TaxonomyNode.objects.create(
            series=self.series,
            name="Node One",
            slug="node-slug",
        )
        n2 = TaxonomyNode.objects.create(
            series=series2,
            name="Node Two",
            slug="node-slug",
        )
        
        self.assertEqual(n1.slug, n2.slug)
        self.assertNotEqual(n1.series, n2.series)
    
    def test_taxonomy_tree_structure(self):
        """Test parent-child relationships in taxonomy tree."""
        root = TaxonomyNode.objects.create(
            series=self.series,
            name="Root Node",
            slug="root",
            parent=None,
        )
        child1 = TaxonomyNode.objects.create(
            series=self.series,
            name="Child One",
            slug="child-one",
            parent=root,
        )
        child2 = TaxonomyNode.objects.create(
            series=self.series,
            name="Child Two",
            slug="child-two",
            parent=root,
        )
        grandchild = TaxonomyNode.objects.create(
            series=self.series,
            name="Grandchild",
            slug="grandchild",
            parent=child1,
        )
        
        # Test relationships
        self.assertEqual(root.children.count(), 2)
        self.assertEqual(child1.children.count(), 1)
        self.assertEqual(grandchild.parent, child1)
        
        # Test full_path property
        self.assertEqual(root.full_path, "Root Node")
        self.assertEqual(child1.full_path, "Root Node > Child One")
        self.assertEqual(grandchild.full_path, "Root Node > Child One > Grandchild")
        
        # Test depth property
        self.assertEqual(root.depth, 0)
        self.assertEqual(child1.depth, 1)
        self.assertEqual(grandchild.depth, 2)
    
    def test_breadcrumbs_property(self):
        """Test breadcrumbs generation."""
        root = TaxonomyNode.objects.create(
            series=self.series,
            name="Root",
            slug="root",
        )
        child = TaxonomyNode.objects.create(
            series=self.series,
            name="Child",
            slug="child",
            parent=root,
        )
        grandchild = TaxonomyNode.objects.create(
            series=self.series,
            name="Grandchild",
            slug="grandchild",
            parent=child,
        )
        
        breadcrumbs = grandchild.breadcrumbs
        self.assertEqual(len(breadcrumbs), 3)
        self.assertEqual(breadcrumbs[0], root)
        self.assertEqual(breadcrumbs[1], child)
        self.assertEqual(breadcrumbs[2], grandchild)


class ProductNodeConstraintsTest(TestCase):
    """Test product-node M2M relationship constraints."""
    
    def setUp(self):
        """Create test data."""
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.series = Series.objects.create(
            category=self.category,
            name="Test Series",
            slug="test-series",
        )
        self.node1 = TaxonomyNode.objects.create(
            series=self.series,
            name="Node One",
            slug="node-one",
        )
        self.node2 = TaxonomyNode.objects.create(
            series=self.series,
            name="Node Two",
            slug="node-two",
        )
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            title_tr="Test Ürün",
            series=self.series,
        )
    
    def test_product_node_unique(self):
        """Product-node relationship must be unique."""
        ProductNode.objects.create(
            product=self.product,
            node=self.node1,
        )
        
        with self.assertRaises(IntegrityError):
            ProductNode.objects.create(
                product=self.product,
                node=self.node1,
            )
    
    def test_product_multiple_nodes_allowed(self):
        """Product can belong to multiple different nodes."""
        pn1 = ProductNode.objects.create(
            product=self.product,
            node=self.node1,
        )
        pn2 = ProductNode.objects.create(
            product=self.product,
            node=self.node2,
        )
        
        self.assertEqual(self.product.nodes.count(), 2)
        self.assertIn(self.node1, self.product.nodes.all())
        self.assertIn(self.node2, self.product.nodes.all())
    
    def test_node_multiple_products_allowed(self):
        """Node can have multiple products."""
        product2 = Product.objects.create(
            name="Product Two",
            slug="product-two",
            title_tr="Ürün İki",
            series=self.series,
        )
        
        ProductNode.objects.create(product=self.product, node=self.node1)
        ProductNode.objects.create(product=product2, node=self.node1)
        
        self.assertEqual(self.node1.products.count(), 2)
