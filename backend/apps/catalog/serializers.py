"""
DRF Serializers for Gastrotech catalog public APIs.

Provides clean serializers for:
- Media metadata (without bytes)
- SpecKeys for specification tables
- Categories and category trees
- Series
- TaxonomyNodes and trees
- Variants with spec rows
- Products (list and detail views)
"""

from rest_framework import serializers

from .models import (
    Brand,
    BrandCategory,
    CatalogAsset,
    Category,
    CategoryCatalog,
    CategoryLogoGroup,
    LogoGroupSeries,
    Media,
    Product,
    ProductMedia,
    Series,
    SpecKey,
    TaxonomyNode,
    Variant,
)


# =============================================================================
# Media Serializers
# =============================================================================


class MediaMetadataSerializer(serializers.ModelSerializer):
    """
    Media metadata serializer - excludes binary bytes.
    
    Provides file_url for streaming endpoint.
    """
    
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Media
        fields = [
            "id",
            "kind",
            "filename",
            "content_type",
            "size_bytes",
            "width",
            "height",
            "checksum_sha256",
            "file_url",
        ]
    
    def get_file_url(self, obj):
        """Generate URL for file streaming endpoint."""
        return f"/api/v1/media/{obj.id}/file/"


# =============================================================================
# SpecKey Serializers
# =============================================================================


class SpecKeySerializer(serializers.ModelSerializer):
    """Serializer for specification keys."""
    
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
        ]
        read_only_fields = ["slug"]


# =============================================================================
# Brand Serializers
# =============================================================================


class BrandCategorySerializer(serializers.ModelSerializer):
    """Serializer for brand-category associations."""

    category_name = serializers.CharField(source="category.name", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)

    class Meta:
        model = BrandCategory
        fields = [
            "id",
            "category",
            "category_name",
            "category_slug",
            "is_active",
            "order",
        ]


class BrandListSerializer(serializers.ModelSerializer):
    """Brand list serializer with logo and category count."""

    logo_url = serializers.SerializerMethodField()
    category_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = [
            "id",
            "name",
            "slug",
            "logo_url",
            "is_active",
            "order",
            "category_count",
        ]

    def get_logo_url(self, obj):
        """Generate URL for logo streaming endpoint."""
        if obj.logo_media:
            return f"/api/v1/media/{obj.logo_media.id}/file/"
        return None

    def get_category_count(self, obj):
        """Return count of categories this brand is in."""
        return obj.categories.count()


class BrandDetailSerializer(serializers.ModelSerializer):
    """Brand detail serializer with categories and products count."""

    logo_url = serializers.SerializerMethodField()
    categories_list = BrandCategorySerializer(source="brand_categories", many=True, read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "website_url",
            "logo_url",
            "is_active",
            "order",
            "categories_list",
            "product_count",
            "created_at",
            "updated_at",
        ]

    def get_logo_url(self, obj):
        """Generate URL for logo streaming endpoint."""
        if obj.logo_media:
            return f"/api/v1/media/{obj.logo_media.id}/file/"
        return None

    def get_product_count(self, obj):
        """Return count of products for this brand."""
        return obj.products.count()


# =============================================================================
# Logo Group Serializers
# =============================================================================


class LogoGroupSeriesSerializer(serializers.ModelSerializer):
    """Serializer for series within a logo group."""
    
    series_id = serializers.UUIDField(source='series.id', read_only=True)
    series_name = serializers.CharField(source='series.name', read_only=True)
    series_slug = serializers.CharField(source='series.slug', read_only=True)
    cover_media_url = serializers.SerializerMethodField()
    
    class Meta:
        model = LogoGroupSeries
        fields = [
            'series_id',
            'series_name',
            'series_slug',
            'order',
            'is_heading',
            'cover_media_url',
        ]
    
    def get_cover_media_url(self, obj):
        """Return cover media URL for the series."""
        if obj.series.cover_media_id:
            return f"/api/v1/media/{obj.series.cover_media_id}/file/"
        return None


class CategoryLogoGroupSerializer(serializers.ModelSerializer):
    """
    Serializer for category logo groups.
    
    Returns brand info with associated series for logo grid navigation.
    """
    
    brand_id = serializers.UUIDField(source='brand.id', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    brand_slug = serializers.CharField(source='brand.slug', read_only=True)
    logo_url = serializers.SerializerMethodField()
    series_list = serializers.SerializerMethodField()
    
    class Meta:
        model = CategoryLogoGroup
        fields = [
            'id',
            'brand_id',
            'brand_name',
            'brand_slug',
            'title',
            'logo_url',
            'order',
            'is_active',
            'series_list',
        ]
    
    def get_logo_url(self, obj):
        """Return brand logo URL."""
        if obj.brand.logo_media_id:
            return f"/api/v1/media/{obj.brand.logo_media_id}/file/"
        return None
    
    def get_series_list(self, obj):
        """Return ordered series for this logo group."""
        logo_series = obj.logo_group_series.select_related('series').order_by('order')
        return LogoGroupSeriesSerializer(logo_series, many=True).data


# =============================================================================
# Category Serializers
# =============================================================================


class CategoryListSerializer(serializers.ModelSerializer):
    """Category list serializer with cover media URL."""
    
    cover_media_url = serializers.SerializerMethodField()
    parent_slug = serializers.SerializerMethodField()
    
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
            "cover_media_url",
            "parent_slug",
        ]
    
    def get_cover_media_url(self, obj):
        """Return file URL if cover media exists."""
        if obj.cover_media_id:
            return f"/api/v1/media/{obj.cover_media_id}/file/"
        return None
    
    def get_parent_slug(self, obj):
        """Return parent category slug if exists."""
        if obj.parent:
            return obj.parent.slug
        return None


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Category tree serializer with recursive children and counts."""

    cover_media_url = serializers.SerializerMethodField()
    parent_slug = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    is_leaf = serializers.SerializerMethodField()
    products_count = serializers.IntegerField(read_only=True, default=0)
    subcategory_count = serializers.IntegerField(read_only=True, default=0)

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
            "cover_media_url",
            "parent_slug",
            "is_leaf",
            "products_count",
            "subcategory_count",
            "children",
        ]

    def get_cover_media_url(self, obj):
        """Return file URL if cover media exists."""
        if obj.cover_media_id:
            return f"/api/v1/media/{obj.cover_media_id}/file/"
        return None

    def get_parent_slug(self, obj):
        """Return parent category slug if exists."""
        if obj.parent:
            return obj.parent.slug
        return None

    def get_is_leaf(self, obj):
        """Return True if category has no children."""
        children = getattr(obj, "_prefetched_children", None)
        if children is not None:
            return len(children) == 0
        # Fallback if subcategory_count is annotated
        count = getattr(obj, "subcategory_count", None)
        if count is not None:
            return count == 0
        return obj.is_leaf

    def get_children(self, obj):
        """Recursively serialize children."""
        children = getattr(obj, "_prefetched_children", None)
        if children is None:
            children = obj.children.all()
        return CategoryTreeSerializer(children, many=True, context=self.context).data


class CategoryChildrenSerializer(serializers.ModelSerializer):
    """Serializer for subcategories (immediate children only) with product counts."""

    cover_media_url = serializers.SerializerMethodField()
    parent_slug = serializers.SerializerMethodField()
    products_count = serializers.IntegerField(read_only=True, default=0)

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
            "cover_media_url",
            "parent_slug",
            "products_count",
        ]

    def get_cover_media_url(self, obj):
        """Return file URL if cover media exists."""
        if obj.cover_media_id:
            return f"/api/v1/media/{obj.cover_media_id}/file/"
        return None

    def get_parent_slug(self, obj):
        """Return parent category slug."""
        return obj.parent.slug if obj.parent else None


class CategoryListWithCountsSerializer(CategoryListSerializer):
    """
    Category list serializer with series and product counts.

    Used for categories page entry point.
    """

    series_count = serializers.IntegerField(read_only=True)
    products_count = serializers.IntegerField(read_only=True)

    class Meta(CategoryListSerializer.Meta):
        fields = CategoryListSerializer.Meta.fields + [
            "series_count",
            "products_count",
        ]


class SeriesWithCountsSerializer(serializers.ModelSerializer):
    """
    Series serializer with product count and visibility info.

    Used in category detail page to show series with counts.

    Visibility rule:
    - is_visible = True when products_count >= 2
    - Series with 0 or 1 product should not appear as navigation groupings
    """

    category_slug = serializers.CharField(source="category.slug", read_only=True)
    cover_media_url = serializers.SerializerMethodField()
    products_count = serializers.IntegerField(read_only=True)
    is_visible = serializers.SerializerMethodField()
    single_product_slug = serializers.SerializerMethodField()
    single_product_name = serializers.SerializerMethodField()
    single_product_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Series
        fields = [
            "id",
            "category_slug",
            "name",
            "slug",
            "description_short",
            "order",
            "is_featured",
            "cover_media_url",
            "products_count",
            "is_visible",
            "single_product_slug",
            "single_product_name",
            "single_product_image_url",
        ]

    def get_cover_media_url(self, obj):
        """Return file URL if cover media exists."""
        if obj.cover_media_id:
            return f"/api/v1/media/{obj.cover_media_id}/file/"
        return None

    def get_is_visible(self, obj):
        """
        Return visibility status based on product count.

        Uses annotated _is_visible if available, otherwise computes from products_count.
        """
        if hasattr(obj, '_is_visible'):
            return obj._is_visible
        # Fall back to products_count annotation
        products_count = getattr(obj, 'products_count', None)
        if products_count is not None:
            return products_count >= 2
        # Fall back to model property
        return obj.is_visible

    def get_single_product_slug(self, obj):
        """
        Return product slug if series contains exactly one active product.
        
        This allows frontend to skip series selection step.
        """
        products_count = getattr(obj, 'products_count', None)
        if products_count is None:
            products_count = obj.products.filter(status='active').count()
            
        if products_count == 1:
            product = obj.products.filter(status='active').first()
            return product.slug if product else None
        return None

    def get_single_product_name(self, obj):
        """Return product name if series contains exactly one active product."""
        products_count = getattr(obj, 'products_count', None)
        if products_count is None:
            products_count = obj.products.filter(status='active').count()
            
        if products_count == 1:
            product = obj.products.filter(status='active').first()
            # Try to return the Turkish title first, fallback to name
            return product.title_tr or product.name if product else None
        return None

    def get_single_product_image_url(self, obj):
        """Return product primary image URL if series contains exactly one active product."""
        products_count = getattr(obj, 'products_count', None)
        if products_count is None:
            products_count = obj.products.filter(status='active').count()
            
        if products_count == 1:
            product = obj.products.filter(status='active').first()
            if product and product.primary_image:
                 return f"/api/v1/media/{product.primary_image.id}/file/"
        return None


class CategoryDetailSerializer(serializers.ModelSerializer):
    """
    Category detail serializer with series list and counts.

    Used for category detail page showing series within category.

    Visibility behavior:
    - series: All series with product counts and visibility flags
    - visible_series: Only series with 2+ products (for navigation)
    - subcategories: Child categories for hierarchical navigation
    - The frontend can choose which to display based on context
    """

    cover_media_url = serializers.SerializerMethodField()
    parent_slug = serializers.SerializerMethodField()
    series = SeriesWithCountsSerializer(many=True, read_only=True)
    visible_series = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()
    logo_groups = serializers.SerializerMethodField()
    products_count = serializers.IntegerField(read_only=True)
    series_mode = serializers.CharField(read_only=True)

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
            "cover_media_url",
            "parent_slug",
            "series_mode",
            "subcategories",
            "logo_groups",
            "series",
            "visible_series",
            "products_count",
        ]

    def get_cover_media_url(self, obj):
        """Return file URL if cover media exists."""
        if obj.cover_media_id:
            return f"/api/v1/media/{obj.cover_media_id}/file/"
        return None

    def get_parent_slug(self, obj):
        """Return parent category slug if exists."""
        if obj.parent:
            return obj.parent.slug
        return None

    def get_visible_series(self, obj):
        """
        Return only series that should be visible in navigation (2+ products).

        This is a convenience field for frontends that want pre-filtered series.
        """
        # Filter prefetched series by visibility
        series_list = getattr(obj, 'series', None)
        if series_list is None:
            return []

        # If it's a prefetched queryset with annotations
        if hasattr(series_list, 'all'):
            series_list = series_list.all()

        visible = []
        for s in series_list:
            products_count = getattr(s, 'products_count', None)
            if products_count is not None and products_count >= 2:
                visible.append(s)
            elif products_count is None and s.is_visible:
                visible.append(s)

        return SeriesWithCountsSerializer(visible, many=True).data

    def get_subcategories(self, obj):
        """
        Return child categories for hierarchical navigation.
        
        Used when a category has subcategories (like Hazırlık Ekipmanları).
        """
        children = obj.children.all().order_by('order')
        return CategoryListSerializer(children, many=True).data
    
    def get_logo_groups(self, obj):
        """
        Return logo groups for this category's landing page.
        
        Logo groups enable brand-based navigation where:
        1. Category page shows brand logos
        2. Clicking a logo reveals series grouped under that brand
        
        Returns empty list if no logo groups configured.
        """
        logo_groups = obj.logo_groups.filter(is_active=True).select_related('brand').order_by('order')
        return CategoryLogoGroupSerializer(logo_groups, many=True).data


# =============================================================================
# Series Serializers
# =============================================================================


class SeriesSerializer(serializers.ModelSerializer):
    """Series serializer with category reference."""
    
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    cover_media_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Series
        fields = [
            "id",
            "category_slug",
            "name",
            "slug",
            "description_short",
            "order",
            "is_featured",
            "cover_media_url",
        ]
    
    def get_cover_media_url(self, obj):
        """Return file URL if cover media exists."""
        if obj.cover_media_id:
            return f"/api/v1/media/{obj.cover_media_id}/file/"
        return None


class SeriesWithProductsSerializer(SeriesSerializer):
    """Extended series serializer including product count."""
    
    products_count = serializers.SerializerMethodField()
    
    class Meta(SeriesSerializer.Meta):
        fields = SeriesSerializer.Meta.fields + ["products_count"]
    
    def get_products_count(self, obj):
        """Return count of active products."""
        return getattr(obj, "_products_count", obj.products.filter(status="active").count())


# =============================================================================
# TaxonomyNode Serializers
# =============================================================================


class TaxonomyNodeTreeSerializer(serializers.ModelSerializer):
    """TaxonomyNode tree serializer with recursive children."""
    
    parent_slug = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    depth = serializers.IntegerField(read_only=True)
    full_path = serializers.CharField(read_only=True)
    
    class Meta:
        model = TaxonomyNode
        fields = [
            "id",
            "name",
            "slug",
            "order",
            "parent_slug",
            "children",
            "depth",
            "full_path",
        ]
    
    def get_parent_slug(self, obj):
        """Return parent node slug if exists."""
        if obj.parent:
            return obj.parent.slug
        return None
    
    def get_children(self, obj):
        """Recursively serialize children."""
        children = getattr(obj, "_prefetched_children", None)
        if children is None:
            children = obj.children.all()
        return TaxonomyNodeTreeSerializer(children, many=True, context=self.context).data


# =============================================================================
# Variant Serializers
# =============================================================================


from apps.common.utils import get_show_prices

class VariantSerializer(serializers.ModelSerializer):
    """
    Variant serializer with specs and computed spec_row.
    
    spec_row provides values ordered by Product.spec_layout.
    """
    
    spec_row = serializers.SerializerMethodField()
    
    class Meta:
        model = Variant
        fields = [
            "id",  # UUID for cart operations
            "model_code",
            "name_tr",
            "name_en",
            "dimensions",
            "weight_kg",
            "list_price",
            "specs",
            "spec_row",
        ]

    def to_representation(self, instance):
        """
        Overridden to conditionally hide list_price based on global setting.
        """
        ret = super().to_representation(instance)
        
        # Check global price visibility setting
        if not get_show_prices():
            ret.pop("list_price", None)
            
        return ret
    
    def get_spec_row(self, obj):
        """
        Return spec values ordered by product's spec_layout.
        
        Example: [{"key": "dimensions", "value": "400x630x280"}, ...]
        """
        product = obj.product
        if not product or not product.spec_layout:
            return []
        
        result = []
        for key in product.spec_layout:
            value = obj.specs.get(key)
            # Also check direct attributes for common fields
            if value is None and key == "boyutlar":
                value = obj.dimensions
            elif value is None and key == "agirlik":
                value = str(obj.weight_kg) if obj.weight_kg else None
            
            result.append({
                "key": key,
                "value": value,
            })
        
        return result


# =============================================================================
# Product Media Serializers
# =============================================================================


class ProductMediaSerializer(serializers.ModelSerializer):
    """Product media association serializer."""
    
    # Return ProductMedia id (for delete/reorder operations)
    id = serializers.IntegerField(read_only=True)
    # Also include media UUID for reference
    media_id = serializers.UUIDField(source="media.id", read_only=True)
    kind = serializers.CharField(source="media.kind", read_only=True)
    filename = serializers.CharField(source="media.filename", read_only=True)
    file_url = serializers.SerializerMethodField()
    width = serializers.IntegerField(source="media.width", read_only=True)
    height = serializers.IntegerField(source="media.height", read_only=True)
    
    class Meta:
        model = ProductMedia
        fields = [
            "id",
            "media_id",
            "kind",
            "filename",
            "file_url",
            "width",
            "height",
            "alt",
            "sort_order",
            "is_primary",
            "variant_id",
        ]
    
    def get_file_url(self, obj):
        """Generate URL for file streaming endpoint."""
        if obj.media_id:
            return f"/api/v1/media/{obj.media_id}/file/"
        return None


# =============================================================================
# Product Serializers
# =============================================================================


class ProductListSerializer(serializers.ModelSerializer):
    """
    Product list serializer - optimized for listing views.
    
    Includes essential fields for product cards.
    """
    
    series_slug = serializers.CharField(source="series.slug", read_only=True)
    series_name = serializers.CharField(source="series.name", read_only=True)
    category_slug = serializers.CharField(source="series.category.slug", read_only=True)
    category_name = serializers.CharField(source="series.category.name", read_only=True)
    brand_slug = serializers.CharField(source="brand.slug", read_only=True, allow_null=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True, allow_null=True)
    primary_image_url = serializers.SerializerMethodField()
    variants_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            "title_tr",
            "title_en",
            "slug",
            "series_slug",
            "series_name",
            "category_slug",
            "category_name",
            "brand_slug",
            "brand_name",
            "status",
            "is_featured",
            "pdf_ref",
            "primary_image_url",
            "variants_count",
        ]
    
    def get_primary_image_url(self, obj):
        """Return URL for primary product image."""
        # Try prefetched media first
        product_media = getattr(obj, "_prefetched_objects_cache", {}).get("product_media")
        if product_media is not None:
            for pm in product_media:
                if pm.is_primary:
                    return f"/api/v1/media/{pm.media_id}/file/"
            # Fallback to first
            if product_media:
                first = min(product_media, key=lambda x: x.sort_order)
                return f"/api/v1/media/{first.media_id}/file/"
        
        # Fallback to property
        primary = obj.primary_image
        if primary:
            return f"/api/v1/media/{primary.id}/file/"
        return None
    
    def get_variants_count(self, obj):
        """Return count of variants."""
        # Try annotated count first
        if hasattr(obj, "_variants_count"):
            return obj._variants_count
        return obj.variants.count()


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Product detail serializer - full catalog page data.
    
    Includes everything needed to render PDF-like page.
    """
    
    series_slug = serializers.CharField(source="series.slug", read_only=True)
    series_name = serializers.CharField(source="series.name", read_only=True)
    category_slug = serializers.CharField(source="series.category.slug", read_only=True)
    category_name = serializers.CharField(source="series.category.name", read_only=True)
    brand_slug = serializers.CharField(source="brand.slug", read_only=True, allow_null=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True, allow_null=True)
    brand_logo = serializers.SerializerMethodField()
    primary_node_slug = serializers.SerializerMethodField()
    spec_keys_resolved = serializers.SerializerMethodField()
    variants = VariantSerializer(many=True, read_only=True)
    product_media = ProductMediaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            "id",
            "title_tr",
            "title_en",
            "slug",
            "series_slug",
            "series_name",
            "category_slug",
            "category_name",
            "brand_slug",
            "brand_name",
            "brand_logo",
            "primary_node_slug",
            "status",
            "is_featured",
            "pdf_ref",
            "general_features",
            "notes",
            "spec_layout",
            "spec_keys_resolved",
            "variants",
            "product_media",
            "long_description",
            "seo_title",
            "seo_description",
        ]
    
    def get_brand_logo(self, obj):
        """Return brand logo URL if brand has a logo."""
        if obj.brand and obj.brand.logo_media_id:
            return f"/api/v1/media/{obj.brand.logo_media_id}/file/"
        return None
    
    def get_primary_node_slug(self, obj):
        """Return primary taxonomy node slug."""
        if obj.primary_node:
            return obj.primary_node.slug
        return None
    
    def get_spec_keys_resolved(self, obj):
        """Return ordered SpecKey objects based on spec_layout."""
        spec_keys = obj.get_spec_keys()
        return SpecKeySerializer(spec_keys, many=True).data


# =============================================================================
# Navigation Serializers
# =============================================================================


class NavSeriesSerializer(serializers.ModelSerializer):
    """
    Minimal series serializer for navigation.

    Includes visibility flag so frontend can filter single-product series.
    """

    products_count = serializers.SerializerMethodField()
    is_visible = serializers.SerializerMethodField()
    single_product_slug = serializers.SerializerMethodField()
    single_product_name = serializers.SerializerMethodField()
    single_product_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Series
        fields = [
            "id",
            "name",
            "slug",
            "order",
            "is_featured",
            "products_count",
            "is_visible",
            "single_product_slug",
            "single_product_name",
            "single_product_image_url",
        ]
    def get_products_count(self, obj):
        """Return product count from annotation or compute."""
        if hasattr(obj, '_product_count'):
            return obj._product_count
        if hasattr(obj, 'products_count'):
            return obj.products_count
        return obj.products.filter(status='active').count()

    def get_is_visible(self, obj):
        """Return visibility status."""
        return self.get_products_count(obj) >= 2 or getattr(obj, 'is_visible', False)

    def _get_single_product(self, obj):
        """
        Return the single active product if count == 1, else None.

        Caches the result on the serializer instance to avoid
        repeated queries for slug, name, and image URL fields.
        """
        cache_attr = f"_cached_single_product_{obj.pk}"
        if hasattr(self, cache_attr):
            return getattr(self, cache_attr)

        product = None
        count = self.get_products_count(obj)
        if count == 1:
            # Use prefetched products if available
            prefetched = getattr(obj, '_prefetched_objects_cache', {})
            if 'products' in prefetched:
                active = [p for p in prefetched['products'] if p.status == 'active']
                product = active[0] if active else None
            else:
                product = obj.products.filter(status='active').only(
                    'slug', 'title_tr', 'name'
                ).first()

        setattr(self, cache_attr, product)
        return product

    def get_single_product_slug(self, obj):
        """Return product slug if series contains exactly one active product."""
        product = self._get_single_product(obj)
        return product.slug if product else None

    def get_single_product_name(self, obj):
        """Return product name if series contains exactly one active product."""
        product = self._get_single_product(obj)
        return (product.title_tr or product.name) if product else None

    def get_single_product_image_url(self, obj):
        """Return product primary image URL if series contains exactly one active product."""
        product = self._get_single_product(obj)
        if product:
            img = product.primary_image
            if img:
                return f"/api/v1/media/{img.id}/file/"
        return None




class NavCategorySerializer(serializers.ModelSerializer):
    """Category serializer for navigation with nested series."""

    series = NavSeriesSerializer(many=True, read_only=True)
    visible_series = serializers.SerializerMethodField()
    cover_media_url = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    parent_slug = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "menu_label",
            "order",
            "is_featured",
            "cover_media_url",
            "series",
            "visible_series",
            "children",
            "parent_slug",
        ]

    def get_cover_media_url(self, obj):
        """Return file URL if cover media exists."""
        if obj.cover_media_id:
            return f"/api/v1/media/{obj.cover_media_id}/file/"
        return None

    def get_visible_series(self, obj):
        """
        Return only visible series (2+ products) for navigation.

        This filters out single-product series that should not appear
        as navigation groupings.
        """
        series_list = getattr(obj, 'series', None)
        if series_list is None:
            return []

        if hasattr(series_list, 'all'):
            series_list = series_list.all()

        visible = []
        for s in series_list:
            # Check for annotated count first
            count = getattr(s, '_product_count', None)
            if count is None:
                count = getattr(s, 'products_count', None)
            if count is None:
                count = s.product_count

            if count >= 2:
                visible.append(s)

        return NavSeriesSerializer(visible, many=True, context=self.context).data

    def get_children(self, obj):
        """Recursively serialize children."""
        children = getattr(obj, "_prefetched_children", None)
        if children is None:
            children = obj.children.all()
        return NavCategorySerializer(children, many=True, context=self.context).data

    def get_parent_slug(self, obj):
        """Return parent category slug."""
        return obj.parent.slug if obj.parent else None



# =============================================================================
# Catalog Asset Serializers
# =============================================================================


class CatalogAssetSerializer(serializers.ModelSerializer):
    """Serializer for catalog assets (PDF downloads)."""
    
    file_url = serializers.SerializerMethodField()
    file_size = serializers.IntegerField(source="media.size_bytes", read_only=True)
    
    class Meta:
        model = CatalogAsset
        fields = [
            "id",
            "title_tr",
            "title_en",
            "is_primary",
            "order",
            "file_url",
            "file_size",
        ]
    
    def get_file_url(self, obj):
        """Generate URL for file download."""
        if obj.media_id:
            return f"/api/v1/media/{obj.media_id}/file/"
        return None


# =============================================================================
# Variant Lookup Serializers
# =============================================================================


class VariantLookupSerializer(serializers.Serializer):
    """
    Serializer for variant lookup response.
    
    Returns variant details with full hierarchy info.
    Used by /api/v1/variants/by-codes endpoint.
    """
    
    model_code = serializers.CharField()
    name_tr = serializers.CharField(allow_null=True)
    name_en = serializers.CharField(allow_null=True)
    product_slug = serializers.CharField(allow_null=True)
    product_title_tr = serializers.CharField(allow_null=True)
    series_slug = serializers.CharField(allow_null=True)
    series_name = serializers.CharField(allow_null=True)
    category_slug = serializers.CharField(allow_null=True)
    category_name = serializers.CharField(allow_null=True)
    dimensions = serializers.CharField(allow_null=True)
    weight_kg = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    list_price = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    specs = serializers.JSONField(allow_null=True)
    error = serializers.CharField(allow_null=True)


# =============================================================================
# Category Catalog Serializers
# =============================================================================


class CategoryCatalogSerializer(serializers.ModelSerializer):
    """Serializer for category catalog PDFs (public)."""

    file_url = serializers.SerializerMethodField()
    file_size = serializers.IntegerField(source="media.size_bytes", read_only=True)
    filename = serializers.CharField(source="media.filename", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = CategoryCatalog
        fields = [
            "id",
            "title_tr",
            "title_en",
            "description",
            "order",
            "file_url",
            "file_size",
            "filename",
            "category_slug",
            "category_name",
        ]

    def get_file_url(self, obj):
        """Generate URL for file download."""
        if obj.media_id:
            return f"/api/v1/media/{obj.media_id}/file/"
        return None
