"""
Django Admin configuration for Gastrotech catalog.

Provides a rich admin interface for managing:
- Categories, Series, TaxonomyNodes
- Products (catalog groups) with variants and media
- SpecKeys for specification management
- Media files
"""

import json

from django.contrib import admin, messages
from django.db.models import Count
from django.utils.html import format_html, mark_safe

from .forms import MediaAdminForm
from .models import (
    Brand,
    BrandCategory,
    CatalogAsset,
    Category,
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
# Inlines
# =============================================================================


class ProductMediaInline(admin.TabularInline):
    """Inline for managing product media associations."""
    
    model = ProductMedia
    extra = 1
    fields = ["thumbnail_preview", "media", "alt", "sort_order", "is_primary"]
    readonly_fields = ["thumbnail_preview"]
    ordering = ["sort_order"]
    autocomplete_fields = ["media"]
    
    def thumbnail_preview(self, obj):
        """Show thumbnail preview of media using the API endpoint."""
        if obj.pk and obj.media:
            if obj.media.kind == "image":
                return format_html(
                    '<img src="/api/v1/media/{}/file" '
                    'style="max-width: 60px; max-height: 60px; object-fit: cover; '
                    'border-radius: 4px; border: 1px solid #ddd;" '
                    'alt="{}" title="{}"/>',
                    obj.media.id,
                    obj.alt or obj.media.filename,
                    f"{obj.media.filename} ({obj.media.width}x{obj.media.height})",
                )
            elif obj.media.kind == "pdf":
                return format_html(
                    '<span style="font-size: 24px;" title="{}">📄</span>',
                    obj.media.filename,
                )
            else:
                return format_html(
                    '<span style="font-size: 24px;" title="{}">🎬</span>',
                    obj.media.filename,
                )
        return format_html('<span style="color: #999;">—</span>')
    thumbnail_preview.short_description = ""


class VariantInline(admin.TabularInline):
    """Inline for managing product variants (model lines)."""
    
    model = Variant
    extra = 1
    fields = [
        "model_code",
        "name_tr",
        "dimensions",
        "weight_kg",
        "list_price",
        "stock_qty",
    ]
    ordering = ["model_code"]


class ProductNodeInline(admin.TabularInline):
    """Inline for managing product-node associations."""
    
    model = ProductNode
    extra = 1
    autocomplete_fields = ["node"]


class SeriesInline(admin.TabularInline):
    """Inline for viewing series within a category."""
    
    model = Series
    extra = 0
    fields = ["name", "slug", "order", "is_featured"]
    readonly_fields = ["name", "slug"]
    show_change_link = True
    can_delete = False
    max_num = 0


class TaxonomyNodeInline(admin.TabularInline):
    """Inline for viewing taxonomy nodes within a series."""

    model = TaxonomyNode
    extra = 0
    fields = ["name", "slug", "parent", "order"]
    readonly_fields = ["name", "slug", "parent"]
    show_change_link = True
    can_delete = False
    max_num = 0
    fk_name = "series"


class BrandCategoryInline(admin.TabularInline):
    """Inline for managing brand-category associations (from Brand side)."""

    model = BrandCategory
    extra = 1
    fields = ["category", "is_active", "order"]
    autocomplete_fields = ["category"]
    ordering = ["order", "category__name"]


class CategoryBrandInline(admin.TabularInline):
    """Inline for viewing brands in a category (from Category side)."""

    model = BrandCategory
    extra = 0
    fields = ["brand", "is_active", "order"]
    readonly_fields = ["brand"]
    show_change_link = True
    can_delete = False
    max_num = 0
    fk_name = "category"
    verbose_name = "Brand in this Category"
    verbose_name_plural = "Brands in this Category"


# =============================================================================
# Model Admins
# =============================================================================


@admin.register(SpecKey)
class SpecKeyAdmin(admin.ModelAdmin):
    """Admin for SpecKey model."""
    
    list_display = [
        "slug",
        "label_tr",
        "label_en",
        "unit",
        "value_type",
        "sort_order",
    ]
    list_filter = ["value_type"]
    search_fields = ["slug", "label_tr", "label_en"]
    ordering = ["sort_order", "label_tr"]
    prepopulated_fields = {"slug": ("label_tr",)}
    autocomplete_fields = ["icon_media"]
    
    fieldsets = (
        (None, {
            "fields": ("slug", "label_tr", "label_en"),
        }),
        ("Configuration", {
            "fields": ("unit", "value_type", "sort_order", "icon_media"),
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for Category model."""
    
    list_display = [
        "name",
        "slug",
        "parent",
        "order",
        "is_featured",
        "series_count",
        "brand_count",
    ]
    list_filter = ["is_featured", "parent"]
    search_fields = ["name", "slug", "menu_label"]
    ordering = ["parent__order", "order", "name"]
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["parent", "cover_media"]
    
    fieldsets = (
        (None, {
            "fields": ("name", "slug", "menu_label", "parent"),
        }),
        ("Display", {
            "fields": ("description_short", "order", "is_featured", "cover_media"),
        }),
    )
    
    inlines = [SeriesInline, CategoryBrandInline]

    def series_count(self, obj):
        """Return count of series in this category."""
        return obj.series.count()
    series_count.short_description = "Series"

    def brand_count(self, obj):
        """Return count of brands in this category."""
        count = obj.category_brands.count()
        if count:
            return count
        return format_html('<span style="color: #999;">0</span>')
    brand_count.short_description = "Brands"
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _series_count=Count("series")
        ).prefetch_related("category_brands")


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Admin for Brand model."""

    list_display = [
        "name",
        "slug",
        "is_active",
        "order",
        "category_count",
        "product_count",
        "logo_preview",
        "created_at",
    ]
    list_filter = ["is_active"]
    search_fields = ["name", "slug", "description"]
    ordering = ["order", "name"]
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["logo_media"]
    list_editable = ["order", "is_active"]

    fieldsets = (
        (None, {
            "fields": ("name", "slug", "logo_media"),
        }),
        ("Description", {
            "fields": ("description", "website_url"),
        }),
        ("Settings", {
            "fields": ("is_active", "order"),
        }),
    )

    inlines = [BrandCategoryInline]

    def logo_preview(self, obj):
        """Show brand logo thumbnail."""
        if obj.logo_media and obj.logo_media.kind == "image":
            return format_html(
                '<img src="/api/v1/media/{}/file" '
                'style="max-width: 40px; max-height: 40px; object-fit: contain;" '
                'alt="{}"/>',
                obj.logo_media.id,
                obj.name,
            )
        return format_html('<span style="color: #999;">—</span>')
    logo_preview.short_description = "Logo"

    def category_count(self, obj):
        """Return count of categories this brand is in."""
        count = obj.categories.count()
        if count:
            return count
        return format_html('<span style="color: #999;">0</span>')
    category_count.short_description = "Categories"

    def product_count(self, obj):
        """Return count of products for this brand."""
        count = obj.products.count()
        if count:
            return count
        return format_html('<span style="color: #999;">0</span>')
    product_count.short_description = "Products"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("logo_media").prefetch_related(
            "categories", "products"
        )


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    """Admin for Series model."""
    
    list_display = [
        "name",
        "slug",
        "category",
        "order",
        "is_featured",
        "product_count",
    ]
    list_filter = ["category", "is_featured"]
    search_fields = ["name", "slug"]
    ordering = ["category", "order", "name"]
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["category", "cover_media"]
    
    fieldsets = (
        (None, {
            "fields": ("category", "name", "slug"),
        }),
        ("Display", {
            "fields": ("description_short", "order", "is_featured", "cover_media"),
        }),
    )
    
    inlines = [TaxonomyNodeInline]
    
    def product_count(self, obj):
        """Return count of products in this series."""
        return obj.products.count()
    product_count.short_description = "Products"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category").annotate(
            _product_count=Count("products")
        )


@admin.register(TaxonomyNode)
class TaxonomyNodeAdmin(admin.ModelAdmin):
    """Admin for TaxonomyNode model."""
    
    list_display = [
        "name",
        "slug",
        "series",
        "parent",
        "order",
        "full_path_display",
        "product_count",
    ]
    list_filter = ["series", "series__category"]
    search_fields = ["name", "slug"]
    ordering = ["series", "parent__order", "order", "name"]
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["series", "parent"]
    
    fieldsets = (
        (None, {
            "fields": ("series", "parent", "name", "slug"),
        }),
        ("Display", {
            "fields": ("order",),
        }),
    )
    
    def full_path_display(self, obj):
        """Display full path of node."""
        return obj.full_path
    full_path_display.short_description = "Path"
    
    def product_count(self, obj):
        """Return count of products using this node."""
        return obj.products.count()
    product_count.short_description = "Products"
    
    actions = ["generate_product_groups"]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "series", "series__category", "parent"
        )
    
    @admin.action(description="Generate Product group pages for selected leaf nodes")
    def generate_product_groups(self, request, queryset):
        """
        Generate Product groups for selected leaf taxonomy nodes.
        
        Only creates products for leaf nodes (nodes without children).
        """
        from .services import generate_products_from_leaf_nodes
        
        result = generate_products_from_leaf_nodes(queryset)
        
        self.message_user(
            request,
            f"Created {result['created']} product(s), "
            f"skipped {result['skipped_existing']} existing, "
            f"skipped {result['skipped_non_leaf']} non-leaf nodes.",
            messages.SUCCESS if result['created'] > 0 else messages.WARNING,
        )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for Product model (catalog group)."""
    
    list_display = [
        "title_tr",
        "series",
        "status",
        "is_featured",
        "variant_count",
        "primary_image_preview",
        "pdf_ref",
        "created_at",
    ]
    list_filter = ["status", "is_featured", "series", "series__category"]
    search_fields = ["name", "slug", "title_tr", "title_en"]
    ordering = ["-created_at"]
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["series", "primary_node", "og_media"]
    date_hierarchy = "created_at"
    
    fieldsets = (
        ("Basic Info", {
            "fields": ("name", "slug", "series", "primary_node", "status"),
        }),
        ("Catalog Display", {
            "fields": ("title_tr", "title_en", "is_featured", "pdf_ref"),
        }),
        ("Features & Specs", {
            "fields": (
                "general_features",
                "general_features_display",
                "spec_layout",
                "spec_layout_display",
                "notes",
            ),
        }),
        ("Legacy Content", {
            "fields": ("short_specs", "long_description"),
            "classes": ("collapse",),
        }),
        ("SEO", {
            "fields": ("seo_title", "seo_description", "og_media"),
            "classes": ("collapse",),
        }),
    )
    
    readonly_fields = ["general_features_display", "spec_layout_display"]
    
    inlines = [VariantInline, ProductMediaInline, ProductNodeInline]
    
    def general_features_display(self, obj):
        """Display general features as a formatted list."""
        if not obj.general_features:
            return format_html('<span style="color: #999;">No features</span>')
        
        items = "".join(f"<li>{f}</li>" for f in obj.general_features)
        return format_html(
            '<ul style="margin: 0; padding-left: 20px;">{}</ul>',
            mark_safe(items),
        )
    general_features_display.short_description = "Features Preview"
    
    def spec_layout_display(self, obj):
        """Display spec layout with validation status."""
        if not obj.spec_layout:
            return format_html('<span style="color: #999;">No spec layout</span>')
        
        valid_slugs = set(SpecKey.objects.values_list("slug", flat=True))
        items = []
        for slug in obj.spec_layout:
            if slug in valid_slugs:
                spec = SpecKey.objects.get(slug=slug)
                items.append(f'<li style="color: green;">✓ {slug} ({spec.label_tr})</li>')
            else:
                items.append(f'<li style="color: red;">✗ {slug} (invalid)</li>')
        
        return format_html(
            '<ul style="margin: 0; padding-left: 20px;">{}</ul>',
            mark_safe("".join(items)),
        )
    spec_layout_display.short_description = "Spec Layout Preview"
    
    def primary_image_preview(self, obj):
        """Show primary image thumbnail using the API endpoint."""
        primary = obj.primary_image
        if primary and primary.kind == "image":
            return format_html(
                '<img src="/api/v1/media/{}/file" '
                'style="max-width: 50px; max-height: 50px; object-fit: cover; '
                'border-radius: 4px;" alt="{}" title="{} ({}x{})"/>',
                primary.id,
                obj.title_tr,
                primary.filename,
                primary.width or "?",
                primary.height or "?",
            )
        return format_html('<span style="color: #999;">—</span>')
    primary_image_preview.short_description = "Image"
    
    def variant_count(self, obj):
        """Return count of variants (model lines)."""
        count = obj.variants.count()
        if count:
            return count
        return format_html('<span style="color: #999;">-</span>')
    variant_count.short_description = "Models"
    
    actions = ["set_first_image_as_primary", "normalize_sort_order", "apply_spec_template"]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "series", "series__category", "primary_node"
        ).prefetch_related("product_media__media", "variants")
    
    @admin.action(description="Set first image as primary for selected products")
    def set_first_image_as_primary(self, request, queryset):
        """Set the first image (by sort_order) as primary for selected products."""
        updated = 0
        for product in queryset:
            first_media = product.product_media.order_by("sort_order").first()
            if first_media and not first_media.is_primary:
                # Unset existing primary
                product.product_media.filter(is_primary=True).update(is_primary=False)
                # Set first as primary
                first_media.is_primary = True
                first_media.save()
                updated += 1
        
        self.message_user(
            request,
            f"Set primary image for {updated} product(s).",
            messages.SUCCESS,
        )
    
    @admin.action(description="Normalize sort_order (10, 20, 30...) for selected products")
    def normalize_sort_order(self, request, queryset):
        """Normalize sort_order to 10, 20, 30... for media in selected products."""
        updated = 0
        for product in queryset:
            media_items = product.product_media.order_by("sort_order")
            for idx, pm in enumerate(media_items):
                new_order = (idx + 1) * 10
                if pm.sort_order != new_order:
                    pm.sort_order = new_order
                    pm.save(update_fields=["sort_order"])
            updated += 1
        
        self.message_user(
            request,
            f"Normalized sort_order for {updated} product(s).",
            messages.SUCCESS,
        )
    
    @admin.action(description="Apply spec template to selected products")
    def apply_spec_template(self, request, queryset):
        """
        Apply a spec template to selected products.
        
        This is a two-step action:
        1. First call shows template selection form
        2. Second call applies the template
        """
        from django import forms
        from django.shortcuts import render
        from django.http import HttpResponseRedirect
        
        class TemplateSelectForm(forms.Form):
            template = forms.ModelChoiceField(
                queryset=SpecTemplate.objects.all(),
                label="Select Template",
                help_text="Choose a template to apply to selected products",
            )
            overwrite = forms.BooleanField(
                required=False,
                initial=False,
                label="Overwrite existing values",
                help_text="If checked, will overwrite existing spec_layout, features, and notes",
            )
        
        if "apply" in request.POST:
            form = TemplateSelectForm(request.POST)
            if form.is_valid():
                template = form.cleaned_data["template"]
                overwrite = form.cleaned_data["overwrite"]
                
                updated = 0
                for product in queryset:
                    fields = template.apply_to_product(product, overwrite=overwrite)
                    if fields:
                        updated += 1
                
                self.message_user(
                    request,
                    f"Applied template '{template.name}' to {updated} product(s).",
                    messages.SUCCESS,
                )
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = TemplateSelectForm()
        
        return render(
            request,
            "admin/catalog/apply_spec_template.html",
            {
                "title": "Apply Spec Template",
                "form": form,
                "products": queryset,
                "opts": self.model._meta,
                "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
            },
        )


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    """Admin for Variant model (model line)."""
    
    list_display = [
        "model_code",
        "name_tr",
        "product",
        "dimensions",
        "weight_kg",
        "list_price",
        "stock_qty",
    ]
    list_filter = ["product__series", "product__status"]
    search_fields = ["model_code", "name_tr", "name_en", "sku", "product__name"]
    ordering = ["product", "model_code"]
    autocomplete_fields = ["product"]
    
    fieldsets = (
        ("Identification", {
            "fields": ("product", "model_code", "sku"),
        }),
        ("Names", {
            "fields": ("name_tr", "name_en"),
        }),
        ("Physical", {
            "fields": ("dimensions", "weight_kg"),
        }),
        ("Pricing", {
            "fields": ("list_price", "price_override"),
        }),
        ("Specifications", {
            "fields": ("specs",),
        }),
        ("Inventory (Legacy)", {
            "fields": ("size", "color", "stock_qty"),
            "classes": ("collapse",),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "product", "product__series"
        )


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    """Admin for Media model with file upload support."""
    
    form = MediaAdminForm
    
    list_display = [
        "thumbnail_preview",
        "filename",
        "kind",
        "content_type",
        "size_display",
        "dimensions_display",
        "usage_count",
        "checksum_short",
        "created_at",
    ]
    list_filter = ["kind", "content_type"]
    search_fields = ["filename", "checksum_sha256"]
    ordering = ["-created_at"]
    readonly_fields = [
        "size_bytes",
        "checksum_sha256",
        "created_at",
        "updated_at",
        "file_preview",
    ]
    date_hierarchy = "created_at"
    
    fieldsets = (
        ("Upload", {
            "fields": ("upload", "file_preview"),
            "description": "Upload a new file or view the current one.",
        }),
        ("File Info", {
            "fields": ("kind", "filename", "content_type"),
        }),
        ("Dimensions", {
            "fields": ("width", "height"),
            "classes": ("collapse",),
        }),
        ("Metadata", {
            "fields": ("size_bytes", "checksum_sha256", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    
    actions = ["delete_unreferenced_media"]
    
    def thumbnail_preview(self, obj):
        """Show thumbnail in list view."""
        if obj.pk and obj.kind == "image":
            return format_html(
                '<img src="/api/v1/media/{}/file" '
                'style="max-width: 40px; max-height: 40px; object-fit: cover; '
                'border-radius: 3px;" alt="{}"/>',
                obj.id,
                obj.filename,
            )
        elif obj.pk and obj.kind == "pdf":
            return format_html('<span style="font-size: 20px;">📄</span>')
        elif obj.pk and obj.kind == "video":
            return format_html('<span style="font-size: 20px;">🎬</span>')
        return "—"
    thumbnail_preview.short_description = ""
    
    def file_preview(self, obj):
        """Show larger preview in detail view."""
        if obj.pk and obj.kind == "image":
            return format_html(
                '<img src="/api/v1/media/{}/file" '
                'style="max-width: 300px; max-height: 200px; object-fit: contain; '
                'border: 1px solid #ddd; border-radius: 4px;" alt="{}"/>'
                '<br><a href="/api/v1/media/{}/file" target="_blank">Open in new tab</a>',
                obj.id,
                obj.filename,
                obj.id,
            )
        elif obj.pk and obj.kind == "pdf":
            return format_html(
                '<a href="/api/v1/media/{}/file" target="_blank" '
                'style="font-size: 48px; text-decoration: none;">📄</a>'
                '<br><a href="/api/v1/media/{}/file" target="_blank">Download PDF</a>',
                obj.id,
                obj.id,
            )
        return "No file uploaded yet."
    file_preview.short_description = "Current File"
    
    def size_display(self, obj):
        """Display human-readable file size."""
        size = obj.size_bytes
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    size_display.short_description = "Size"
    
    def dimensions_display(self, obj):
        """Display image dimensions."""
        if obj.width and obj.height:
            return f"{obj.width}×{obj.height}"
        return "-"
    dimensions_display.short_description = "Dimensions"
    
    def usage_count(self, obj):
        """Show how many products use this media."""
        count = obj.media_products.count()
        if count:
            return count
        return format_html('<span style="color: #999;">0</span>')
    usage_count.short_description = "Used"
    
    def checksum_short(self, obj):
        """Display truncated checksum."""
        if obj.checksum_sha256:
            return format_html(
                '<code title="{}">{}</code>',
                obj.checksum_sha256,
                obj.checksum_sha256[:12] + "...",
            )
        return "-"
    checksum_short.short_description = "Checksum"
    
    def get_search_results(self, request, queryset, search_term):
        """Enable autocomplete search."""
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )
        return queryset, use_distinct
    
    @admin.action(description="Delete unreferenced media (not used by any product)")
    def delete_unreferenced_media(self, request, queryset):
        """Delete media that is not referenced by any ProductMedia."""
        deleted = 0
        skipped = 0
        for media in queryset:
            # Check all possible references
            has_products = media.media_products.exists()
            has_categories = media.category_covers.exists()
            has_series = media.series_covers.exists()
            has_spec_keys = media.spec_key_icons.exists()
            has_og_images = media.product_og_images.exists()
            
            if not any([has_products, has_categories, has_series, has_spec_keys, has_og_images]):
                media.delete()
                deleted += 1
            else:
                skipped += 1
        
        if deleted:
            self.message_user(
                request,
                f"Deleted {deleted} unreferenced media file(s).",
                messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"Skipped {skipped} media file(s) that are still in use.",
                messages.WARNING,
            )


@admin.register(CatalogAsset)
class CatalogAssetAdmin(admin.ModelAdmin):
    """Admin for CatalogAsset model (PDF catalog downloads)."""
    
    list_display = [
        "title_tr",
        "media",
        "is_primary",
        "order",
        "published",
        "file_size",
        "created_at",
    ]
    list_filter = ["published", "is_primary"]
    search_fields = ["title_tr", "title_en"]
    ordering = ["order", "title_tr"]
    autocomplete_fields = ["media"]
    list_editable = ["order", "published", "is_primary"]
    
    fieldsets = (
        (None, {
            "fields": ("title_tr", "title_en", "media"),
        }),
        ("Settings", {
            "fields": ("is_primary", "order", "published"),
        }),
    )
    
    def file_size(self, obj):
        """Display file size of associated media."""
        if obj.media:
            size = obj.media.size_bytes
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "-"
    file_size.short_description = "Size"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("media")


@admin.register(SpecTemplate)
class SpecTemplateAdmin(admin.ModelAdmin):
    """Admin for SpecTemplate model (fast content entry)."""
    
    list_display = [
        "name",
        "spec_layout_count",
        "features_count",
        "applies_to_series",
        "applies_to_parent_taxonomy_slug",
        "created_at",
    ]
    list_filter = ["applies_to_series"]
    search_fields = ["name", "applies_to_parent_taxonomy_slug"]
    ordering = ["name"]
    autocomplete_fields = ["applies_to_series"]
    
    fieldsets = (
        (None, {
            "fields": ("name",),
        }),
        ("Spec Layout", {
            "fields": ("spec_layout", "spec_layout_preview"),
            "description": "Enter SpecKey slugs as a JSON list, e.g., [\"goz-adedi\", \"guc-kw\"]",
        }),
        ("Default Content", {
            "fields": ("default_general_features", "default_notes"),
            "classes": ("collapse",),
        }),
        ("Scope (Optional)", {
            "fields": ("applies_to_series", "applies_to_parent_taxonomy_slug"),
            "description": "Optionally limit this template to specific series or taxonomy.",
        }),
    )
    
    readonly_fields = ["spec_layout_preview"]
    
    def spec_layout_count(self, obj):
        """Display count of spec keys in layout."""
        if obj.spec_layout:
            return len(obj.spec_layout)
        return 0
    spec_layout_count.short_description = "Specs"
    
    def features_count(self, obj):
        """Display count of default features."""
        if obj.default_general_features:
            return len(obj.default_general_features)
        return 0
    features_count.short_description = "Features"
    
    def spec_layout_preview(self, obj):
        """Display spec layout with validation status."""
        if not obj.spec_layout:
            return format_html('<span style="color: #999;">No spec layout</span>')
        
        valid_slugs = set(SpecKey.objects.values_list("slug", flat=True))
        items = []
        for slug in obj.spec_layout:
            if slug in valid_slugs:
                spec = SpecKey.objects.get(slug=slug)
                items.append(f'<li style="color: green;">✓ {slug} ({spec.label_tr})</li>')
            else:
                items.append(f'<li style="color: red;">✗ {slug} (invalid)</li>')
        
        return format_html(
            '<ul style="margin: 0; padding-left: 20px;">{}</ul>',
            mark_safe("".join(items)),
        )
    spec_layout_preview.short_description = "Spec Layout Preview"