"""
Admin serializers for catalog CRUD operations.

These serializers are used for admin endpoints that allow
creating, updating, and managing catalog entities.
"""

from rest_framework import serializers

from .models import (
    Brand,
    BrandCategory,
    CatalogAsset,
    Category,
    CategoryCatalog,
    Media,
    Product,
    ProductMedia,
    ProductNode,
    Series,
    SpecKey,
    SpecTemplate,
    TaxonomyNode,
    Variant,
)


# =============================================================================
# Brand Admin Serializers
# =============================================================================


class AdminBrandSerializer(serializers.ModelSerializer):
    """Full CRUD serializer for brands."""
    
    logo_media_url = serializers.SerializerMethodField(read_only=True)
    products_count = serializers.IntegerField(read_only=True, required=False)
    categories = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Category.objects.all(),
        many=True,
        required=False
    )
    
    class Meta:
        model = Brand
        fields = [
            "id",
            "name",
            "slug",
            "logo_media",
            "logo_media_url",
            "description",
            "website_url",
            "is_active",
            "order",
            "categories",
            "products_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "logo_media_url", "products_count"]
        extra_kwargs = {
            "website_url": {"required": False, "allow_blank": True},
            "slug": {"required": False, "allow_blank": True},
        }
    
    def get_logo_media_url(self, obj):
        if obj.logo_media_id:
            return f"/api/v1/media/{obj.logo_media_id}/file"
        return None

    def create(self, validated_data):
        categories = validated_data.pop("categories", [])
        brand = super().create(validated_data)
        
        # Create brand categories with order
        for index, category in enumerate(categories):
            BrandCategory.objects.create(
                brand=brand,
                category=category,
                order=index,
                is_active=True
            )
        return brand

    def update(self, instance, validated_data):
        categories = validated_data.pop("categories", None)
        brand = super().update(instance, validated_data)
        
        if categories is not None:
            # Sync categories (full replacement strategy to support reordering)
            # This is simpler and correct for "edit form" behavior where the list is the source of truth
            from django.db import transaction
            
            with transaction.atomic():
                # Clear existing
                brand.brand_categories.all().delete()
                
                # Re-create with new order
                batch = [
                    BrandCategory(
                        brand=brand,
                        category=category,
                        order=index,
                        is_active=True
                    )
                    for index, category in enumerate(categories)
                ]
                BrandCategory.objects.bulk_create(batch)
        
        return brand


# =============================================================================
# Category Admin Serializers
# =============================================================================


class AdminCategorySerializer(serializers.ModelSerializer):
    """Full CRUD serializer for categories."""
    
    cover_media_url = serializers.SerializerMethodField(read_only=True)
    parent_slug = serializers.SlugRelatedField(
        source="parent",
        slug_field="slug",
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
    )
    products_count = serializers.IntegerField(read_only=True, required=False)
    series_count = serializers.IntegerField(read_only=True, required=False)
    
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "menu_label",
            "description_short",
            "order",
            "is_featured",
            "cover_media",
            "cover_media_url",
            "parent",
            "parent_slug",
            "products_count",
            "series_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "cover_media_url", "products_count", "series_count"]
        extra_kwargs = {
            "slug": {"required": False, "allow_blank": True},
        }
        validators = []  # Disable implicit UniqueTogetherValidator due to field aliasing
    
    def get_cover_media_url(self, obj):
        if obj.cover_media_id:
            return f"/api/v1/media/{obj.cover_media_id}/file"
        return None


class AdminSeriesSerializer(serializers.ModelSerializer):
    """Full CRUD serializer for series."""
    
    cover_media_url = serializers.SerializerMethodField(read_only=True)
    category_slug = serializers.SlugRelatedField(
        source="category",
        slug_field="slug",
        queryset=Category.objects.all(),
    )
    products_count = serializers.IntegerField(read_only=True, required=False)
    
    class Meta:
        model = Series
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "category_slug",
            "description_short",
            "order",
            "is_featured",
            "cover_media",
            "cover_media_url",
            "products_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "cover_media_url", "category", "products_count"]
        extra_kwargs = {
            "slug": {"required": False, "allow_blank": True},
        }
        validators = []  # Disable implicit UniqueTogetherValidator due to field aliasing
    
    def get_cover_media_url(self, obj):
        if obj.cover_media_id:
            return f"/api/v1/media/{obj.cover_media_id}/file"
        return None
        
class AdminCategoryDetailSerializer(AdminCategorySerializer):
    """Detail serializer for categories including series."""
    series = AdminSeriesSerializer(many=True, read_only=True)
    
    class Meta(AdminCategorySerializer.Meta):
        fields = AdminCategorySerializer.Meta.fields + ["series"]


# =============================================================================
# TaxonomyNode Admin Serializers
# =============================================================================


class AdminTaxonomyNodeSerializer(serializers.ModelSerializer):
    """Full CRUD serializer for taxonomy nodes."""
    
    series_slug = serializers.SlugRelatedField(
        source="series",
        slug_field="slug",
        queryset=Series.objects.all(),
    )
    parent_id = serializers.PrimaryKeyRelatedField(
        source="parent",
        queryset=TaxonomyNode.objects.all(),
        required=False,
        allow_null=True,
    )
    full_path = serializers.CharField(read_only=True)
    depth = serializers.IntegerField(read_only=True)
    is_leaf = serializers.SerializerMethodField()
    
    class Meta:
        model = TaxonomyNode
        fields = [
            "id",
            "name",
            "slug",
            "series",
            "series_slug",
            "parent",
            "parent_id",
            "order",
            "full_path",
            "depth",
            "is_leaf",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "full_path", "depth", "series", "parent"]
        extra_kwargs = {
            "slug": {"required": False, "allow_blank": True},
        }
        validators = []  # Disable implicit UniqueTogetherValidator due to field aliasing (handled by DB)
    
    def get_is_leaf(self, obj):
        return not obj.children.exists()


# =============================================================================
# SpecKey Admin Serializers
# =============================================================================


class AdminSpecKeySerializer(serializers.ModelSerializer):
    """Full CRUD serializer for spec keys."""
    
    class Meta:
        model = SpecKey
        fields = [
            "id",
            "slug",
            "label_tr",
            "label_en",
            "unit",
            "value_type",
            "sort_order",
            "icon_media",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# =============================================================================
# SpecTemplate Admin Serializers
# =============================================================================


class AdminSpecTemplateSerializer(serializers.ModelSerializer):
    """Full CRUD serializer for spec templates."""
    
    applies_to_series_slug = serializers.SlugRelatedField(
        source="applies_to_series",
        slug_field="slug",
        queryset=Series.objects.all(),
        required=False,
        allow_null=True,
    )
    
    class Meta:
        model = SpecTemplate
        fields = [
            "id",
            "name",
            "spec_layout",
            "default_general_features",
            "default_notes",
            "applies_to_series",
            "applies_to_series_slug",
            "applies_to_parent_taxonomy_slug",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def validate_spec_layout(self, value):
        """Validate that all slugs in spec_layout exist."""
        if value:
            valid_slugs = set(SpecKey.objects.values_list("slug", flat=True))
            invalid_slugs = [s for s in value if s not in valid_slugs]
            if invalid_slugs:
                raise serializers.ValidationError(
                    f"Invalid SpecKey slugs: {', '.join(invalid_slugs)}"
                )
        return value


# =============================================================================
# Product Admin Serializers
# =============================================================================


class AdminProductListSerializer(serializers.ModelSerializer):
    """Lightweight product serializer for list views."""
    
    series_slug = serializers.CharField(source="series.slug", read_only=True)
    series_name = serializers.CharField(source="series.name", read_only=True)
    category_slug = serializers.CharField(source="series.category.slug", read_only=True)
    category_name = serializers.CharField(source="series.category.name", read_only=True)
    primary_node_slug = serializers.CharField(source="primary_node.slug", read_only=True, allow_null=True)
    brand_slug = serializers.CharField(source="brand.slug", read_only=True, allow_null=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True, allow_null=True)
    variants_count = serializers.SerializerMethodField()
    primary_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "title_tr",
            "title_en",
            "series_slug",
            "series_name",
            "category_slug",
            "category_name",
            "primary_node_slug",
            "brand_slug",
            "brand_name",
            "status",
            "is_featured",
            "pdf_ref",
            "variants_count",
            "primary_image_url",
            "created_at",
            "updated_at",
        ]
    
    def get_variants_count(self, obj):
        if hasattr(obj, "_variants_count"):
            return obj._variants_count
        return obj.variants.count()
    
    def get_primary_image_url(self, obj):
        primary = obj.primary_image
        if primary:
            return f"/api/v1/media/{primary.id}/file"
        return None


class AdminProductDetailSerializer(serializers.ModelSerializer):
    """Full product serializer for detail/update views."""
    
    series_slug = serializers.SlugRelatedField(
        source="series",
        slug_field="slug",
        queryset=Series.objects.all(),
    )
    series_name = serializers.CharField(source="series.name", read_only=True)
    category_slug = serializers.CharField(source="series.category.slug", read_only=True)
    category_name = serializers.CharField(source="series.category.name", read_only=True)
    primary_node_slug = serializers.SlugRelatedField(
        source="primary_node",
        slug_field="slug",
        queryset=TaxonomyNode.objects.all(),
        required=False,
        allow_null=True,
    )
    brand_slug = serializers.SlugRelatedField(
        source="brand",
        slug_field="slug",
        queryset=Brand.objects.all(),
        required=False,
        allow_null=True,
    )
    brand_name = serializers.CharField(source="brand.name", read_only=True, allow_null=True)
    nodes = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=TaxonomyNode.objects.all(),
        required=False,
    )
    
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "title_tr",
            "title_en",
            "series",
            "series_slug",
            "series_name",
            "category_slug",
            "category_name",
            "primary_node",
            "primary_node_slug",
            "brand",
            "brand_slug",
            "brand_name",
            "nodes",
            "status",
            "is_featured",
            "general_features",
            "notes",
            "spec_layout",
            "pdf_ref",
            "short_specs",
            "long_description",
            "seo_title",
            "seo_description",
            "og_media",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "series_name", "category_slug", "category_name", "brand_name", "series", "brand", "primary_node"]
        extra_kwargs = {
            "slug": {"required": False, "allow_blank": True},
        }
    
    def validate_spec_layout(self, value):
        """Validate that all slugs in spec_layout exist."""
        if value:
            valid_slugs = set(SpecKey.objects.values_list("slug", flat=True))
            invalid_slugs = [s for s in value if s not in valid_slugs]
            if invalid_slugs:
                raise serializers.ValidationError(
                    f"Invalid SpecKey slugs: {', '.join(invalid_slugs)}"
                )
        return value
    
    def validate_status(self, value):
        """Validate status is in allowed values."""
        allowed = [choice[0] for choice in Product.Status.choices]
        if value not in allowed:
            raise serializers.ValidationError(
                f"Status must be one of: {', '.join(allowed)}"
            )
        return value


class AdminProductUpdateSerializer(serializers.ModelSerializer):
    """Simplified serializer for patching product fields."""
    
    primary_node_slug = serializers.SlugRelatedField(
        source="primary_node",
        slug_field="slug",
        queryset=TaxonomyNode.objects.all(),
        required=False,
        allow_null=True,
    )
    brand_slug = serializers.SlugRelatedField(
        source="brand",
        slug_field="slug",
        queryset=Brand.objects.all(),
        required=False,
        allow_null=True,
    )
    
    class Meta:
        model = Product
        fields = [
            "title_tr",
            "title_en",
            "status",
            "is_featured",
            "general_features",
            "notes",
            "spec_layout",
            "primary_node",
            "primary_node_slug",
            "brand",
            "brand_slug",
            "pdf_ref",
            "long_description",
            "seo_title",
            "seo_description",
        ]
    
    def validate_spec_layout(self, value):
        """Validate that all slugs in spec_layout exist."""
        if value:
            valid_slugs = set(SpecKey.objects.values_list("slug", flat=True))
            invalid_slugs = [s for s in value if s not in valid_slugs]
            if invalid_slugs:
                raise serializers.ValidationError(
                    f"Invalid SpecKey slugs: {', '.join(invalid_slugs)}"
                )
        return value


# =============================================================================
# Variant Admin Serializers
# =============================================================================


class AdminVariantSerializer(serializers.ModelSerializer):
    """Full CRUD serializer for variants."""
    
    # Use product_slug for both read and write
    product_slug = serializers.SlugRelatedField(
        source="product",
        slug_field="slug",
        queryset=Product.objects.all(),
    )
    # product UUID is read-only (use product_slug for writes)
    product = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Variant
        fields = [
            "id",
            "model_code",
            "name_tr",
            "name_en",
            "product",
            "product_slug",
            "sku",
            "dimensions",
            "weight_kg",
            "list_price",
            "price_override",
            "specs",
            "size",
            "color",
            "stock_qty",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "product", "created_at", "updated_at"]


class AdminVariantUpdateSerializer(serializers.ModelSerializer):
    """Simplified serializer for patching variant fields."""
    
    class Meta:
        model = Variant
        fields = [
            "name_tr",
            "name_en",
            "dimensions",
            "weight_kg",
            "list_price",
            "price_override",
            "specs",
            "stock_qty",
        ]


class VariantBulkUpdateItemSerializer(serializers.Serializer):
    """Serializer for a single item in bulk update."""
    
    model_code = serializers.CharField()
    name_tr = serializers.CharField(required=False)
    name_en = serializers.CharField(required=False, allow_blank=True)
    dimensions = serializers.CharField(required=False, allow_blank=True)
    weight_kg = serializers.DecimalField(
        max_digits=10, decimal_places=3, required=False, allow_null=True
    )
    list_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    specs = serializers.JSONField(required=False)
    stock_qty = serializers.IntegerField(required=False)


class VariantBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk variant update request."""
    
    updates = VariantBulkUpdateItemSerializer(many=True)


# =============================================================================
# Taxonomy Generate Products Serializers
# =============================================================================


class TaxonomyGenerateProductsRequestSerializer(serializers.Serializer):
    """Request serializer for generating products from leaf nodes."""
    
    series = serializers.CharField(help_text="Series slug")
    leaf_slugs = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of leaf node slugs to generate products for"
    )
    dry_run = serializers.BooleanField(
        default=False,
        help_text="If true, only return preview without creating products"
    )
    status = serializers.ChoiceField(
        choices=["draft", "active", "archived"],
        default="draft",
        help_text="Status for newly created products"
    )
    template_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Optional SpecTemplate ID to apply to new products"
    )


class TaxonomyGenerateProductsResponseSerializer(serializers.Serializer):
    """Response serializer for generate products endpoint."""
    
    created = serializers.IntegerField()
    skipped_existing = serializers.IntegerField()
    skipped_non_leaf = serializers.IntegerField()
    created_slugs = serializers.ListField(child=serializers.CharField())
    errors = serializers.ListField(child=serializers.DictField(), required=False)


# =============================================================================
# Apply Template Serializers
# =============================================================================


class ApplyTemplateRequestSerializer(serializers.Serializer):
    """Request serializer for applying a spec template."""
    
    template_id = serializers.UUIDField()
    overwrite = serializers.BooleanField(default=False)


class ApplyTemplateResponseSerializer(serializers.Serializer):
    """Response serializer for apply template endpoint."""

    updated_fields = serializers.ListField(child=serializers.CharField())
    message = serializers.CharField()


# =============================================================================
# Bulk Brand Update Serializers
# =============================================================================


class BulkBrandUpdateRequestSerializer(serializers.Serializer):
    """Request serializer for bulk brand update."""

    # Selection mode: either explicit IDs or filter-based
    product_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="Explicit list of product UUIDs to update"
    )

    # Alternative: use filters to select products
    filters = serializers.DictField(
        required=False,
        help_text="Filter criteria to select products (series, category, status, search)"
    )

    # Target brand
    brand_slug = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Brand.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        help_text="Target brand slug (null to remove brand)"
    )

    # Two-phase pattern
    dry_run = serializers.BooleanField(
        default=True,
        help_text="If true, only preview changes without committing"
    )

    def validate(self, data):
        """Ensure either product_ids or filters is provided."""
        if not data.get("product_ids") and not data.get("filters"):
            raise serializers.ValidationError(
                "Either 'product_ids' or 'filters' must be provided"
            )
        return data


class BulkBrandUpdateResponseSerializer(serializers.Serializer):
    """Response serializer for bulk brand update."""

    affected_count = serializers.IntegerField(
        help_text="Number of products that will be/were updated"
    )
    products_preview = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Preview of first N products to be updated (dry_run only)"
    )
    dry_run = serializers.BooleanField()
    message = serializers.CharField()


# =============================================================================
# Category Catalog Admin Serializer
# =============================================================================


class AdminCategoryCatalogSerializer(serializers.ModelSerializer):
    """Full CRUD serializer for category catalogs."""

    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(parent__isnull=True),
        help_text="Only root (parent) categories are allowed.",
    )
    category_name = serializers.CharField(source="category.name", read_only=True)
    media_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CategoryCatalog
        fields = [
            "id",
            "category",
            "category_name",
            "title_tr",
            "title_en",
            "description",
            "media",
            "media_details",
            "order",
            "published",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_media_details(self, obj):
        if not obj.media:
            return None
        return {
            "id": str(obj.media.id),
            "filename": obj.media.filename,
            "size_bytes": obj.media.size_bytes,
            "content_type": obj.media.content_type,
            "file_url": f"/api/v1/media/{obj.media.id}/file/",
        }


# =============================================================================
# Catalog Asset Admin Serializer
# =============================================================================


class AdminCatalogAssetSerializer(serializers.ModelSerializer):
    """Full CRUD serializer for catalog assets (downloadable PDFs)."""

    media_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CatalogAsset
        fields = [
            "id",
            "title_tr",
            "title_en",
            "media",
            "media_details",
            "is_primary",
            "order",
            "published",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_media_details(self, obj):
        if not obj.media:
            return None
        return {
            "id": str(obj.media.id),
            "filename": obj.media.filename,
            "size_bytes": obj.media.size_bytes,
            "content_type": obj.media.content_type,
            "file_url": f"/api/v1/media/{obj.media.id}/file/",
        }
