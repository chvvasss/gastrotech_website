"""
Catalog service functions.

Business logic for catalog operations.
"""

import re
from typing import Dict, List

from apps.common.slugify_tr import slugify_tr
from ..models import Product, ProductNode, SpecTemplate, TaxonomyNode


def generate_products_from_leaf_nodes(nodes_queryset) -> Dict[str, int]:
    """
    Generate Product groups for leaf taxonomy nodes.
    
    Args:
        nodes_queryset: QuerySet of TaxonomyNode objects
        
    Returns:
        Dict with counts: created, skipped_existing, skipped_non_leaf
    """
    result = {
        "created": 0,
        "skipped_existing": 0,
        "skipped_non_leaf": 0,
    }
    
    for node in nodes_queryset.select_related("series", "parent"):
        # Skip non-leaf nodes (nodes with children)
        if node.children.exists():
            result["skipped_non_leaf"] += 1
            continue
        
        # Check if product already exists for this node
        existing = Product.objects.filter(
            series=node.series,
            primary_node=node,
        ).exists()
        
        if existing:
            result["skipped_existing"] += 1
            continue
        
        # Create product
        product = create_product_for_leaf_node(node)
        if product:
            result["created"] += 1
    
    return result


def create_product_for_leaf_node(node: TaxonomyNode, status: str = "active") -> Product:
    """
    Create a Product for a leaf taxonomy node.
    
    Args:
        node: TaxonomyNode (must be a leaf node)
        status: Product status ("draft", "active", "archived")
        
    Returns:
        Created Product instance
    """
    series = node.series
    
    # Generate product name and slug
    name = f"{series.name} / {node.full_path}"
    slug = generate_product_slug(series, node)
    
    # Map status string to enum
    status_map = {
        "draft": Product.Status.DRAFT,
        "active": Product.Status.ACTIVE,
        "archived": Product.Status.ARCHIVED,
    }
    product_status = status_map.get(status, Product.Status.DRAFT)
    
    # Create product
    product = Product.objects.create(
        name=name,
        slug=slug,
        title_tr=node.name,
        series=series,
        primary_node=node,
        status=product_status,
    )
    
    # Add ProductNode relationships (leaf + ancestors)
    add_product_node_relationships(product, node)
    
    # Apply SpecTemplate if available
    apply_spec_template_to_product(product, node)
    
    return product


def generate_product_slug(series, node: TaxonomyNode) -> str:
    """
    Generate a product slug based on series and node.
    
    Rules:
    - If series.slug is numeric-like: "{series.slug}-serisi-{node.slug}"
    - Otherwise: "{series.slug}-{node.slug}"
    """
    series_slug = series.slug
    node_slug = node.slug
    
    # Check if series slug is numeric-like (e.g., "600", "700", "900")
    if re.match(r"^\d+$", series_slug):
        base_slug = f"{series_slug}-serisi-{node_slug}"
    else:
        base_slug = f"{series_slug}-{node_slug}"
    
    # Ensure uniqueness
    slug = base_slug
    counter = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug


def add_product_node_relationships(product: Product, node: TaxonomyNode):
    """
    Add ProductNode M2M relationships for a product.
    
    Adds the leaf node and all its ancestors.
    """
    # Get breadcrumbs (ancestors + self)
    nodes_to_add = node.breadcrumbs
    
    for n in nodes_to_add:
        ProductNode.objects.get_or_create(
            product=product,
            node=n,
        )


def apply_spec_template_to_product(product: Product, node: TaxonomyNode):
    """
    Apply a SpecTemplate to a product if one matches.
    
    Priority:
    1. Template with applies_to_series=series AND applies_to_parent_taxonomy_slug=node.parent.slug
    2. Template with applies_to_series=series
    3. No template
    """
    series = product.series
    parent_slug = node.parent.slug if node.parent else ""
    
    template = None
    
    # Try to find template with both series and parent slug match
    if parent_slug:
        template = SpecTemplate.objects.filter(
            applies_to_series=series,
            applies_to_parent_taxonomy_slug=parent_slug,
        ).first()
    
    # Fall back to template with just series match
    if not template:
        template = SpecTemplate.objects.filter(
            applies_to_series=series,
            applies_to_parent_taxonomy_slug="",
        ).first()
        
        # Also try null parent slug
        if not template:
            template = SpecTemplate.objects.filter(
                applies_to_series=series,
            ).exclude(
                applies_to_parent_taxonomy_slug__isnull=False,
            ).first()
    
    # Apply template if found
    if template:
        template.apply_to_product(product, overwrite=False)


def get_leaf_nodes_for_series(series) -> List[TaxonomyNode]:
    """
    Get all leaf nodes for a series.
    
    A leaf node is a node with no children.
    """
    all_nodes = TaxonomyNode.objects.filter(series=series)
    leaf_nodes = [node for node in all_nodes if not node.children.exists()]
    return leaf_nodes
