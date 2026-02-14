"""
Views for Gastrotech catalog public APIs.

All endpoints are public (AllowAny permission).
Implements caching for navigation and tree endpoints.
"""

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)

from .cache_keys import (
    nav_key,
    categories_tree_key,
    taxonomy_tree_key,
    spec_keys_key,
    NAV_CACHE_TTL,
    TREE_CACHE_TTL,
    SPEC_KEYS_CACHE_TTL,
)
from .filters import ProductFilter
from .query_utils import parse_bool_param, resolve_category_ids
from .models import (
    Brand,
    BrandCategory,
    CatalogAsset,
    Category,
    CategoryCatalog,
    Media,
    Product,
    ProductMedia,
    Series,
    SpecKey,
    TaxonomyNode,
    Variant,
)
from .pagination import ProductCursorPagination
from .serializers import (
    BrandDetailSerializer,
    BrandListSerializer,
    CatalogAssetSerializer,
    CategoryCatalogSerializer,
    CategoryChildrenSerializer,
    CategoryDetailSerializer,
    CategoryListSerializer,
    CategoryListWithCountsSerializer,
    CategoryTreeSerializer,
    MediaMetadataSerializer,
    NavCategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    SeriesSerializer,
    SeriesWithProductsSerializer,
    SeriesWithCountsSerializer,
    SpecKeySerializer,
    TaxonomyNodeTreeSerializer,
    VariantLookupSerializer,
)
from apps.common.utils import get_catalog_mode


# =============================================================================
# Cache Configuration (legacy, use cache_keys module)
# =============================================================================

CACHE_TTL_MEDIA = 60 * 60 * 24 * 7  # 7 days


# =============================================================================
# Navigation View
# =============================================================================


@extend_schema(
    summary="Get navigation structure",
    description="Returns categories with their series for site navigation. Cached for 5 minutes.",
    tags=["Navigation"],
    responses={200: NavCategorySerializer(many=True)},
    auth=[],  # Public endpoint - no authentication required
)
class NavView(APIView):
    """
    GET /api/v1/nav
    
    Returns categories with nested series for navigation.
    Cached in Redis for 5 minutes.
    """
    
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request):
        cache_key = nav_key()
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data)

        # Fetch only root categories with prefetched series
        # Series are annotated with product counts for visibility calculation
        # Subcategories are no longer nested; they appear as filters in PLP
        root_categories = list(
            Category.objects.filter(parent__isnull=True)
            .prefetch_related(
                Prefetch(
                    "series",
                    queryset=Series.objects.annotate(
                        _product_count=Count(
                            'products',
                            filter=Q(products__status='active')
                        )
                    ).order_by("order", "name"),
                )
            )
            .order_by("order", "name")
        )

        serializer = NavCategorySerializer(root_categories, many=True)
        data = serializer.data

        cache.set(cache_key, data, NAV_CACHE_TTL)
        return Response(data)



# =============================================================================
# Category Views
# =============================================================================


@extend_schema(
    summary="List categories",
    description="Returns flat list of all categories.",
    tags=["Categories"],
    responses={200: CategoryListSerializer(many=True)},
    auth=[],  # Public endpoint - no authentication required
)
class CategoryListView(generics.ListAPIView):
    """
    GET /api/v1/categories/

    Returns flat list of all categories.
    Query params:
    - include_counts: Add series_count and products_count annotations
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        include_counts = self.request.query_params.get("include_counts", "").lower() == "true"
        if include_counts:
            return CategoryListWithCountsSerializer
        return CategoryListSerializer

    def get_queryset(self):
        from django.db.models import Q
        queryset = Category.objects.select_related("parent").order_by("order", "name")

        # Add counts if requested
        include_counts = self.request.query_params.get("include_counts", "").lower() == "true"
        if include_counts:
            queryset = queryset.annotate(
                series_count=Count("series", distinct=True),
                products_count=Count(
                    "series__products",
                    filter=Q(series__products__status="active"),
                    distinct=True
                )
            )

        return queryset


@extend_schema(
    summary="Get category tree",
    description="Returns hierarchical category tree with children. Cached for 5 minutes.",
    tags=["Categories"],
    responses={200: CategoryTreeSerializer(many=True)},
    auth=[],  # Public endpoint - no authentication required
)
class CategoryTreeView(APIView):
    """
    GET /api/v1/categories/tree
    
    Returns category tree with recursive children.
    """
    
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request):
        cache_key = categories_tree_key()
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return Response(cached_data)
        
        # Fetch root categories
        categories = Category.objects.filter(parent__isnull=True).order_by("order", "name")
        
        # Prefetch all categories to avoid N+1 with counts
        all_categories = list(
            Category.objects
            .select_related("parent")
            .annotate(
                products_count=Count(
                    'series__products',
                    filter=Q(series__products__status='active'),
                    distinct=True
                ),
                subcategory_count=Count('children', distinct=True)
            )
        )

        # Build children map
        children_map = {}
        for cat in all_categories:
            if cat.parent_id:
                if cat.parent_id not in children_map:
                    children_map[cat.parent_id] = []
                children_map[cat.parent_id].append(cat)

        # Attach children to categories
        for cat in all_categories:
            cat._prefetched_children = children_map.get(cat.id, [])
        
        # Filter root categories with attached children
        root_categories = [c for c in all_categories if c.parent_id is None]
        root_categories.sort(key=lambda x: (x.order, x.name))
        
        serializer = CategoryTreeSerializer(root_categories, many=True)
        data = serializer.data
        
        cache.set(cache_key, data, TREE_CACHE_TTL)
        return Response(data)


@extend_schema(
    summary="Get category detail",
    description="Returns category with series list and product counts.",
    tags=["Categories"],
    responses={200: CategoryDetailSerializer},
    auth=[],  # Public endpoint - no authentication required
)
class CategoryDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/categories/<slug>/

    Returns category detail with:
    - Series list with product counts
    - Total products count in category
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = CategoryDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        from django.db.models import Q
        
        # Get brand slug from query params
        brand_slug = self.request.query_params.get("brand")
        
        # Base filters for products/series
        product_filters = Q(products__status="active")
        series_product_filters = Q(series__products__status="active")
        
        if brand_slug:
            product_filters &= Q(products__brand__slug=brand_slug)
            series_product_filters &= Q(series__products__brand__slug=brand_slug)

        return (
            Category.objects
            .select_related("parent", "cover_media")
            .prefetch_related(
                Prefetch(
                    "series",
                    queryset=Series.objects.annotate(
                        products_count=Count(
                            "products",
                            filter=product_filters
                        )
                    ).filter(
                        # Filter series to only those having active products (optionally filtered by brand)
                        products__status="active"
                    ).filter(
                        # If brand is selected, ensured series has products of that brand
                        Q(products__brand__slug=brand_slug) if brand_slug else Q()
                    ).distinct().order_by("order", "name")
                )
            )
            .annotate(
                products_count=Count(
                    "series__products",
                    filter=series_product_filters,
                    distinct=True
                )
            )
        )


@extend_schema(
    summary="Get category children (subcategories)",
    description="Returns immediate children of a category with product counts.",
    tags=["Categories"],
    responses={200: CategoryChildrenSerializer(many=True)},
    auth=[],  # Public endpoint - no authentication required
)
class CategoryChildrenView(generics.ListAPIView):
    """
    GET /api/v1/categories/<slug>/children/

    Returns immediate subcategories of a category with product counts.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = CategoryChildrenSerializer

    def get_queryset(self):
        from django.db.models import Q

        parent_slug = self.kwargs['slug']
        parent = get_object_or_404(Category, slug=parent_slug)

        return (
            Category.objects
            .filter(parent=parent)
            .annotate(
                products_count=Count(
                    'series__products',
                    filter=Q(series__products__status='active'),
                    distinct=True
                )
            )
            .order_by('order', 'name')
        )


# =============================================================================
# Series Views
# =============================================================================


@extend_schema(
    summary="List series",
    description="Returns series list, optionally filtered by category. Includes product counts and single_product info for singleton series.",
    tags=["Series"],
    parameters=[
        OpenApiParameter(
            name="category",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by category slug",
        ),
        OpenApiParameter(
            name="include_descendants",
            type=bool,
            location=OpenApiParameter.QUERY,
            description="Include descendant categories when filtering by category (default: true)",
        ),
        OpenApiParameter(
            name="include_descendants",
            type=bool,
            location=OpenApiParameter.QUERY,
            description="Include descendant categories when filtering by category (default: false)",
        ),
        OpenApiParameter(
            name="brand",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by brand slug",
        ),
    ],
    responses={200: SeriesWithCountsSerializer(many=True)},
    auth=[],  # Public endpoint - no authentication required
)
class SeriesListView(generics.ListAPIView):
    """
    GET /api/v1/series

    List series, optionally filtered by category slug.

    Returns series with:
    - products_count: Number of active products in series
    - is_visible: True if series has 2+ products (suitable for navigation grouping)
    - single_product_slug/name/image_url: For singleton series (1 product), allows direct product linking
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = SeriesWithCountsSerializer

    def get_queryset(self):
        queryset = Series.objects.select_related("category").order_by("order", "name")

        # Base products filter
        from django.db.models import Q
        product_filters = Q(products__status="active")

        category_slug = self.request.query_params.get("category")
        if category_slug:
            include_descendants = parse_bool_param(
                self.request.query_params.get("include_descendants")
            )
            include_descendants = False if include_descendants is None else include_descendants
            category_ids = resolve_category_ids(
                [category_slug],
                include_descendants=include_descendants,
            )
            if category_ids:
                queryset = queryset.filter(category__id__in=category_ids)
            else:
                return queryset.none()

        # Filter by Brand
        brand_slug = self.request.query_params.get("brand")
        if brand_slug:
            # Filter series that have products of this brand
            queryset = queryset.filter(products__brand__slug=brand_slug).distinct()
            # Update product count filter
            product_filters &= Q(products__brand__slug=brand_slug)

        # Annotate with product count (filtered) - SeriesWithCountsSerializer expects 'products_count'
        queryset = queryset.annotate(
            products_count=Count(
                "products",
                filter=product_filters,
                distinct=True
            )
        )

        return queryset


# =============================================================================
# Brand Views
# =============================================================================


@extend_schema(
    summary="List brands",
    description="Returns active brands list for filtering.",
    tags=["Brands"],
    parameters=[
        OpenApiParameter(
            name="series",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by series slug",
        ),
        OpenApiParameter(
            name="category",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by category slug",
        ),
        OpenApiParameter(
            name="include_descendants",
            type=bool,
            location=OpenApiParameter.QUERY,
            description="Include descendant categories when filtering by category (default: false)",
        ),
    ],
    responses={200: "list of brands"},
    auth=[],  # Public endpoint - no authentication required
)
class BrandListView(generics.ListAPIView):
    """
    GET /api/v1/brands
    
    List active brands.
    """
    
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        from .models import Brand
        queryset = Brand.objects.filter(is_active=True)
        
        series_slug = self.request.query_params.get("series")
        if series_slug:
            queryset = queryset.filter(products__series__slug=series_slug).distinct()

        category_slug = self.request.query_params.get("category")
        if category_slug:
            include_descendants = parse_bool_param(
                self.request.query_params.get("include_descendants")
            )
            include_descendants = False if include_descendants is None else include_descendants
            category_ids = resolve_category_ids(
                [category_slug],
                include_descendants=include_descendants,
            )
            if not category_ids:
                return queryset.none()

            if series_slug:
                queryset = queryset.filter(
                    products__series__category__id__in=category_ids
                ).distinct()
            else:
                assigned_brand_ids = BrandCategory.objects.filter(
                    category_id__in=category_ids,
                    is_active=True,
                ).values_list("brand_id", flat=True)

                product_brand_ids = Product.objects.filter(
                    series__category__id__in=category_ids,
                    status=Product.Status.ACTIVE,
                    brand__isnull=False,
                ).values_list("brand_id", flat=True)

                queryset = queryset.filter(
                    Q(id__in=assigned_brand_ids) | Q(id__in=product_brand_ids)
                ).distinct()
            
        return queryset.order_by("order", "name")
    
    def get(self, request, *args, **kwargs):
        brands = self.get_queryset()

        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        category_slug = request.query_params.get("category")
        logger.info(f"[BrandListView] category_slug={category_slug}, brand_count={brands.count()}")

        # Force reload
        data = [
            {
                "id": str(b.id),
                "name": b.name,
                "slug": b.slug,
                "logo_url": f"/api/v1/media/{b.logo_media_id}/file/" if b.logo_media_id else None,
                "description": b.description or None,
                "website_url": b.website_url or None,
                "is_active": b.is_active,
                "order": b.order,
            }
            for b in brands
        ]
        logger.info(f"[BrandListView] Returning {len(data)} brands")
        return Response(data)


# =============================================================================
# Taxonomy Views
# =============================================================================


@extend_schema(
    summary="Get taxonomy tree",
    description="Returns taxonomy tree for a series. Cached for 5 minutes per series.",
    tags=["Taxonomy"],
    parameters=[
        OpenApiParameter(
            name="series",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Series slug (required)",
            required=True,
        ),
    ],
    responses={
        200: TaxonomyNodeTreeSerializer(many=True),
        400: OpenApiResponse(description="Missing series parameter"),
    },
    auth=[],  # Public endpoint - no authentication required
)
class TaxonomyTreeView(APIView):
    """
    GET /api/v1/taxonomy/tree?series=series-slug
    
    Returns taxonomy tree for a series.
    """
    
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request):
        series_slug = request.query_params.get("series")
        if not series_slug:
            return Response(
                {"error": "series parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        cache_key = taxonomy_tree_key(series_slug)
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return Response(cached_data)
        
        # Get series
        series = get_object_or_404(Series, slug=series_slug)
        
        # Fetch all nodes for this series
        all_nodes = list(
            TaxonomyNode.objects.filter(series=series)
            .select_related("parent")
            .order_by("order", "name")
        )
        
        # Build children map
        children_map = {}
        for node in all_nodes:
            if node.parent_id:
                if node.parent_id not in children_map:
                    children_map[node.parent_id] = []
                children_map[node.parent_id].append(node)
        
        # Attach children and compute depth
        for node in all_nodes:
            node._prefetched_children = children_map.get(node.id, [])
        
        # Filter root nodes
        root_nodes = [n for n in all_nodes if n.parent_id is None]
        
        serializer = TaxonomyNodeTreeSerializer(root_nodes, many=True)
        data = serializer.data
        
        cache.set(cache_key, data, TREE_CACHE_TTL)
        return Response(data)


# =============================================================================
# SpecKey Views
# =============================================================================


@extend_schema(
    summary="List spec keys",
    description="Returns all specification keys ordered by sort_order.",
    tags=["Specifications"],
    responses={200: SpecKeySerializer(many=True)},
    auth=[],  # Public endpoint - no authentication required
)
class SpecKeyListView(generics.ListAPIView):
    """
    GET /api/v1/spec-keys
    
    Returns all spec keys.
    """
    
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = SpecKeySerializer
    queryset = SpecKey.objects.order_by("sort_order", "label_tr")


# =============================================================================
# Product Views
# =============================================================================


@extend_schema(
    summary="List products",
    description="Returns paginated product list with filtering and sorting.",
    tags=["Products"],
    parameters=[
        OpenApiParameter(
            name="series",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by series slug",
        ),
        OpenApiParameter(
            name="node",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by taxonomy node slug",
        ),
        OpenApiParameter(
            name="category",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by category slug",
        ),
        OpenApiParameter(
            name="status",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by status (default: active)",
            enum=["draft", "active", "archived"],
        ),
        OpenApiParameter(
            name="search",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Search in title and model codes",
        ),
        OpenApiParameter(
            name="sort",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Sort order",
            enum=["newest", "featured", "title_asc"],
        ),
        OpenApiParameter(
            name="cursor",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Pagination cursor",
        ),
        OpenApiParameter(
            name="page_size",
            type=int,
            location=OpenApiParameter.QUERY,
            description="Page size (default: 24, max: 100)",
        ),
    ],
    responses={200: ProductListSerializer(many=True)},
    auth=[],  # Public endpoint - no authentication required
)
class ProductListView(generics.ListAPIView):
    """
    GET /api/v1/products

    Cursor-paginated product list with filtering.
    Defaults to active products only for public view.
    Returns empty when catalog_mode is ON.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = ProductListSerializer
    pagination_class = ProductCursorPagination
    filterset_class = ProductFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        if get_catalog_mode():
            return Product.objects.none()

        queryset = (
            Product.objects
            .select_related("series", "series__category", "primary_node", "brand")
            .prefetch_related(
                # Only prefetch media metadata, not bytes
                Prefetch(
                    "product_media",
                    queryset=ProductMedia.objects.select_related("media").only(
                        "id",
                        "product_id",
                        "media_id",
                        "sort_order",
                        "is_primary",
                        "media__id",
                        "media__kind",
                        "media__filename",
                    ).order_by("sort_order"),
                ),
            )
            .annotate(_variants_count=Count("variants"))
        )

        # Default to active only if status not specified
        if "status" not in self.request.query_params:
            queryset = queryset.filter(status=Product.Status.ACTIVE)

        return queryset


@extend_schema(
    summary="Get, update or delete product detail",
    description="Returns full product detail. DELETE requires authentication.",
    tags=["Products"],
    responses={
        200: ProductDetailSerializer,
        204: OpenApiResponse(description="Product deleted"),
        404: OpenApiResponse(description="Product not found"),
    },
)
class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/v1/products/{slug}
    DELETE /api/v1/products/{slug}

    Returns 404 when catalog_mode is ON.
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        if get_catalog_mode():
            return Product.objects.none()

        queryset = (
            Product.objects
            .select_related("series", "series__category", "primary_node", "brand")
            .prefetch_related(
                # Prefetch media without bytes
                Prefetch(
                    "product_media",
                    queryset=ProductMedia.objects.select_related("media").defer(
                        "media__bytes"
                    ).order_by("sort_order"),
                ),
                "variants",
            )
        )

        # For public view, only show active products
        # (can be removed if admin needs access)
        if "status" not in self.request.query_params:
            queryset = queryset.filter(status=Product.Status.ACTIVE)

        return queryset


# =============================================================================
# Media Views
# =============================================================================


@extend_schema(
    summary="Get media metadata",
    description="Returns media metadata without binary content.",
    tags=["Media"],
    responses={
        200: MediaMetadataSerializer,
        404: OpenApiResponse(description="Media not found"),
    },
    auth=[],  # Public endpoint - no authentication required
)
class MediaMetadataView(generics.RetrieveAPIView):
    """
    GET /api/v1/media/{id}
    
    Returns media metadata only (no bytes).
    """
    
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = MediaMetadataSerializer
    lookup_field = "id"
    
    def get_queryset(self):
        # Explicitly exclude bytes from query
        return Media.objects.defer("bytes")


@extend_schema(
    summary="Stream media file",
    description=(
        "Streams binary content with proper headers. "
        "Supports ETag caching with If-None-Match header."
    ),
    tags=["Media"],
    responses={
        200: OpenApiResponse(
            description="Binary file content",
        ),
        304: OpenApiResponse(description="Not Modified (ETag match)"),
        404: OpenApiResponse(description="Media not found"),
    },
    auth=[],  # Public endpoint - no authentication required
)
class MediaFileView(APIView):
    """
    GET /api/v1/media/{id}/file
    
    Stream binary content with caching headers.
    """
    
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request, id):
        # Get media object
        media = get_object_or_404(Media, id=id)
        
        # Check If-None-Match header for 304 response
        if_none_match = request.headers.get("If-None-Match")
        if if_none_match:
            # Strip quotes if present
            etag = if_none_match.strip('"')
            if etag == media.checksum_sha256:
                response = HttpResponse(status=304)
                response["ETag"] = f'"{media.checksum_sha256}"'
                return response
        
        # Build response with binary content
        response = HttpResponse(
            media.bytes,
            content_type=media.content_type,
        )
        
        # Set caching headers
        response["Content-Length"] = media.size_bytes
        response["ETag"] = f'"{media.checksum_sha256}"'
        
        # Cache for 7 days for images/PDFs
        if media.kind in ["image", "pdf"]:
            response["Cache-Control"] = "public, max-age=604800"
        else:
            response["Cache-Control"] = "public, max-age=3600"
        
        # Content-Disposition for downloads
        if media.kind == "pdf":
            response["Content-Disposition"] = f'inline; filename="{media.filename}"'
        
        return response


# =============================================================================
# Catalog Asset Views
# =============================================================================


@extend_schema(
    summary="List catalog assets",
    description="Returns published catalog assets (PDF downloads).",
    tags=["Catalog Assets"],
    responses={200: CatalogAssetSerializer(many=True)},
    auth=[],  # Public endpoint - no authentication required
)
class CatalogAssetListView(generics.ListAPIView):
    """
    GET /api/v1/catalog-assets
    
    Returns published catalog assets for download.
    """
    
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = CatalogAssetSerializer
    pagination_class = None  # No pagination for this small list
    
    def get_queryset(self):
        return (
            CatalogAsset.objects
            .filter(published=True)
            .select_related("media")
            .order_by("order", "title_tr")
        )


# =============================================================================
# Variant Lookup Views
# =============================================================================


@extend_schema(
    summary="Lookup variants by model codes",
    description=(
        "Returns variant details for the given model codes. "
        "Preserves input order. Returns error for unknown codes. "
        "Max 50 codes per request."
    ),
    tags=["Variants"],
    parameters=[
        OpenApiParameter(
            name="codes",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Comma-separated model codes (e.g., GKO6010,GKO6020)",
            required=True,
        ),
    ],
    responses={
        200: VariantLookupSerializer(many=True),
        400: OpenApiResponse(description="Missing or invalid codes parameter"),
    },
    auth=[],  # Public endpoint - no authentication required
)
class VariantByCodesView(APIView):
    """
    GET /api/v1/variants/by-codes?codes=GKO6010,GKO6020
    
    Lookup variants by model codes with full hierarchy info.
    Returns results in the same order as input codes.
    """
    
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request):
        codes_param = request.query_params.get("codes", "")
        
        if not codes_param:
            return Response(
                {"error": "codes parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Parse, trim, dedupe, limit to 50
        raw_codes = [c.strip() for c in codes_param.split(",") if c.strip()]
        seen = set()
        codes = []
        for code in raw_codes:
            if code not in seen and len(codes) < 50:
                seen.add(code)
                codes.append(code)
        
        if not codes:
            return Response(
                {"error": "No valid codes provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Fetch variants with optimized query (no Media.bytes)
        variants = (
            Variant.objects
            .filter(model_code__in=codes)
            .select_related("product__series__category")
            .only(
                "model_code",
                "name_tr",
                "name_en",
                "dimensions",
                "weight_kg",
                "list_price",
                "specs",
                "product__slug",
                "product__title_tr",
                "product__series__slug",
                "product__series__name",
                "product__series__category__slug",
                "product__series__category__name",
            )
        )
        
        # Build lookup map
        variant_map = {v.model_code: v for v in variants}
        
        # Build response in input order
        result = []
        for code in codes:
            variant = variant_map.get(code)
            if variant:
                result.append({
                    "model_code": code,
                    "name_tr": variant.name_tr,
                    "name_en": variant.name_en or None,
                    "product_slug": variant.product.slug if variant.product else None,
                    "product_title_tr": variant.product.title_tr if variant.product else None,
                    "series_slug": variant.product.series.slug if variant.product and variant.product.series else None,
                    "series_name": variant.product.series.name if variant.product and variant.product.series else None,
                    "category_slug": variant.product.series.category.slug if variant.product and variant.product.series and variant.product.series.category else None,
                    "category_name": variant.product.series.category.name if variant.product and variant.product.series and variant.product.series.category else None,
                    "dimensions": variant.dimensions or None,
                    "weight_kg": variant.weight_kg,
                    "list_price": variant.list_price,
                    "specs": variant.specs or None,
                    "error": None,
                })
            else:
                result.append({
                    "model_code": code,
                    "name_tr": None,
                    "name_en": None,
                    "product_slug": None,
                    "product_title_tr": None,
                    "series_slug": None,
                    "series_name": None,
                    "category_slug": None,
                    "category_name": None,
                    "dimensions": None,
                    "weight_kg": None,
                    "list_price": None,
                    "specs": None,
                    "error": "not_found",
                })
        
        return Response(result, status=status.HTTP_200_OK)


# =============================================================================
# Brand Views
# =============================================================================


@extend_schema(
    summary="List brands",
    description="Returns paginated brand list with category associations.",
    tags=["Brands"],
    parameters=[
        OpenApiParameter(
            name="category",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter brands by category slug",
        ),
        OpenApiParameter(
            name="is_active",
            type=bool,
            location=OpenApiParameter.QUERY,
            description="Filter by active status (default: true)",
        ),
    ],
    responses={200: BrandListSerializer(many=True)},
    auth=[],  # Public endpoint - no authentication required
)
# BrandListView is defined earlier in the file (line ~435)
# This duplicate definition has been removed


@extend_schema(
    summary="Get brand detail",
    description="Returns full brand detail with category associations and product count.",
    tags=["Brands"],
    responses={
        200: BrandDetailSerializer,
        404: OpenApiResponse(description="Brand not found"),
    },
    auth=[],  # Public endpoint - no authentication required
)
class BrandDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/brands/{slug}

    Returns full brand detail with categories.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = BrandDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Brand.objects
            .select_related("logo_media")
            .prefetch_related(
                "brand_categories__category",
                "products",
            )
            .order_by("order", "name")
        )


@extend_schema(
    summary="Update brand categories",
    description="Update categories associated with a brand. Requires authentication.",
    tags=["Brands"],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "categories": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "format": "uuid"},
                            "is_active": {"type": "boolean"},
                            "order": {"type": "integer"},
                        },
                        "required": ["category", "is_active", "order"],
                    },
                }
            },
            "required": ["categories"],
        }
    },
    responses={
        200: BrandDetailSerializer,
        400: OpenApiResponse(description="Invalid data"),
        401: OpenApiResponse(description="Authentication required"),
        404: OpenApiResponse(description="Brand not found"),
    },
)
class BrandCategoriesUpdateView(APIView):
    """
    PUT /api/v1/brands/{slug}/categories/

    Update categories for a brand. Requires admin authentication.
    """

    permission_classes = [permissions.IsAdminUser]

    def put(self, request, slug):
        # Get brand
        try:
            brand = Brand.objects.get(slug=slug)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        categories_data = request.data.get("categories", [])

        # Validate categories exist
        category_ids = [cat["category"] for cat in categories_data]
        existing_categories = set(
            str(uuid) for uuid in Category.objects.filter(id__in=category_ids).values_list("id", flat=True)
        )

        for cat_id in category_ids:
            if str(cat_id) not in existing_categories:
                return Response(
                    {"error": f"Category {cat_id} not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Delete existing brand categories
        brand.brand_categories.all().delete()

        # Create new brand categories
        brand_categories = []
        for cat_data in categories_data:
            brand_categories.append(
                BrandCategory(
                    brand=brand,
                    category_id=cat_data["category"],
                    is_active=cat_data["is_active"],
                    order=cat_data["order"],
                )
            )

        BrandCategory.objects.bulk_create(brand_categories)

        # Return updated brand
        brand.refresh_from_db()
        serializer = BrandDetailSerializer(brand)
        return Response(serializer.data)


# =============================================================================
# Browse Endpoint (Category Navigation)
# =============================================================================


@extend_schema(
    summary="Browse category",
    description=(
        "Returns category navigation data with optimized series visibility:\n"
        "- series: Only series with 2+ products (visible for navigation)\n"
        "- products: All products in category, including those from singleton series\n\n"
        "This implements the 'single-product series becomes product' rule."
    ),
    tags=["Navigation"],
    parameters=[
        OpenApiParameter(
            name="category",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Category slug (required)",
            required=True,
        ),
        OpenApiParameter(
            name="brand",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by brand slug",
        ),
        OpenApiParameter(
            name="include_singletons",
            type=bool,
            location=OpenApiParameter.QUERY,
            description="Include singleton series in series list (default: false)",
        ),
        OpenApiParameter(
            name="include_empty",
            type=bool,
            location=OpenApiParameter.QUERY,
            description="Include empty series in series list (default: false)",
        ),
    ],
    responses={
        200: {
            "type": "object",
            "properties": {
                "category": {"$ref": "#/components/schemas/CategoryDetail"},
                "series": {"type": "array", "items": {"$ref": "#/components/schemas/SeriesWithCounts"}},
                "products": {"type": "array", "items": {"$ref": "#/components/schemas/ProductList"}},
                "total_products": {"type": "integer"},
                "singleton_series_count": {"type": "integer"},
            },
        },
        400: OpenApiResponse(description="Missing category parameter"),
        404: OpenApiResponse(description="Category not found"),
    },
    auth=[],  # Public endpoint
)
class BrowseCategoryView(APIView):
    """
    GET /api/v1/browse?category=<slug>&brand=<slug>

    Returns navigation-optimized data for a category:
    - series: Multi-product series (2+ products) for navigation
    - products: All products including singleton-series products

    This enables the UX pattern where:
    - Series with 2+ products appear as groupings
    - Series with 1 product: user sees product directly
    - Series with 0 products: hidden
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        category_slug = request.query_params.get("category")
        if not category_slug:
            return Response(
                {"error": "category parameter is required", "code": "MISSING_CATEGORY"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get category
        try:
            category = Category.objects.select_related("parent", "cover_media").get(slug=category_slug)
        except Category.DoesNotExist:
            return Response(
                {"error": f"Category '{category_slug}' not found", "code": "CATEGORY_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Parse options
        brand_slug = request.query_params.get("brand")
        include_singletons = request.query_params.get("include_singletons", "").lower() == "true"
        include_empty = request.query_params.get("include_empty", "").lower() == "true"

        # Base product filter
        product_filter = Q(products__status="active")
        if brand_slug:
            product_filter &= Q(products__brand__slug=brand_slug)

        # Get series with product counts
        series_qs = (
            Series.objects
            .filter(category=category)
            .annotate(
                products_count=Count("products", filter=product_filter, distinct=True)
            )
            .select_related("category")
            .order_by("order", "name")
        )

        # Determine visible series based on options
        all_series = list(series_qs)
        visible_series = []
        singleton_series = []

        for s in all_series:
            if s.products_count >= 2:
                visible_series.append(s)
            elif s.products_count == 1:
                singleton_series.append(s)
            # Empty series (products_count == 0) excluded by default

        # Optionally include singletons in series list
        if include_singletons:
            visible_series.extend(singleton_series)
            visible_series.sort(key=lambda x: (x.order, x.name))

        # Optionally include empty series
        if include_empty:
            empty_series = [s for s in all_series if s.products_count == 0]
            visible_series.extend(empty_series)
            visible_series.sort(key=lambda x: (x.order, x.name))

        # Get products (all active products in category)
        products_qs = (
            Product.objects
            .filter(series__category=category, status=Product.Status.ACTIVE)
            .select_related("series", "series__category", "brand")
            .prefetch_related(
                Prefetch(
                    "product_media",
                    queryset=ProductMedia.objects.select_related("media").only(
                        "id", "product_id", "media_id", "sort_order", "is_primary",
                        "media__id", "media__kind", "media__filename",
                    ).order_by("sort_order"),
                ),
            )
            .annotate(_variants_count=Count("variants"))
            .order_by("series__order", "is_featured", "title_tr")
        )

        if brand_slug:
            products_qs = products_qs.filter(brand__slug=brand_slug)

        products = list(products_qs)

        # Serialize data
        series_data = SeriesWithCountsSerializer(visible_series, many=True).data
        products_data = ProductListSerializer(products, many=True).data

        # Build category summary
        category_data = {
            "id": str(category.id),
            "name": category.name,
            "slug": category.slug,
            "menu_label": category.menu_label,
            "description_short": category.description_short,
            "cover_media_url": f"/api/v1/media/{category.cover_media_id}/file" if category.cover_media_id else None,
        }

        return Response({
            "category": category_data,
            "series": series_data,
            "products": products_data,
            "total_products": len(products),
            "singleton_series_count": len(singleton_series),
            "visible_series_count": len(visible_series),
        })


# =============================================================================
# Category Catalog Views
# =============================================================================


class CategoryCatalogListView(generics.ListAPIView):
    """
    GET /api/v1/category-catalogs/?category=<slug>

    Returns published category catalog PDFs.
    Returns empty list when catalog_mode is OFF.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = CategoryCatalogSerializer
    pagination_class = None

    def get_queryset(self):
        if not get_catalog_mode():
            return CategoryCatalog.objects.none()

        qs = (
            CategoryCatalog.objects
            .filter(published=True)
            .select_related('media', 'category')
            .order_by('order', 'title_tr')
        )

        category_slug = self.request.query_params.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        return qs
