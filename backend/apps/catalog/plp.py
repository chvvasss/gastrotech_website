"""
Product Listing Page (PLP) API views for Gastrotech catalog.

Provides faceted filtering, sorting, and pagination for category-based
product browsing with real-time filter counts.
"""

from collections import defaultdict
from decimal import Decimal
from typing import Any

from django.db.models import Count, Max, Min, Q, Prefetch, Case, When, Value, BooleanField, F
from django.db.models.functions import Coalesce
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Brand, Category, CategoryCatalog, Product, ProductMedia, Variant
from .serializers import CategoryCatalogSerializer
from apps.common.utils import get_catalog_mode


# =============================================================================
# Constants
# =============================================================================

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 24

# Known attribute keys that should appear as facets
# These correspond to common keys in Variant.specs JSON
FACET_ATTRIBUTE_KEYS = [
    ("power_type", "Güç Tipi"),
    ("series_type", "Seri"),
    ("capacity", "Kapasite"),
    ("width", "Genişlik"),
    ("depth", "Derinlik"),
]

SORT_OPTIONS = {
    "name_asc": ("title_tr", "İsim (A-Z)"),
    "name_desc": ("-title_tr", "İsim (Z-A)"),
    "price_asc": ("_min_price", "Fiyat (Artan)"),
    "price_desc": ("-_min_price", "Fiyat (Azalan)"),
    "newest": ("-created_at", "En Yeni"),
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_category_subtree_ids(category: Category) -> list:
    """
    Get all category IDs in the subtree (including the category itself).
    Uses the Category.get_descendants() method for recursive traversal.
    """
    descendants = category.get_descendants(include_self=True)
    return [cat.id for cat in descendants]


def parse_comma_list(value: str | None) -> list[str]:
    """Parse comma-separated string into list of trimmed values."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def parse_bool(value: str | None) -> bool | None:
    """Parse boolean query parameter."""
    if value is None:
        return None
    return value.lower() in ("true", "1", "yes")


def parse_decimal(value: str | None) -> Decimal | None:
    """Parse decimal query parameter."""
    if not value:
        return None
    try:
        return Decimal(value)
    except Exception:
        return None


def parse_int(value: str | None, default: int = 1) -> int:
    """Parse integer query parameter with default."""
    if not value:
        return default
    try:
        return int(value)
    except Exception:
        return default


# =============================================================================
# PLP View
# =============================================================================

@extend_schema(
    summary="Product Listing Page with faceted filters",
    description=(
        "Returns products with faceted filter counts for category-based browsing.\n\n"
        "Features:\n"
        "- Category subtree filtering (includes all descendant categories)\n"
        "- Brand filtering with counts\n"
        "- Price range filtering\n"
        "- Stock filtering\n"
        "- Dynamic attribute facets from variant specs\n"
        "- Multiple sort options\n"
        "- Page-based pagination"
    ),
    tags=["PLP"],
    parameters=[
        OpenApiParameter(
            name="category",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Category slug (required)",
            required=True,
        ),
        OpenApiParameter(
            name="brands",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Comma-separated brand slugs",
        ),
        OpenApiParameter(
            name="price_min",
            type=float,
            location=OpenApiParameter.QUERY,
            description="Minimum price filter",
        ),
        OpenApiParameter(
            name="price_max",
            type=float,
            location=OpenApiParameter.QUERY,
            description="Maximum price filter",
        ),
        OpenApiParameter(
            name="in_stock",
            type=bool,
            location=OpenApiParameter.QUERY,
            description="Filter to only show in-stock products",
        ),
        OpenApiParameter(
            name="sort",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Sort order",
            enum=list(SORT_OPTIONS.keys()),
        ),
        OpenApiParameter(
            name="page",
            type=int,
            location=OpenApiParameter.QUERY,
            description="Page number (default: 1)",
        ),
        OpenApiParameter(
            name="page_size",
            type=int,
            location=OpenApiParameter.QUERY,
            description=f"Items per page (default: {DEFAULT_PAGE_SIZE}, max: {MAX_PAGE_SIZE})",
        ),
    ],
    responses={
        200: OpenApiResponse(description="PLP data with products and facets"),
        400: OpenApiResponse(description="Missing or invalid category parameter"),
        404: OpenApiResponse(description="Category not found"),
    },
    auth=[],
)
class PLPView(APIView):
    """
    GET /api/v1/plp/?category=<slug>&brands=...&price_min=...
    
    Returns:
    - products: Paginated product list
    - pagination: Page info
    - facets: Brand counts, price range, attribute counts
    - selected_filters: Currently applied filters
    """
    
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Parse required category parameter
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

        # Catalog mode: return catalogs instead of products
        if get_catalog_mode():
            catalogs = (
                CategoryCatalog.objects
                .filter(category=category, published=True)
                .select_related("media", "category")
                .order_by("order", "title_tr")
            )
            catalogs_data = CategoryCatalogSerializer(catalogs, many=True).data

            breadcrumbs = [
                {"name": c.name, "slug": c.slug}
                for c in category.breadcrumbs
            ]

            return Response({
                "catalog_mode": True,
                "category": {
                    "id": str(category.id),
                    "name": category.name,
                    "slug": category.slug,
                    "description_short": category.description_short,
                    "cover_media_url": f"/api/v1/media/{category.cover_media_id}/file" if category.cover_media_id else None,
                    "breadcrumbs": breadcrumbs,
                },
                "catalogs": catalogs_data,
                "products": [],
                "pagination": {
                    "total": 0,
                    "page": 1,
                    "page_size": 24,
                    "total_pages": 1,
                    "has_next": False,
                    "has_prev": False,
                },
                "facets": {
                    "brands": [],
                    "categories": [],
                    "price": {"min": 0, "max": 0},
                    "series": [],
                    "attributes": [],
                },
                "selected_filters": {
                    "brands": [],
                    "price_min": None,
                    "price_max": None,
                    "in_stock": False,
                    "series": [],
                    "attrs": None,
                },
                "sort": "name_asc",
                "sort_options": [
                    {"key": k, "label": v[1]} for k, v in SORT_OPTIONS.items()
                ],
            })

        # Parse filter parameters
        brand_slugs = parse_comma_list(request.query_params.get("brands"))
        price_min = parse_decimal(request.query_params.get("price_min"))
        price_max = parse_decimal(request.query_params.get("price_max"))
        in_stock = parse_bool(request.query_params.get("in_stock"))
        sort_key = request.query_params.get("sort", "name_asc")
        page = parse_int(request.query_params.get("page"), 1)
        page_size = min(
            parse_int(request.query_params.get("page_size"), DEFAULT_PAGE_SIZE),
            MAX_PAGE_SIZE
        )
        
        # Get category subtree IDs
        category_ids = get_category_subtree_ids(category)
        
        # Build base product queryset
        base_qs = (
            Product.objects
            .filter(
                Q(series__category_id__in=category_ids) | Q(category_id__in=category_ids),
                status=Product.Status.ACTIVE,
            )
            .select_related("series", "series__category", "brand", "brand__logo_media")
            .prefetch_related(
                Prefetch(
                    "product_media",
                    queryset=ProductMedia.objects.select_related("media").only(
                        "id", "product_id", "media_id", "sort_order", "is_primary",
                        "media__id", "media__kind", "media__filename",
                    ).order_by("-is_primary", "sort_order"),
                ),
            )
            .distinct()
        )
        
        # Annotate with price and stock info from variants
        base_qs = base_qs.annotate(
            _min_price=Min("variants__list_price"),
            _max_price=Max("variants__list_price"),
            _has_stock=Case(
                When(variants__stock_qty__isnull=True, then=Value(True)),  # NULL = unlimited
                When(variants__stock_qty__gt=0, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )
        
        # =====================================================================
        # Compute facets BEFORE applying filters (for accurate counts)
        # =====================================================================
        
        # Brand facets (count products per brand in category)
        brand_facets = self._compute_brand_facets(base_qs, brand_slugs)
        
        # Price range facet
        price_facet = self._compute_price_facet(base_qs)
        
        # Subcategory facets
        category_facets = self._compute_category_facets(category, category_ids, base_qs)

        # Series facets
        series_facets = self._compute_series_facets(base_qs)

        # Attribute facets (from Variant specs)
        attribute_facets = self._compute_attribute_facets(base_qs)
        
        # =====================================================================
        # Apply filters
        # =====================================================================
        
        filtered_qs = base_qs
        
        # Brand filter (OR within, so multiple brands = A OR B)
        if brand_slugs:
            filtered_qs = filtered_qs.filter(brand__slug__in=brand_slugs)

        # Series filter
        series_slugs = parse_comma_list(request.query_params.get("series"))
        if series_slugs:
            filtered_qs = filtered_qs.filter(series__slug__in=series_slugs)
            
        # Attribute filters (format: attrs=key:value,key2:value2)
        attrs_param = request.query_params.get("attrs")
        if attrs_param:
            for pair in attrs_param.split(","):
                if ":" in pair:
                    key, val = pair.split(":", 1)
                    key, val = key.strip(), val.strip()
                    if key and val:
                        # JSON contains check for specs
                        filtered_qs = filtered_qs.filter(variants__specs__contains={key: val})
        
        # Price filter
        if price_min is not None:
            filtered_qs = filtered_qs.filter(_min_price__gte=price_min)
        if price_max is not None:
            filtered_qs = filtered_qs.filter(_max_price__lte=price_max)
        
        # Stock filter
        if in_stock:
            # Product has stock if any variant has stock
            filtered_qs = filtered_qs.filter(
                Q(variants__stock_qty__isnull=True) | Q(variants__stock_qty__gt=0)
            ).distinct()
        
        # =====================================================================
        # Sorting
        # =====================================================================
        
        sort_field = SORT_OPTIONS.get(sort_key, SORT_OPTIONS["name_asc"])[0]
        filtered_qs = filtered_qs.order_by(sort_field)
        
        # =====================================================================
        # Pagination
        # =====================================================================
        
        total = filtered_qs.count()
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        page = max(1, min(page, total_pages))  # Clamp to valid range
        
        offset = (page - 1) * page_size
        products = list(filtered_qs[offset:offset + page_size])
        
        # =====================================================================
        # Build response
        # =====================================================================
        
        # Serialize products
        products_data = [self._serialize_product(p) for p in products]
        
        # Build category breadcrumbs
        breadcrumbs = [
            {"name": c.name, "slug": c.slug}
            for c in category.breadcrumbs
        ]
        
        return Response({
            "category": {
                "id": str(category.id),
                "name": category.name,
                "slug": category.slug,
                "description_short": category.description_short,
                "cover_media_url": f"/api/v1/media/{category.cover_media_id}/file" if category.cover_media_id else None,
                "breadcrumbs": breadcrumbs,
            },
            "products": products_data,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
            "facets": {
                "brands": brand_facets,
                "categories": category_facets,
                "price": price_facet,
                "series": series_facets,
                "attributes": attribute_facets,
            },
            "selected_filters": {
                "brands": brand_slugs,
                "price_min": float(price_min) if price_min else None,
                "price_max": float(price_max) if price_max else None,
                "in_stock": in_stock or False,
                # Simple serialization for series/attrs for now
                "series": parse_comma_list(request.query_params.get("series")),
                "attrs": request.query_params.get("attrs"),
            },
            "sort": sort_key,
            "sort_options": [
                {"key": k, "label": v[1]} for k, v in SORT_OPTIONS.items()
            ],
        })
    
    def _compute_brand_facets(self, queryset, selected_brands: list[str]) -> list[dict]:
        """Compute brand facet counts."""
        brand_counts = (
            queryset
            .filter(brand__isnull=False, brand__is_active=True)
            .values("brand__id", "brand__name", "brand__slug", "brand__logo_media_id")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count", "brand__name")
        )
        
        return [
            {
                "id": str(bc["brand__id"]),
                "name": bc["brand__name"],
                "slug": bc["brand__slug"],
                "count": bc["count"],
                "logo_url": f"/api/v1/media/{bc['brand__logo_media_id']}/file/" if bc["brand__logo_media_id"] else None,
                "selected": bc["brand__slug"] in selected_brands,
            }
            for bc in brand_counts
        ]
    
    def _compute_price_facet(self, queryset) -> dict:
        """Compute price range from all products."""
        agg = queryset.aggregate(
            min_price=Min("variants__list_price"),
            max_price=Max("variants__list_price"),
        )
        return {
            "min": float(agg["min_price"]) if agg["min_price"] else 0,
            "max": float(agg["max_price"]) if agg["max_price"] else 0,
        }
    
    def _compute_category_facets(self, root_category: Category, category_ids: list, queryset) -> list[dict]:
        """Compute subcategory facet counts."""
        # Get direct children of root category
        children = Category.objects.filter(parent=root_category).order_by("order", "name")
        
        # If no children, show alternatives:
        if not children.exists():
            if root_category.parent_id:
                # Has a parent: show sibling categories (same parent, excluding self)
                children = Category.objects.filter(
                    parent_id=root_category.parent_id
                ).exclude(id=root_category.id).order_by("order", "name")
            else:
                # Is a root category: show other root categories (excluding self)
                children = Category.objects.filter(
                    parent_id__isnull=True
                ).exclude(id=root_category.id).order_by("order", "name")
        
        facets = []
        for child in children:
            child_ids = get_category_subtree_ids(child)
            
            # For sibling/root categories, we need to query ALL products, not just current category
            # Use a fresh queryset
            count = (
                Product.objects
                .filter(
                    Q(series__category_id__in=child_ids) | Q(category_id__in=child_ids),
                    status=Product.Status.ACTIVE,
                )
                .distinct()
                .count()
            )
            
            if count > 0:
                facets.append({
                    "id": str(child.id),
                    "name": child.name,
                    "slug": child.slug,
                    "count": count,
                    "depth": child.depth,
                })
        
        return facets

    def _compute_series_facets(self, queryset) -> list[dict]:
        """Compute series counts."""
        series_counts = (
            queryset
            .filter(series__isnull=False)
            .values("series__id", "series__name", "series__slug")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count", "series__name")
        )
        
        return [
            {
                "id": str(sc["series__id"]),
                "name": sc["series__name"],
                "slug": sc["series__slug"],
                "count": sc["count"],
            }
            for sc in series_counts
        ]

    def _compute_attribute_facets(self, queryset) -> list[dict]:
        """
        Compute dynamic attribute facets from Variant specs.
        Iterates over known FACET_ATTRIBUTE_KEYS.
        """
        facets = []
        
        # We need to inspect variants of the filtered products
        # This can be expensive, so we specific keys only
        
        for key, label in FACET_ATTRIBUTE_KEYS:
            # Group by specific json key
            # Django ORM supports KeyTextTransform/KeyTransform for JSON
            # But simple approach: filter products with variants having this key
            
            # Get all values for this key from variants of these products
            # We use a raw-ish approach or simple annotation if possible
            # Standard ORM for JSON grouping is tricky across DBs, but Postgres supports it.
            
            # Safer approach for now:
            # 1. Filter variants present in these products
            # 2. Extract specific key
            # 3. Aggregation
            
            # Using JSON_EXTRACT equivalent in Django:
            values = (
                Variant.objects
                .filter(product__in=queryset)
                .values(value=Case(
                    When(specs__has_key=key, then=F(f"specs__{key}")),
                    default=None
                ))
                .filter(value__isnull=False)
                .annotate(count=Count("product", distinct=True))
                .order_by("-count", "value")
            )
            
            if values:
                options = []
                for v in values:
                    val_str = str(v["value"]).strip()
                    if val_str:
                        options.append({
                            "value": val_str,
                            "count": v["count"],
                            "label": val_str, # Could be mapped if needed
                        })
                
                if options:
                    facets.append({
                        "key": key,
                        "label": label,
                        "options": options
                    })
                    
        return facets
    
    def _serialize_product(self, product: Product) -> dict:
        """Serialize a product for PLP response."""
        # Get primary image
        hero_image_url = None
        product_media_list = list(product.product_media.all())
        if product_media_list:
            primary = next((pm for pm in product_media_list if pm.is_primary), None)
            if not primary:
                primary = product_media_list[0]
            if primary and primary.media_id:
                hero_image_url = f"/api/v1/media/{primary.media_id}/file/"
        
        # Price info
        price_info = None
        if product._min_price is not None:
            price_info = {
                "min": float(product._min_price),
                "max": float(product._max_price) if product._max_price else float(product._min_price),
                "currency": "TRY",
            }
        
        return {
            "id": str(product.id),
            "slug": product.slug,
            "name": product.name,
            "title_tr": product.title_tr,
            "brand": {
                "id": str(product.brand.id),
                "name": product.brand.name,
                "slug": product.brand.slug,
            } if product.brand else None,
            "hero_image_url": hero_image_url,
            "price": price_info,
            "in_stock": getattr(product, "_has_stock", True),
            "short_specs": product.short_specs[:3] if product.short_specs else [],
        }
