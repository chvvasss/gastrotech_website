"""
Global Admin Search API.

Provides fuzzy text search across multiple catalog entities using PostgreSQL
trigram similarity for efficient and accurate matching.

Endpoint: GET /api/v1/admin/search?q=<string>&limit=<int>
"""

import logging
from typing import List, Dict, Any

from django.contrib.postgres.search import TrigramSimilarity, TrigramWordSimilarity
from django.db.models import F, Value, CharField
from django.db.models.functions import Greatest, Coalesce
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import IsAdminOrEditor
from apps.catalog.models import (
    Brand,
    CatalogAsset,
    Category,
    Product,
    Series,
    SpecKey,
    SpecTemplate,
    TaxonomyNode,
    Variant,
)

logger = logging.getLogger(__name__)

# Constants
DEFAULT_LIMIT = 20
MAX_LIMIT = 50
MIN_QUERY_LENGTH = 2
MIN_SIMILARITY_THRESHOLD = 0.1


class AdminSearchView(APIView):
    """
    Global admin search endpoint.
    
    Searches across Products, Categories, Series, TaxonomyNodes, and Variants
    using PostgreSQL trigram similarity for fuzzy matching.
    
    Results are grouped by type and ordered by relevance score.
    """
    
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    
    @extend_schema(
        operation_id="admin_global_search",
        summary="Global Admin Search",
        description="""
        Search across all catalog entities with fuzzy matching.
        
        Searches in:
        - Products (title, slug, name)
        - Categories (name, slug)
        - Series (name, slug)
        - Taxonomy nodes (name, slug)
        - Taxonomy nodes (name, slug)
        - Variants (model_code, name)
        - Brands (name)
        - Spec Templates (name)
        - Spec Keys (label, slug)
        - Catalog Assets (title)
        
        Uses PostgreSQL trigram similarity for fuzzy text matching.
        Results are ordered by relevance score (descending).
        """,
        parameters=[
            OpenApiParameter(
                name="q",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Search query (minimum 2 characters)",
                required=True,
                examples=[
                    OpenApiExample(
                        name="Search products",
                        value="ocak",
                    ),
                    OpenApiExample(
                        name="Search by model code",
                        value="GKO6010",
                    ),
                ],
            ),
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                description=f"Maximum results to return (default: {DEFAULT_LIMIT}, max: {MAX_LIMIT})",
                required=False,
            ),
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": [
                                        "product", "category", "series", "taxonomy", "variant",
                                        "brand", "spec_template", "spec_key", "catalog_asset"
                                    ],
                                },
                                "id": {"type": "string", "format": "uuid"},
                                "title": {"type": "string"},
                                "subtitle": {"type": "string", "nullable": True},
                                "href": {"type": "string"},
                                "score": {"type": "number", "format": "float"},
                            },
                        },
                    },
                },
                "example": {
                    "query": "ocak",
                    "results": [
                        {
                            "type": "product",
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "title": "Gazlı Ocaklar",
                            "subtitle": "600 Series",
                            "href": "/catalog/products/gazli-ocaklar",
                            "score": 0.85,
                        },
                        {
                            "type": "taxonomy",
                            "id": "550e8400-e29b-41d4-a716-446655440001",
                            "title": "Ocaklar",
                            "subtitle": "Pişirme Üniteleri > 600 Series",
                            "href": "/catalog/taxonomy?node=ocaklar",
                            "score": 0.72,
                        },
                    ],
                },
            },
        },
        tags=["Admin - Search"],
    )
    def get(self, request):
        """Execute global search across catalog entities."""
        query = request.query_params.get("q", "").strip()
        
        # Validate query length
        if len(query) < MIN_QUERY_LENGTH:
            return Response({
                "query": query,
                "results": [],
            })
        
        # Parse and validate limit
        try:
            limit = int(request.query_params.get("limit", DEFAULT_LIMIT))
            limit = min(max(1, limit), MAX_LIMIT)
        except (ValueError, TypeError):
            limit = DEFAULT_LIMIT
        
        # Perform search across all entities
        results = []
        
        # Calculate per-type limit (distribute evenly, then take top overall)
        per_type_limit = max(5, limit // 3)
        
        try:
            # Search products
            product_results = self._search_products(query, per_type_limit)
            results.extend(product_results)
            
            # Search categories
            category_results = self._search_categories(query, per_type_limit)
            results.extend(category_results)
            
            # Search series
            series_results = self._search_series(query, per_type_limit)
            results.extend(series_results)
            
            # Search taxonomy nodes
            taxonomy_results = self._search_taxonomy_nodes(query, per_type_limit)
            results.extend(taxonomy_results)
            
            # Search variants (model codes)
            variant_results = self._search_variants(query, per_type_limit)
            results.extend(variant_results)
            
            # Search brands
            brand_results = self._search_brands(query, per_type_limit)
            results.extend(brand_results)

            # Search spec templates
            template_results = self._search_spec_templates(query, per_type_limit)
            results.extend(template_results)

            # Search spec keys
            key_results = self._search_spec_keys(query, per_type_limit)
            results.extend(key_results)

            # Search catalog assets
            asset_results = self._search_catalog_assets(query, per_type_limit)
            results.extend(asset_results)
            
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            # Return empty results on error rather than failing
            return Response({
                "query": query,
                "results": [],
            })
        
        # Sort by score descending and limit total results
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:limit]
        
        return Response({
            "query": query,
            "results": results,
        })
    
    def _search_products(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search products by title, name, and slug."""
        products = (
            Product.objects
            .annotate(
                title_sim=TrigramSimilarity("title_tr", query),
                name_sim=TrigramSimilarity("name", query),
                slug_sim=TrigramSimilarity("slug", query),
                similarity=Greatest("title_sim", "name_sim", "slug_sim"),
            )
            .filter(similarity__gte=MIN_SIMILARITY_THRESHOLD)
            .select_related("series", "series__category")
            .only("id", "title_tr", "slug", "series__name", "series__category__name")
            .order_by("-similarity")[:limit]
        )
        
        results = []
        for p in products:
            subtitle = None
            if p.series:
                if p.series.category:
                    subtitle = f"{p.series.category.name} > {p.series.name}"
                else:
                    subtitle = p.series.name
            
            results.append({
                "type": "product",
                "id": str(p.id),
                "title": p.title_tr,
                "subtitle": subtitle,
                "href": f"/catalog/products/{p.slug}",
                "score": round(float(p.similarity), 3),
            })
        
        return results
    
    def _search_categories(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search categories by name and slug."""
        categories = (
            Category.objects
            .annotate(
                name_sim=TrigramSimilarity("name", query),
                slug_sim=TrigramSimilarity("slug", query),
                similarity=Greatest("name_sim", "slug_sim"),
            )
            .filter(similarity__gte=MIN_SIMILARITY_THRESHOLD)
            .select_related("parent")
            .only("id", "name", "slug", "parent__name")
            .order_by("-similarity")[:limit]
        )
        
        results = []
        for c in categories:
            subtitle = c.parent.name if c.parent else None
            
            results.append({
                "type": "category",
                "id": str(c.id),
                "title": c.name,
                "subtitle": subtitle,
                "href": f"/catalog/products?category={c.slug}",
                "score": round(float(c.similarity), 3),
            })
        
        return results
    
    def _search_series(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search series by name and slug."""
        series_qs = (
            Series.objects
            .annotate(
                name_sim=TrigramSimilarity("name", query),
                slug_sim=TrigramSimilarity("slug", query),
                similarity=Greatest("name_sim", "slug_sim"),
            )
            .filter(similarity__gte=MIN_SIMILARITY_THRESHOLD)
            .select_related("category")
            .only("id", "name", "slug", "category__name")
            .order_by("-similarity")[:limit]
        )
        
        results = []
        for s in series_qs:
            subtitle = s.category.name if s.category else None
            
            results.append({
                "type": "series",
                "id": str(s.id),
                "title": s.name,
                "subtitle": subtitle,
                "href": f"/catalog/products?series={s.slug}",
                "score": round(float(s.similarity), 3),
            })
        
        return results
    
    def _search_taxonomy_nodes(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search taxonomy nodes by name and slug."""
        nodes = (
            TaxonomyNode.objects
            .annotate(
                name_sim=TrigramSimilarity("name", query),
                slug_sim=TrigramSimilarity("slug", query),
                similarity=Greatest("name_sim", "slug_sim"),
            )
            .filter(similarity__gte=MIN_SIMILARITY_THRESHOLD)
            .select_related("series", "series__category", "parent")
            .only("id", "name", "slug", "series__name", "series__category__name", "parent__name")
            .order_by("-similarity")[:limit]
        )
        
        results = []
        for n in nodes:
            # Build breadcrumb subtitle
            parts = []
            if n.series and n.series.category:
                parts.append(n.series.category.name)
            if n.series:
                parts.append(n.series.name)
            if n.parent:
                parts.append(n.parent.name)
            subtitle = " > ".join(parts) if parts else None
            
            results.append({
                "type": "taxonomy",
                "id": str(n.id),
                "title": n.name,
                "subtitle": subtitle,
                "href": f"/catalog/taxonomy?node={n.slug}",
                "score": round(float(n.similarity), 3),
            })
        
        return results
    
    def _search_variants(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search variants by model_code and name."""
        variants = (
            Variant.objects
            .annotate(
                code_sim=TrigramSimilarity("model_code", query),
                name_sim=TrigramSimilarity("name_tr", query),
                similarity=Greatest("code_sim", "name_sim"),
            )
            .filter(similarity__gte=MIN_SIMILARITY_THRESHOLD)
            .select_related("product")
            .only("id", "model_code", "name_tr", "product__slug", "product__title_tr")
            .order_by("-similarity")[:limit]
        )
        
        results = []
        for v in variants:
            subtitle = v.product.title_tr if v.product else None
            product_slug = v.product.slug if v.product else ""
            
            results.append({
                "type": "variant",
                "id": str(v.id),
                "title": f"{v.model_code} - {v.name_tr}",
                "subtitle": subtitle,
                "href": f"/catalog/products/{product_slug}",
                "score": round(float(v.similarity), 3),
            })
        
        return results
    
    def _search_brands(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search brands by name."""
        brands = (
            Brand.objects
            .annotate(
                similarity=TrigramSimilarity("name", query),
            )
            .filter(similarity__gte=MIN_SIMILARITY_THRESHOLD)
            .only("id", "name", "slug")
            .order_by("-similarity")[:limit]
        )
        
        results = []
        for b in brands:
            results.append({
                "type": "brand",
                "id": str(b.id),
                "title": b.name,
                "subtitle": "Marka",
                "href": f"/catalog/brands/{b.slug}",
                "score": round(float(b.similarity), 3),
            })
        return results

    def _search_spec_templates(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search spec templates by name."""
        templates = (
            SpecTemplate.objects
            .annotate(
                similarity=TrigramSimilarity("name", query),
            )
            .filter(similarity__gte=MIN_SIMILARITY_THRESHOLD)
            .only("id", "name")
            .order_by("-similarity")[:limit]
        )
        
        results = []
        for t in templates:
            results.append({
                "type": "spec_template",
                "id": str(t.id),
                "title": t.name,
                "subtitle": "Özellik Şablonu",
                # No detailed page yet, maybe direct to edit dialog? 
                # For now point to list page
                "href": "/catalog/templates", 
                "score": round(float(t.similarity), 3),
            })
        return results

    def _search_spec_keys(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search spec keys by label and slug."""
        keys = (
            SpecKey.objects
            .annotate(
                label_sim=TrigramSimilarity("label_tr", query),
                slug_sim=TrigramSimilarity("slug", query),
                similarity=Greatest("label_sim", "slug_sim"),
            )
            .filter(similarity__gte=MIN_SIMILARITY_THRESHOLD)
            .only("id", "label_tr", "slug")
            .order_by("-similarity")[:limit]
        )
        
        results = []
        for k in keys:
            results.append({
                "type": "spec_key",
                "id": str(k.id),
                "title": k.label_tr,
                "subtitle": k.slug,
                "href": "/catalog/specs", # List page
                "score": round(float(k.similarity), 3),
            })
        return results

    def _search_catalog_assets(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search catalog assets by title."""
        assets = (
            CatalogAsset.objects
            .annotate(
                similarity=TrigramSimilarity("title_tr", query),
            )
            .filter(similarity__gte=MIN_SIMILARITY_THRESHOLD)
            .only("id", "title_tr")
            .order_by("-similarity")[:limit]
        )
        
        results = []
        for a in assets:
            results.append({
                "type": "catalog_asset",
                "id": str(a.id),
                "title": a.title_tr,
                "subtitle": "Katalog Dosyası",
                "href": "/catalog/assets",
                "score": round(float(a.similarity), 3),
            })
        return results
