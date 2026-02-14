"""
Admin ViewSets for catalog CRUD operations.

Provides DRF ViewSets for admin panel operations:
- Categories, Series, TaxonomyNodes CRUD
- Products CRUD with overview fields
- Variants CRUD with bulk update
- SpecTemplates and SpecKeys
- Taxonomy leaf → Product generation
- Apply SpecTemplate to Product
"""

from django.db import transaction
from django.db.models import Count, F
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import IsAdminOrEditor

from django.utils import timezone

from .admin_serializers import (
    AdminBrandSerializer,
    AdminCategorySerializer,
    AdminCategoryDetailSerializer,
    AdminProductDetailSerializer,
    AdminProductListSerializer,
    AdminProductUpdateSerializer,
    AdminSeriesSerializer,
    AdminSpecKeySerializer,
    AdminSpecTemplateSerializer,
    AdminTaxonomyNodeSerializer,
    AdminVariantSerializer,
    AdminVariantUpdateSerializer,
    ApplyTemplateRequestSerializer,
    ApplyTemplateResponseSerializer,
    AdminCatalogAssetSerializer,
    AdminCategoryCatalogSerializer,
    BulkBrandUpdateRequestSerializer,
    BulkBrandUpdateResponseSerializer,
    TaxonomyGenerateProductsRequestSerializer,
    TaxonomyGenerateProductsResponseSerializer,
    VariantBulkUpdateSerializer,
)
from .models import (
    Brand,
    CatalogAsset,
    Category,
    CategoryCatalog,
    Product,
    Series,
    SpecKey,
    SpecTemplate,
    TaxonomyNode,
    Variant,
)
from .services import create_product_for_leaf_node


# =============================================================================
# Brand ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List brands", tags=["Admin - Brands"]),
    retrieve=extend_schema(summary="Get brand", tags=["Admin - Brands"]),
    create=extend_schema(summary="Create brand", tags=["Admin - Brands"]),
    update=extend_schema(summary="Update brand", tags=["Admin - Brands"]),
    partial_update=extend_schema(summary="Partial update brand", tags=["Admin - Brands"]),
    destroy=extend_schema(summary="Delete brand", tags=["Admin - Brands"]),
)
class AdminBrandViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for brands."""
    
    permission_classes = [IsAdminOrEditor]
    serializer_class = AdminBrandSerializer
    queryset = Brand.objects.all().select_related("logo_media")
    lookup_field = "slug"
    
    def get_queryset(self):
        queryset = super().get_queryset().annotate(products_count=Count("products"))
        # Filter by is_active if requested
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("order", "name")


# =============================================================================
# Category ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List categories", tags=["Admin - Categories"]),
    retrieve=extend_schema(summary="Get category", tags=["Admin - Categories"]),
    create=extend_schema(summary="Create category", tags=["Admin - Categories"]),
    update=extend_schema(summary="Update category", tags=["Admin - Categories"]),
    partial_update=extend_schema(summary="Partial update category", tags=["Admin - Categories"]),
    destroy=extend_schema(summary="Delete category", tags=["Admin - Categories"]),
)
class AdminCategoryViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for categories."""
    
    permission_classes = [IsAdminOrEditor]
    queryset = Category.objects.all().select_related("parent", "cover_media")
    lookup_field = "slug"
    
    def get_serializer_class(self):
        if self.action == "retrieve":
            return AdminCategoryDetailSerializer
        return AdminCategorySerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Annotate with counts
        # Annotate with counts (including immediate subcategories)
        queryset = queryset.annotate(
            direct_products=Count("series__products", distinct=True),
            child_products=Count("children__series__products", distinct=True),
            series_count=Count("series", distinct=True)
        ).annotate(
            products_count=F("direct_products") + F("child_products")
        )
        
        # Filter by parent if requested
        parent_slug = self.request.query_params.get("parent")
        if parent_slug:
            if parent_slug == "null":
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent__slug=parent_slug)
        return queryset.order_by("order", "name")


# =============================================================================
# Series ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List series", tags=["Admin - Series"]),
    retrieve=extend_schema(summary="Get series", tags=["Admin - Series"]),
    create=extend_schema(summary="Create series", tags=["Admin - Series"]),
    update=extend_schema(summary="Update series", tags=["Admin - Series"]),
    partial_update=extend_schema(summary="Partial update series", tags=["Admin - Series"]),
    destroy=extend_schema(summary="Delete series", tags=["Admin - Series"]),
)
class AdminSeriesViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for series."""
    
    permission_classes = [IsAdminOrEditor]
    serializer_class = AdminSeriesSerializer
    queryset = Series.objects.all().select_related("category", "cover_media")
    lookup_field = "slug"
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Annotate with products count
        queryset = queryset.annotate(products_count=Count("products"))
        
        # Filter by category if requested
        category_slug = self.request.query_params.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset.order_by("category__order", "order", "name")


# =============================================================================
# TaxonomyNode ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List taxonomy nodes", tags=["Admin - Taxonomy"]),
    retrieve=extend_schema(summary="Get taxonomy node", tags=["Admin - Taxonomy"]),
    create=extend_schema(summary="Create taxonomy node", tags=["Admin - Taxonomy"]),
    update=extend_schema(summary="Update taxonomy node", tags=["Admin - Taxonomy"]),
    partial_update=extend_schema(summary="Partial update taxonomy node", tags=["Admin - Taxonomy"]),
    destroy=extend_schema(summary="Delete taxonomy node", tags=["Admin - Taxonomy"]),
)
class AdminTaxonomyNodeViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for taxonomy nodes."""
    
    permission_classes = [IsAdminOrEditor]
    serializer_class = AdminTaxonomyNodeSerializer
    queryset = TaxonomyNode.objects.all().select_related("series", "parent")
    lookup_field = "id"
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by series if requested
        series_slug = self.request.query_params.get("series")
        if series_slug:
            queryset = queryset.filter(series__slug=series_slug)
        
        # Filter by parent if requested
        parent_id = self.request.query_params.get("parent")
        if parent_id:
            if parent_id == "null":
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent_id)
        
        # Filter to leaf nodes only if requested
        leaf_only = self.request.query_params.get("leaf_only")
        if leaf_only and leaf_only.lower() in ("true", "1"):
            # Annotate with children count and filter
            queryset = queryset.annotate(
                children_count=Count("children")
            ).filter(children_count=0)
        
        return queryset.order_by("series__order", "order", "name")


# =============================================================================
# SpecKey ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List spec keys", tags=["Admin - SpecKeys"]),
    retrieve=extend_schema(summary="Get spec key", tags=["Admin - SpecKeys"]),
    create=extend_schema(summary="Create spec key", tags=["Admin - SpecKeys"]),
    update=extend_schema(summary="Update spec key", tags=["Admin - SpecKeys"]),
    partial_update=extend_schema(summary="Partial update spec key", tags=["Admin - SpecKeys"]),
    destroy=extend_schema(summary="Delete spec key", tags=["Admin - SpecKeys"]),
)
class AdminSpecKeyViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for specification keys."""
    
    permission_classes = [IsAdminOrEditor]
    serializer_class = AdminSpecKeySerializer
    queryset = SpecKey.objects.all()
    lookup_field = "slug"
    
    def get_queryset(self):
        return super().get_queryset().order_by("sort_order", "label_tr")


# =============================================================================
# SpecTemplate ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List spec templates", tags=["Admin - SpecTemplates"]),
    retrieve=extend_schema(summary="Get spec template", tags=["Admin - SpecTemplates"]),
    create=extend_schema(summary="Create spec template", tags=["Admin - SpecTemplates"]),
    update=extend_schema(summary="Update spec template", tags=["Admin - SpecTemplates"]),
    partial_update=extend_schema(summary="Partial update spec template", tags=["Admin - SpecTemplates"]),
    destroy=extend_schema(summary="Delete spec template", tags=["Admin - SpecTemplates"]),
)
class AdminSpecTemplateViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for spec templates."""
    
    permission_classes = [IsAdminOrEditor]
    serializer_class = AdminSpecTemplateSerializer
    queryset = SpecTemplate.objects.all().select_related("applies_to_series")
    lookup_field = "id"
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by series if requested
        series_slug = self.request.query_params.get("series")
        if series_slug:
            queryset = queryset.filter(applies_to_series__slug=series_slug)
        
        return queryset.order_by("name")


# =============================================================================
# Product ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List products", tags=["Admin - Products"]),
    retrieve=extend_schema(summary="Get product", tags=["Admin - Products"]),
    create=extend_schema(summary="Create product", tags=["Admin - Products"]),
    update=extend_schema(summary="Update product", tags=["Admin - Products"]),
    partial_update=extend_schema(summary="Partial update product", tags=["Admin - Products"]),
    destroy=extend_schema(summary="Delete product", tags=["Admin - Products"]),
)
class AdminProductViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for products."""
    
    permission_classes = [IsAdminOrEditor]
    queryset = Product.objects.all().select_related(
        "series", "series__category", "primary_node"
    ).prefetch_related("product_media__media", "variants")
    lookup_field = "slug"
    
    def get_object(self):
        """Support lookup by both slug and UUID."""
        queryset = self.filter_queryset(self.get_queryset())
        lookup_value = self.kwargs.get(self.lookup_field)
        
        # Try to parse as UUID first
        import uuid
        try:
            uuid.UUID(lookup_value)
            filter_kwargs = {"id": lookup_value}
        except (ValueError, AttributeError):
            # Not a UUID, treat as slug
            filter_kwargs = {"slug": lookup_value}
        
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj
    
    def get_serializer_class(self):
        if self.action == "list":
            return AdminProductListSerializer
        elif self.action in ("update", "partial_update"):
            return AdminProductUpdateSerializer
        return AdminProductDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Annotate with variants count
        queryset = queryset.annotate(_variants_count=Count("variants"))
        
        # Filter by series
        series_slug = self.request.query_params.get("series")
        if series_slug:
            queryset = queryset.filter(series__slug=series_slug)
            
        # Filter by category
        category_slug = self.request.query_params.get("category")
        if category_slug:
            queryset = queryset.filter(series__category__slug=category_slug)
            
        # Filter by brand
        brand_slug = self.request.query_params.get("brand")
        if brand_slug:
            queryset = queryset.filter(brand__slug=brand_slug)
        
        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by is_featured
        is_featured = self.request.query_params.get("is_featured")
        if is_featured:
            queryset = queryset.filter(is_featured=is_featured.lower() in ("true", "1"))
        
        # Search
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(title_tr__icontains=search)
        
        # Ordering
        ordering = self.request.query_params.get("ordering", "-created_at")
        valid_orderings = [
            "created_at", "-created_at",
            "updated_at", "-updated_at",
            "title_tr", "-title_tr",
            "status", "-status",
        ]
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    @extend_schema(
        summary="Apply spec template to product",
        request=ApplyTemplateRequestSerializer,
        responses={200: ApplyTemplateResponseSerializer},
        tags=["Admin - Products"],
    )
    @action(detail=True, methods=["post"], url_path="apply-template")
    def apply_template(self, request, slug=None):
        """Apply a SpecTemplate to this product."""
        product = self.get_object()

        serializer = ApplyTemplateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        template_id = serializer.validated_data["template_id"]
        overwrite = serializer.validated_data.get("overwrite", False)

        try:
            template = SpecTemplate.objects.get(id=template_id)
        except SpecTemplate.DoesNotExist:
            return Response(
                {"error": f"SpecTemplate with id {template_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        updated_fields = template.apply_to_product(product, overwrite=overwrite)

        return Response({
            "updated_fields": updated_fields,
            "message": f"Applied template '{template.name}' to product. Updated: {', '.join(updated_fields) or 'nothing'}",
        })

    @extend_schema(
        summary="Bulk update product brands",
        description="Update brand for multiple products at once. Supports dry_run mode for preview.",
        request=BulkBrandUpdateRequestSerializer,
        responses={200: BulkBrandUpdateResponseSerializer},
        tags=["Admin - Products"],
    )
    @action(detail=False, methods=["post"], url_path="bulk-update-brand")
    def bulk_update_brand(self, request):
        """Bulk update brand for multiple products."""
        serializer = BulkBrandUpdateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        product_ids = data.get("product_ids", [])
        filters = data.get("filters", {})
        brand = data.get("brand_slug")  # This is already the Brand instance due to SlugRelatedField
        dry_run = data.get("dry_run", True)

        # Build queryset
        queryset = Product.objects.all()

        if product_ids:
            queryset = queryset.filter(id__in=product_ids)
        elif filters:
            if filters.get("series"):
                queryset = queryset.filter(series__slug=filters["series"])
            if filters.get("category"):
                queryset = queryset.filter(series__category__slug=filters["category"])
            if filters.get("status"):
                queryset = queryset.filter(status=filters["status"])
            if filters.get("search"):
                queryset = queryset.filter(title_tr__icontains=filters["search"])
            if filters.get("brand"):
                # Filter by current brand (for "change from X to Y" scenarios)
                if filters["brand"] == "__null__":
                    queryset = queryset.filter(brand__isnull=True)
                else:
                    queryset = queryset.filter(brand__slug=filters["brand"])

        affected_count = queryset.count()

        # Preview (limit to first 20)
        preview = []
        if dry_run:
            preview_qs = queryset.select_related("brand", "series")[:20]
            for p in preview_qs:
                preview.append({
                    "id": str(p.id),
                    "slug": p.slug,
                    "title_tr": p.title_tr,
                    "current_brand": p.brand.name if p.brand else None,
                    "new_brand": brand.name if brand else None,
                })

        # Execute update if not dry_run
        if not dry_run:
            with transaction.atomic():
                queryset.update(brand=brand, updated_at=timezone.now())

        brand_name = brand.name if brand else "Yok"
        return Response({
            "affected_count": affected_count,
            "products_preview": preview,
            "dry_run": dry_run,
            "message": f"{'Güncellenecek' if dry_run else 'Güncellendi'}: {affected_count} ürün → Marka: '{brand_name}'",
        })


# =============================================================================
# Variant ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List variants", tags=["Admin - Variants"]),
    retrieve=extend_schema(summary="Get variant", tags=["Admin - Variants"]),
    create=extend_schema(summary="Create variant", tags=["Admin - Variants"]),
    update=extend_schema(summary="Update variant", tags=["Admin - Variants"]),
    partial_update=extend_schema(summary="Partial update variant", tags=["Admin - Variants"]),
    destroy=extend_schema(summary="Delete variant", tags=["Admin - Variants"]),
)
class AdminVariantViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for variants with bulk update support."""
    
    permission_classes = [IsAdminOrEditor]
    queryset = Variant.objects.all().select_related("product", "product__series")
    lookup_field = "model_code"
    
    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return AdminVariantUpdateSerializer
        return AdminVariantSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by product
        product_slug = self.request.query_params.get("product")
        if product_slug:
            queryset = queryset.filter(product__slug=product_slug)
        
        # Search by model_code
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(model_code__icontains=search)
        
        return queryset.order_by("product__title_tr", "model_code")
    
    @extend_schema(
        summary="Bulk update variants",
        description="Update multiple variants by model_code in a single request.",
        request=VariantBulkUpdateSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "updated": {"type": "integer"},
                    "not_found": {"type": "array", "items": {"type": "string"}},
                    "errors": {"type": "array", "items": {"type": "object"}},
                },
            }
        },
        tags=["Admin - Variants"],
    )
    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_update(self, request):
        """Bulk update variants by model_code."""
        serializer = VariantBulkUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        updates = serializer.validated_data["updates"]
        
        result = {
            "updated": 0,
            "not_found": [],
            "errors": [],
        }
        
        with transaction.atomic():
            for item in updates:
                model_code = item.pop("model_code")
                
                try:
                    variant = Variant.objects.get(model_code=model_code)
                except Variant.DoesNotExist:
                    result["not_found"].append(model_code)
                    continue
                
                try:
                    # Update fields
                    for field, value in item.items():
                        if value is not None:
                            setattr(variant, field, value)
                    variant.save()
                    result["updated"] += 1
                except Exception as e:
                    result["errors"].append({
                        "model_code": model_code,
                        "error": str(e),
                    })
        
        return Response(result)


# =============================================================================
# Taxonomy Generate Products View
# =============================================================================


class TaxonomyGenerateProductsView(APIView):
    """
    Generate Product pages from leaf taxonomy nodes.
    
    POST /api/v1/admin/taxonomy/generate-products
    
    Supports dry_run mode to preview what would be created.
    """
    
    permission_classes = [IsAdminOrEditor]
    
    @extend_schema(
        summary="Generate products from leaf nodes",
        description="Create Product pages for specified leaf taxonomy nodes. Use dry_run=true to preview.",
        request=TaxonomyGenerateProductsRequestSerializer,
        responses={200: TaxonomyGenerateProductsResponseSerializer},
        tags=["Admin - Taxonomy"],
    )
    def post(self, request):
        serializer = TaxonomyGenerateProductsRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        series_slug = serializer.validated_data["series"]
        leaf_slugs = serializer.validated_data["leaf_slugs"]
        dry_run = serializer.validated_data.get("dry_run", False)
        product_status = serializer.validated_data.get("status", "draft")
        template_id = serializer.validated_data.get("template_id")
        
        # Find series
        try:
            series = Series.objects.get(slug=series_slug)
        except Series.DoesNotExist:
            return Response(
                {"error": f"Series with slug '{series_slug}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Get template if specified
        template = None
        if template_id:
            try:
                template = SpecTemplate.objects.get(id=template_id)
            except SpecTemplate.DoesNotExist:
                return Response(
                    {"error": f"SpecTemplate with id '{template_id}' not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        
        result = {
            "created": 0,
            "skipped_existing": 0,
            "skipped_non_leaf": 0,
            "created_slugs": [],
            "skipped_existing_slugs": [],
            "preview": [],
            "errors": [],
            "dry_run": dry_run,
        }
        
        # Process each node
        for node_slug in leaf_slugs:
            # Find node
            try:
                node = TaxonomyNode.objects.get(series=series, slug=node_slug)
            except TaxonomyNode.DoesNotExist:
                result["errors"].append({
                    "slug": node_slug,
                    "error": "Node not found in this series",
                })
                continue
            
            # Check if leaf
            if node.children.exists():
                result["skipped_non_leaf"] += 1
                continue
            
            # Generate expected slug
            from .services import slugify_tr
            expected_slug = f"{series.slug}-serisi-{slugify_tr(node.name)}"
            
            # Check if product already exists
            existing = Product.objects.filter(
                series=series,
                primary_node=node,
            ).first()
            
            if existing:
                result["skipped_existing"] += 1
                result["skipped_existing_slugs"].append(existing.slug)
                result["preview"].append({
                    "node_slug": node_slug,
                    "node_path": node.full_path,
                    "expected_slug": existing.slug,
                    "status": "exists",
                    "existing_product_slug": existing.slug,
                })
                continue
            
            # Add to preview
            result["preview"].append({
                "node_slug": node_slug,
                "node_path": node.full_path,
                "expected_slug": expected_slug,
                "status": "will_create",
                "existing_product_slug": None,
            })
            
            # If dry_run, don't actually create
            if dry_run:
                result["created"] += 1
                result["created_slugs"].append(expected_slug)
                continue
            
            # Create product
            try:
                with transaction.atomic():
                    product = create_product_for_leaf_node(node, status=product_status)
                    
                    # Apply template if specified
                    if template:
                        template.apply_to_product(product, overwrite=False)
                    
                    result["created"] += 1
                    result["created_slugs"].append(product.slug)
            except Exception as e:
                result["errors"].append({
                    "slug": node_slug,
                    "error": str(e),
                })
        
        return Response(result)

# =============================================================================
# Bulk Upload ViewSet
# =============================================================================


class BulkUploadViewSet(viewsets.ViewSet):
    """
    ViewSet for handling bulk product uploads.
    """
    permission_classes = [IsAdminOrEditor]

    @extend_schema(
        summary="Bulk upload products via Excel",
        description="Upload an Excel file to create/update catalog items in bulk.",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "Excel file (.xlsx)"
                    },
                    "dry_run": {
                        "type": "boolean",
                        "default": True,
                        "description": "If true, simulates the upload without saving changes."
                    }
                },
                "required": ["file"]
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "categories_created": {"type": "integer"},
                    "series_created": {"type": "integer"},
                    "brands_created": {"type": "integer"},
                    "products_created": {"type": "integer"},
                    "products_updated": {"type": "integer"},
                    "variants_created": {"type": "integer"},
                    "variants_updated": {"type": "integer"},
                    "rows_processed": {"type": "integer"},
                    "errors": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "dry_run": {"type": "boolean"}
                }
            }
        },
        tags=["Admin - Bulk Upload"]
    )
    def create(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check dry_run param - handle 'true' string from form data
        dry_run = request.data.get("dry_run", "true")
        if isinstance(dry_run, str):
            dry_run = dry_run.lower() == "true"
            
        from .services.bulk_upload import BulkUploadService
        service = BulkUploadService(file_obj)
        
        try:
            service.validate_and_parse()
            results = service.process_data(dry_run=dry_run)
            results["dry_run"] = dry_run
            return Response(results)
        except Exception as e:
            return Response(
                {"error": str(e), "details": service.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Download Excel template",
        description="Download a blank Excel template with required headers.",
        responses={
            200: OpenApiParameter(
                name="Content-Type",
                description="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        tags=["Admin - Bulk Upload"]
    )
    @action(detail=False, methods=["get"], url_path="template")
    def download_template(self, request):
        """Generate and return an Excel template file."""
        # Import all dependencies at the top for reliability
        import logging
        import traceback
        import pandas as pd
        from io import BytesIO
        from django.http import HttpResponse
        from rest_framework.response import Response
        from .services.bulk_upload import BulkUploadService
        
        logger = logging.getLogger(__name__)
        
        try:
            logger.info("Starting Excel template generation")
            
            # Create DataFrame with minimal example or just headers
            # We can also add comment rows or examples
            
            headers = BulkUploadService.REQUIRED_COLUMNS + [
                 "Taxonomy", "Title EN", "Dimensions", "Weight", "Price", "Spec:Power", "Spec:Capacity"
            ]
            
            # Create an example row
            example_data = {
                "Brand": ["Gastrotech"],
                "Category": ["Pişirme"],
                "Series": ["900 Serisi"],
                "Product Name": ["Gazlı Ocak 4'lü"],
                "Model Code": ["GKO9010"],
                "Title TR": ["Gazlı Ocak 4'lü"],
                "Taxonomy": ["Ocaklar > Gazlı"],
                "Title EN": ["Gas Cooker 4 Burner"],
                "Dimensions": ["800x900x850"],
                "Weight": [120],
                "Price": [15000],
                "Spec:Power": ["24kW"],
                "Spec:Capacity": ["4 Burner"]
            }
            
            logger.info("Creating DataFrame with example data")
            df = pd.DataFrame(example_data)
            
            # Clear data if we want strict blank (optional, but example is better)
            # df = pd.DataFrame(columns=headers) 
            
            logger.info("Generating Excel file with openpyxl")
            output = BytesIO()
            
            # Use context manager to ensure proper cleanup
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
                
                # Auto-adjust column widths (optional, requires more openpyxl logic)
                try:
                    worksheet = writer.sheets['Sheet1']
                    for idx, col in enumerate(df.columns):
                        # max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                        col_letter = chr(65 + idx) if idx < 26 else 'Z' # Simple fallback
                        worksheet.column_dimensions[col_letter].width = 20
                except Exception as e:
                    logger.warning(f"Column width adjustment failed: {e}")
                    # Non-critical, continue
                    
            output.seek(0)
            excel_data = output.read()
            
            if not excel_data:
                raise ValueError("Generated Excel file is empty")
            
            logger.info(f"Successfully generated Excel template ({len(excel_data)} bytes)")
            
            filename = "bulk_upload_template.xlsx"
            response = HttpResponse(
                excel_data,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = f"attachment; filename={filename}"
            return response
            
        except ImportError as e:
            logger.error(f"Import error in template generation: {e}")
            logger.error(traceback.format_exc())
            return Response(
                {"detail": f"Missing required library: {str(e)}. Please ensure pandas and openpyxl are installed."},
                status=500
            )
        except Exception as e:
            logger.error(f"Template generation failed: {e}")
            logger.error(traceback.format_exc())
            return Response(
                {"detail": f"Template generation failed: {str(e)}"},
                status=500
            )


# =============================================================================
# Category Catalog ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List category catalogs", tags=["Admin - Category Catalogs"]),
    retrieve=extend_schema(summary="Get category catalog", tags=["Admin - Category Catalogs"]),
    create=extend_schema(summary="Create category catalog", tags=["Admin - Category Catalogs"]),
    update=extend_schema(summary="Update category catalog", tags=["Admin - Category Catalogs"]),
    partial_update=extend_schema(summary="Partial update category catalog", tags=["Admin - Category Catalogs"]),
    destroy=extend_schema(summary="Delete category catalog", tags=["Admin - Category Catalogs"]),
)
class AdminCategoryCatalogViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for category catalogs (PDF per category)."""

    permission_classes = [IsAdminOrEditor]
    serializer_class = AdminCategoryCatalogSerializer
    pagination_class = None

    def get_queryset(self):
        qs = CategoryCatalog.objects.select_related("category", "media").order_by("order", "title_tr")

        category_slug = self.request.query_params.get("category_slug")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        return qs


# =============================================================================
# Catalog Asset ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List catalog assets", tags=["Admin - Catalog Assets"]),
    retrieve=extend_schema(summary="Get catalog asset", tags=["Admin - Catalog Assets"]),
    create=extend_schema(summary="Create catalog asset", tags=["Admin - Catalog Assets"]),
    update=extend_schema(summary="Update catalog asset", tags=["Admin - Catalog Assets"]),
    partial_update=extend_schema(summary="Partial update catalog asset", tags=["Admin - Catalog Assets"]),
    destroy=extend_schema(summary="Delete catalog asset", tags=["Admin - Catalog Assets"]),
)
class AdminCatalogAssetViewSet(viewsets.ModelViewSet):
    """CRUD ViewSet for catalog assets (downloadable PDFs)."""

    permission_classes = [IsAdminOrEditor]
    serializer_class = AdminCatalogAssetSerializer
    pagination_class = None

    def get_queryset(self):
        return CatalogAsset.objects.select_related("media").order_by("order", "title_tr")
