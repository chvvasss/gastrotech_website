"""
Catalog models for Gastrotech B2B product catalog.

This module implements the complete catalog domain:
- Category: Top-level product categories
- Series: Product series/lines within categories (600/700/900/etc.)
- TaxonomyNode: Hierarchical classification within series
- Product: Catalog group (contains multiple model lines)
- Variant: Individual model line within a product group
- SpecKey: Specification keys for consistent labeling
- Media: Binary media storage in PostgreSQL
- ProductMedia: Product-media associations
"""

import hashlib
import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimeStampedUUIDModel
from apps.common.slugify_tr import slugify_tr


class Media(TimeStampedUUIDModel):
    """
    Media storage model - stores binary data directly in PostgreSQL.
    
    Supports images, PDFs, and videos with metadata.
    """
    
    class Kind(models.TextChoices):
        IMAGE = "image", "Image"
        PDF = "pdf", "PDF"
        VIDEO = "video", "Video"
        FILE = "file", "File"  # For CSV, Excel, and other data files
    
    kind = models.CharField(
        max_length=10,
        choices=Kind.choices,
        default=Kind.IMAGE,
        db_index=True,
        help_text="Type of media file",
    )
    filename = models.CharField(
        max_length=255,
        help_text="Original filename",
    )
    content_type = models.CharField(
        max_length=100,
        help_text="MIME type (e.g., image/jpeg)",
    )
    bytes = models.BinaryField(
        help_text="Binary content stored in database",
    )
    size_bytes = models.PositiveIntegerField(
        help_text="File size in bytes",
    )
    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Image width in pixels",
    )
    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Image height in pixels",
    )
    checksum_sha256 = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 hash of file content",
    )
    
    class Meta:
        verbose_name = "media"
        verbose_name_plural = "media"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["kind"]),
            models.Index(fields=["checksum_sha256"]),
        ]
    
    def __str__(self):
        return f"{self.filename} ({self.kind})"
    
    def save(self, *args, **kwargs):
        """Compute checksum and size before saving."""
        if self.bytes:
            self.size_bytes = len(self.bytes)
            self.checksum_sha256 = self.compute_sha256(self.bytes)
        super().save(*args, **kwargs)
    
    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """Compute SHA-256 hash of binary data."""
        return hashlib.sha256(data).hexdigest()


class SpecKey(TimeStampedUUIDModel):
    """
    Specification key for consistent labeling across product groups.
    
    Enables consistent labels & UI icons in spec tables.
    """
    
    class ValueType(models.TextChoices):
        TEXT = "text", "Text"
        INT = "int", "Integer"
        DECIMAL = "decimal", "Decimal"
        BOOL = "bool", "Boolean"
    
    slug = models.SlugField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Unique identifier for this spec key",
    )
    label_tr = models.CharField(
        max_length=100,
        help_text="Turkish label",
    )
    label_en = models.CharField(
        max_length=100,
        blank=True,
        help_text="English label",
    )
    unit = models.CharField(
        max_length=20,
        blank=True,
        help_text="Unit of measurement (e.g., kW, mm, kg)",
    )
    value_type = models.CharField(
        max_length=10,
        choices=ValueType.choices,
        default=ValueType.TEXT,
        help_text="Data type for this spec value",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Display order in spec tables",
    )
    icon_media = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="spec_key_icons",
        help_text="Optional icon for UI display",
    )
    
    class Meta:
        verbose_name = "spec key"
        verbose_name_plural = "spec keys"
        ordering = ["sort_order", "label_tr"]
    
    def __str__(self):
        unit_str = f" ({self.unit})" if self.unit else ""
        return f"{self.label_tr}{unit_str}"


class Category(TimeStampedUUIDModel):
    """
    Top-level product category.
    
    Examples: Pişirme Üniteleri, Fırınlar, Soğutma Üniteleri
    """
    
    name = models.CharField(
        max_length=160,
        help_text="Category name",
    )
    slug = models.SlugField(
        max_length=160,
        db_index=True,
        help_text="URL-friendly identifier (unique within same parent)",
    )
    menu_label = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional label for navigation menu",
    )
    description_short = models.CharField(
        max_length=280,
        blank=True,
        help_text="Short description for cards/previews",
    )
    order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Display order (lower = first)",
    )
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Show in featured sections",
    )
    cover_media = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="category_covers",
        help_text="Cover image for category",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        help_text="Parent category for hierarchical structure",
    )

    class SeriesMode(models.TextChoices):
        DISABLED = "disabled", "Disabled"
        OPTIONAL = "optional", "Optional"
        REQUIRED = "required", "Required"

    series_mode = models.CharField(
        max_length=10,
        choices=SeriesMode.choices,
        default=SeriesMode.DISABLED,
        db_index=True,
        help_text="Controls series requirement for products: disabled (no series), optional (default), required",
    )

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        ordering = ["parent__order", "order", "name"]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["is_featured"]),
            models.Index(fields=["parent", "order"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "parent"],
                name="uq_category_slug_parent",
            ),
            # Handle NULL parent case separately (root categories must have unique slugs)
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(parent__isnull=True),
                name="uq_category_slug_root",
            ),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_tr(self.name)
        super().save(*args, **kwargs)

    def clean(self):
        """Validate category hierarchy to prevent circular references and enforce depth limit."""
        super().clean()

        # Prevent self-parent
        if self.parent and self.parent == self:
            raise ValidationError({"parent": "Category cannot be its own parent"})

        # Check for circular references
        if self.parent:
            visited = {self.id} if self.id else set()
            current = self.parent
            while current:
                if current.id in visited:
                    raise ValidationError({"parent": "Circular category reference detected"})
                visited.add(current.id)
                current = current.parent

            # Enforce max depth of 3 (root → subcategory → sub-subcategory)
            depth = 0
            current = self.parent
            while current:
                depth += 1
                if depth > 2:
                    raise ValidationError({
                        "parent": "Maximum category depth is 3 levels (root → sub → sub-sub). "
                                 "Cannot nest deeper."
                    })
                current = current.parent

    @property
    def is_root(self) -> bool:
        """Check if this is a root category (no parent)."""
        return self.parent_id is None

    @property
    def is_leaf(self) -> bool:
        """Check if this is a leaf category (no children)."""
        # Use hasattr to check if children are prefetched
        if hasattr(self, '_prefetched_children'):
            return len(self._prefetched_children) == 0
        return not self.children.exists()

    @property
    def depth(self) -> int:
        """Return depth in tree (0 = root, 1 = subcategory, etc.)."""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth

    @property
    def breadcrumbs(self) -> list:
        """Return list of ancestor categories including self (root → ... → self)."""
        crumbs = [self]
        current = self.parent
        while current:
            crumbs.insert(0, current)
            current = current.parent
        return crumbs

    @property
    def breadcrumb_path(self) -> str:
        """Return breadcrumb path as string (e.g., 'Fırınlar > Pizza Fırını')."""
        return " > ".join(c.name for c in self.breadcrumbs)

    def get_descendants(self, include_self=False):
        """Get all descendant categories recursively."""
        descendants = [self] if include_self else []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants(include_self=False))
        return descendants

    def get_leaf_categories(self):
        """Get all leaf (childless) categories under this category."""
        if self.is_leaf:
            return [self]
        leaves = []
        for child in self.children.all():
            leaves.extend(child.get_leaf_categories())
        return leaves


class BrandCategory(models.Model):
    """
    Through model for Brand-Category M2M relationship.

    Tracks which brands operate in which categories with additional metadata.
    This allows:
    - A brand like "Bosch" to be in multiple categories (Ovens, Dishwashers, etc.)
    - Category-specific brand ordering
    - Automatic relationship creation during import
    """

    brand = models.ForeignKey(
        "Brand",
        on_delete=models.CASCADE,
        related_name="brand_categories",
        help_text="Brand in this relationship",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="category_brands",
        help_text="Category in this relationship",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this brand-category combination is active",
    )
    order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Display order of brand within this category",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "brand category"
        verbose_name_plural = "brand categories"
        ordering = ["category", "order", "brand__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["brand", "category"],
                name="unique_brand_category",
            ),
        ]
        indexes = [
            models.Index(fields=["brand", "category"]),
            models.Index(fields=["category", "is_active", "order"]),
        ]

    def __str__(self):
        return f"{self.brand.name} in {self.category.name}"


class CategoryLogoGroup(models.Model):
    """
    Maps a brand logo to a group of series within a category.
    
    This enables the "logo grid" navigation pattern where:
    1. User enters a category (e.g., "Hamur İşleme Makineleri")
    2. Multiple brand logos are displayed (e.g., CGF, vitella)
    3. Clicking a logo shows the series grouped under that brand
    
    Example:
        CategoryLogoGroup(
            category="Hamur İşleme Makineleri",
            brand="vitella",
            order=1,
            series=["Hamur Bölme ve Yuvarlama Makineleri", ...]
        )
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="logo_groups",
        help_text="Category this logo group belongs to",
    )
    brand = models.ForeignKey(
        "Brand",
        on_delete=models.CASCADE,
        related_name="category_logo_groups",
        help_text="Brand whose logo is displayed",
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional title displayed when logo is clicked (defaults to brand name)",
    )
    order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Display order of logo within category (lower = first)",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this logo group is active",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "category logo group"
        verbose_name_plural = "category logo groups"
        ordering = ["category", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "brand"],
                name="unique_category_brand_logo_group",
            ),
        ]
        indexes = [
            models.Index(fields=["category", "order"]),
            models.Index(fields=["category", "is_active"]),
        ]
    
    def __str__(self):
        return f"{self.category.name} - {self.brand.name} logo group"


class LogoGroupSeries(models.Model):
    """
    Through model for CategoryLogoGroup-Series M2M relationship.
    
    Allows ordering of series within a logo group.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    logo_group = models.ForeignKey(
        CategoryLogoGroup,
        on_delete=models.CASCADE,
        related_name="logo_group_series",
        help_text="Logo group this series belongs to",
    )
    series = models.ForeignKey(
        "Series",
        on_delete=models.CASCADE,
        related_name="logo_group_memberships",
        help_text="Series in this logo group",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within the logo group",
    )
    is_heading = models.BooleanField(
        default=False,
        help_text="If true, this series is displayed as a heading (bold/prominent)",
    )
    
    class Meta:
        verbose_name = "logo group series"
        verbose_name_plural = "logo group series"
        ordering = ["logo_group", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["logo_group", "series"],
                name="unique_logo_group_series",
            ),
        ]
    
    def __str__(self):
        return f"{self.logo_group.brand.name} - {self.series.name}"


class Series(TimeStampedUUIDModel):
    """
    Product series within a category.
    
    Examples: 600 Series, 700 Series, 900 Series, Drop-in
    """
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="series",
        help_text="Parent category",
    )
    name = models.CharField(
        max_length=160,
        help_text="Series name",
    )
    slug = models.SlugField(
        max_length=160,
        db_index=True,
        help_text="URL-friendly identifier",
    )
    description_short = models.CharField(
        max_length=280,
        blank=True,
        help_text="Short description for cards/previews",
    )
    order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Display order within category",
    )
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Show in featured sections",
    )
    cover_media = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="series_covers",
        help_text="Cover image for series",
    )
    
    class Meta:
        verbose_name = "series"
        verbose_name_plural = "series"
        ordering = ["category", "order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "slug"],
                name="unique_series_slug_per_category",
            ),
        ]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["is_featured"]),
            models.Index(fields=["category", "order"]),
        ]
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_tr(self.name)
        super().save(*args, **kwargs)

    @property
    def product_count(self) -> int:
        """Return count of active products in this series."""
        # Use cached annotation if available (from queryset)
        if hasattr(self, '_product_count'):
            return self._product_count
        return self.products.filter(status='active').count()

    @property
    def is_visible(self) -> bool:
        """
        Series visibility rule: visible only if it contains 2+ products.

        Business rule:
        - Series with 0 products = orphan, not visible
        - Series with 1 product = single-product, not visible in navigation
          (the product appears directly under category)
        - Series with 2+ products = visible as a grouping

        Note: This does NOT delete the series - it just hides it from navigation.
        The series record is preserved for imports and historical data.
        """
        return self.product_count >= 2

    @classmethod
    def visible_series(cls):
        """
        Return queryset of series that should be visible in navigation.

        Usage:
            Series.visible_series().filter(category=some_category)
        """
        from django.db.models import Count, Q
        return cls.objects.annotate(
            _product_count=Count('products', filter=Q(products__status='active'))
        ).filter(_product_count__gte=2)

    @classmethod
    def annotate_visibility(cls, queryset):
        """
        Annotate a Series queryset with visibility information.

        Adds:
        - _product_count: Count of active products
        - _is_visible: Boolean indicating if series should be shown in nav

        Usage:
            qs = Series.annotate_visibility(Series.objects.filter(category=cat))
        """
        from django.db.models import Count, Q, Case, When, Value, BooleanField
        return queryset.annotate(
            _product_count=Count('products', filter=Q(products__status='active')),
        ).annotate(
            _is_visible=Case(
                When(_product_count__gte=2, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )


class TaxonomyNode(TimeStampedUUIDModel):
    """
    Hierarchical taxonomy node within a series.
    
    Examples: Ocaklar > Gazlı, Ocaklar > Elektrikli
    """
    
    series = models.ForeignKey(
        Series,
        on_delete=models.CASCADE,
        related_name="taxonomy_nodes",
        help_text="Parent series",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        help_text="Parent node for tree structure",
    )
    name = models.CharField(
        max_length=160,
        help_text="Node name",
    )
    slug = models.SlugField(
        max_length=160,
        db_index=True,
        help_text="URL-friendly identifier",
    )
    order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Display order within parent",
    )
    
    class Meta:
        verbose_name = "taxonomy node"
        verbose_name_plural = "taxonomy nodes"
        ordering = ["series", "parent__order", "order", "name"]
        constraints = [
            # FIX: Changed from unique(series, slug) to unique(series, parent, slug)
            models.UniqueConstraint(
                fields=["series", "parent", "slug"],
                name="unique_taxonomy_slug_per_series_parent",
            ),
        ]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["series", "order"]),
            models.Index(fields=["parent", "order"]),
        ]
    
    def __str__(self):
        return f"{self.series.name} - {self.full_path}"
    
    @property
    def full_path(self) -> str:
        """Generate breadcrumb path for this node."""
        path_parts = [self.name]
        current = self.parent
        while current:
            path_parts.insert(0, current.name)
            current = current.parent
        return " > ".join(path_parts)
    
    @property
    def breadcrumbs(self) -> list:
        """Return list of ancestor nodes including self."""
        crumbs = [self]
        current = self.parent
        while current:
            crumbs.insert(0, current)
            current = current.parent
        return crumbs
    
    @property
    def depth(self) -> int:
        """Return depth of node in tree (0 = root)."""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_tr(self.name)
        super().save(*args, **kwargs)


class Brand(TimeStampedUUIDModel):
    """
    Product brand for multi-brand catalog support.

    Examples: Gastrotech, Partner Brand A, Partner Brand B

    Brands can be associated with multiple categories via M2M relationship.
    This allows flexible brand-category combinations (e.g., Bosch in both
    Ovens and Dishwashers categories).
    """

    name = models.CharField(
        max_length=100,
        help_text="Brand name",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="URL-friendly identifier",
    )
    logo_media = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="brand_logos",
        help_text="Brand logo image",
    )
    description = models.TextField(
        blank=True,
        help_text="Brand description",
    )
    website_url = models.URLField(
        blank=True,
        help_text="Brand website URL",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether brand is active",
    )
    order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Display order (lower = first)",
    )
    categories = models.ManyToManyField(
        Category,
        through="BrandCategory",
        related_name="brands",
        blank=True,
        help_text="Categories this brand operates in",
    )

    class Meta:
        verbose_name = "brand"
        verbose_name_plural = "brands"
        ordering = ["order", "name"]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_tr(self.name)
        super().save(*args, **kwargs)


class Product(TimeStampedUUIDModel):
    """
    Product group (catalog page) for Gastrotech catalog.
    
    Represents a "group page" in the PDF catalog containing multiple model lines.
    Each Product has Variants representing individual model lines.
    """
    
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"
    
    series = models.ForeignKey(
        Series,
        on_delete=models.PROTECT,
        related_name="products",
        help_text="Primary series for this product group",
    )
    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        help_text="Primary category (denormalized from Series)",
    )
    primary_node = models.ForeignKey(
        TaxonomyNode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_products",
        help_text="Primary taxonomy node for categorization",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        help_text="Product brand",
    )
    
    # Basic identification
    name = models.CharField(
        max_length=255,
        help_text="Internal product name",
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="URL-friendly identifier (globally unique)",
    )
    
    # Localized titles (for PDF catalog display)
    title_tr = models.CharField(
        max_length=200,
        help_text="Turkish title for catalog display",
    )
    title_en = models.CharField(
        max_length=200,
        blank=True,
        help_text="English title for catalog display",
    )
    
    # Status and visibility
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        help_text="Publication status",
    )
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Show in featured sections",
    )
    
    # Catalog group content
    general_features = models.JSONField(
        default=list,
        blank=True,
        help_text="Bullet list of general features (Genel Özellikler)",
    )
    notes = models.JSONField(
        default=list,
        blank=True,
        help_text="Footnotes and special notes",
    )
    spec_layout = models.JSONField(
        default=list,
        blank=True,
        help_text="Ordered list of SpecKey slugs for table display",
    )
    pdf_ref = models.CharField(
        max_length=50,
        blank=True,
        help_text="PDF catalog reference (e.g., 'p9')",
    )
    
    # Legacy/SEO fields
    short_specs = models.JSONField(
        default=list,
        blank=True,
        help_text="3-5 bullet specs for product cards (legacy)",
    )
    long_description = models.TextField(
        blank=True,
        help_text="Detailed product description",
    )
    seo_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="SEO title",
    )
    seo_description = models.CharField(
        max_length=255,
        blank=True,
        help_text="SEO meta description",
    )
    og_media = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_og_images",
        help_text="Open Graph image for social sharing",
    )
    nodes = models.ManyToManyField(
        TaxonomyNode,
        through="ProductNode",
        related_name="products",
        blank=True,
        help_text="All taxonomy nodes this product belongs to",
    )
    
    class Meta:
        verbose_name = "product"
        verbose_name_plural = "products"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["is_featured"]),
            models.Index(fields=["series", "status"]),
            # FIX: Changed from ["-created_at"] to ["created_at"]
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        return self.title_tr or self.name

    def clean(self):
        """Validate spec_layout contains valid SpecKey slugs."""
        super().clean()
        if self.spec_layout:
            # Efficient validation: only query for the slugs we're checking
            valid_count = SpecKey.objects.filter(slug__in=self.spec_layout).count()
            if valid_count != len(self.spec_layout):
                # Only fetch all slugs if validation fails (rare case)
                valid_slugs = set(SpecKey.objects.filter(slug__in=self.spec_layout).values_list("slug", flat=True))
                invalid_slugs = [s for s in self.spec_layout if s not in valid_slugs]
                raise ValidationError({
                    "spec_layout": f"Invalid SpecKey slugs: {', '.join(invalid_slugs)}"
                })

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_tr(self.name)
        if not self.title_tr:
            self.title_tr = self.name
        super().save(*args, **kwargs)
    
    @property
    def primary_image(self):
        """Return the primary product image if exists."""
        primary = self.product_media.filter(is_primary=True).first()
        if primary:
            return primary.media
        # Fallback to first image
        first = self.product_media.order_by("sort_order").first()
        return first.media if first else None
    
    def get_spec_keys(self):
        """Return ordered SpecKey objects based on spec_layout."""
        if not self.spec_layout:
            return []
        return list(
            SpecKey.objects.filter(slug__in=self.spec_layout)
            .order_by(
                models.Case(
                    # FIX: Use models.Value(pos) for proper ordering
                    *[
                        models.When(slug=slug, then=models.Value(pos))
                        for pos, slug in enumerate(self.spec_layout)
                    ],
                    output_field=models.IntegerField(),
                )
            )
        )


class ProductNode(models.Model):
    """
    Through model for Product-TaxonomyNode M2M relationship.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="product_nodes",
    )
    node = models.ForeignKey(
        TaxonomyNode,
        on_delete=models.CASCADE,
        related_name="node_products",
    )
    
    class Meta:
        verbose_name = "product node"
        verbose_name_plural = "product nodes"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "node"],
                name="unique_product_node",
            ),
        ]
    
    def __str__(self):
        return f"{self.product.name} -> {self.node.name}"


class Variant(TimeStampedUUIDModel):
    """
    Product variant / model line within a product group.
    
    Represents an individual model line (e.g., GKO6010) in a catalog page,
    with specific dimensions, pricing, and specifications.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        help_text="Parent product group",
    )
    
    # Primary identifier
    model_code = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Model code (e.g., GKO6010) - primary public identifier",
    )
    
    # Localized names
    name_tr = models.CharField(
        max_length=200,
        help_text="Turkish model name",
    )
    name_en = models.CharField(
        max_length=200,
        blank=True,
        help_text="English model name",
    )
    
    # Legacy SKU (optional, for internal use)
    sku = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Stock Keeping Unit (legacy)",
    )
    
    # Physical attributes
    dimensions = models.CharField(
        max_length=64,
        blank=True,
        help_text="Dimensions (e.g., '400x630x280')",
    )
    weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Weight in kilograms",
    )
    
    # Pricing
    list_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="List price",
    )
    price_override = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Override price for this variant",
    )
    
    # Flexible specs (JSON for extra columns per group)
    specs = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible specifications keyed by SpecKey slug",
    )
    
    # Inventory (legacy, payment-ready)
    size = models.CharField(
        max_length=50,
        blank=True,
        help_text="Size variant (legacy)",
    )
    color = models.CharField(
        max_length=50,
        blank=True,
        help_text="Color variant (legacy)",
    )
    stock_qty = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=None,
        help_text="Current stock quantity. NULL = unlimited stock, 0 = out of stock",
    )
    
    class Meta:
        verbose_name = "variant"
        verbose_name_plural = "variants"
        ordering = ["product", "model_code"]
        constraints = [
            # FIX: Improved constraint to ignore both null and empty string
            models.UniqueConstraint(
                fields=["sku"],
                condition=models.Q(sku__isnull=False) & ~models.Q(sku=""),
                name="unique_variant_sku",
            ),
        ]
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["model_code"]),
            models.Index(fields=["sku"]),
        ]
    
    def __str__(self):
        return f"{self.model_code} - {self.name_tr}"

    def clean(self):
        """Validate model_code is not empty."""
        super().clean()
        if self.model_code is not None and not self.model_code.strip():
            from django.core.exceptions import ValidationError
            raise ValidationError({
                "model_code": "Model code cannot be empty or whitespace only."
            })

    def get_spec_value(self, spec_key_slug: str):
        """Get specification value by key slug."""
        return self.specs.get(spec_key_slug)
    
    def get_display_price(self):
        """Return the display price (override or list price)."""
        return self.price_override or self.list_price


class ProductMedia(models.Model):
    """
    Association between Product and Media with ordering and primary flag.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="product_media",
    )
    media = models.ForeignKey(
        Media,
        on_delete=models.CASCADE,
        related_name="media_products",
    )
    variant = models.ForeignKey(
        "Variant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="variant_media",
        help_text="Specific variant this image represents (optional)",
    )
    alt = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alt text for accessibility",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Display order (lower = first)",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary image for product cards",
    )
    
    class Meta:
        verbose_name = "product media"
        verbose_name_plural = "product media"
        ordering = ["sort_order"]
        indexes = [
            models.Index(fields=["sort_order"]),
            models.Index(fields=["product", "sort_order"]),
        ]
    
    def __str__(self):
        primary_indicator = " [PRIMARY]" if self.is_primary else ""
        return f"{self.product.name} - {self.media.filename}{primary_indicator}"
    
    def clean(self):
        """Validate that only one primary image exists per product."""
        if self.is_primary:
            existing_primary = ProductMedia.objects.filter(
                product=self.product,
                is_primary=True,
            ).exclude(pk=self.pk)
            if existing_primary.exists():
                raise ValidationError(
                    "A product can only have one primary image. "
                    "Please unset the current primary image first."
                )
    
    def save(self, *args, **kwargs):
        # If setting as primary, unset other primaries
        # Use select_for_update to prevent race conditions
        from django.db import transaction

        if self.is_primary:
            with transaction.atomic():
                # Lock and update other primaries to prevent race conditions
                ProductMedia.objects.select_for_update().filter(
                    product=self.product,
                    is_primary=True,
                ).exclude(pk=self.pk).update(is_primary=False)
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


class CatalogAsset(TimeStampedUUIDModel):
    """
    Downloadable catalog assets (PDF catalogs, brochures).
    
    For "Katalog İndir" functionality.
    """
    
    title_tr = models.CharField(
        max_length=200,
        help_text="Turkish title",
    )
    title_en = models.CharField(
        max_length=200,
        blank=True,
        help_text="English title",
    )
    media = models.ForeignKey(
        Media,
        on_delete=models.PROTECT,
        related_name="catalog_assets",
        limit_choices_to={"kind": "pdf"},
        help_text="PDF file (must be kind=pdf)",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary/main catalog",
    )
    order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Display order",
    )
    published = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Visible on public site",
    )
    
    class Meta:
        verbose_name = "catalog asset"
        verbose_name_plural = "catalog assets"
        ordering = ["order", "title_tr"]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["published"]),
        ]
    
    def __str__(self):
        primary_indicator = " [PRIMARY]" if self.is_primary else ""
        return f"{self.title_tr}{primary_indicator}"
    
    def save(self, *args, **kwargs):
        # Enforce single primary
        if self.is_primary:
            CatalogAsset.objects.filter(is_primary=True).exclude(pk=self.pk).update(
                is_primary=False
            )
        super().save(*args, **kwargs)


class CategoryCatalog(TimeStampedUUIDModel):
    """
    PDF catalog files linked to categories.

    When catalog_mode is ON, these replace product listings
    inside category pages on the public site.
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="category_catalogs",
        help_text="Category this catalog belongs to",
    )
    title_tr = models.CharField(
        max_length=200,
        help_text="Turkish title",
    )
    title_en = models.CharField(
        max_length=200,
        blank=True,
        help_text="English title",
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description",
    )
    media = models.ForeignKey(
        Media,
        on_delete=models.PROTECT,
        related_name="category_catalog_files",
        limit_choices_to={"kind": "pdf"},
        help_text="PDF file (must be kind=pdf)",
    )
    order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Display order",
    )
    published = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Visible on public site",
    )

    class Meta:
        verbose_name = "category catalog"
        verbose_name_plural = "category catalogs"
        ordering = ["order", "title_tr"]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["published"]),
        ]

    def __str__(self):
        return f"{self.category.name} - {self.title_tr}"


class SpecTemplate(TimeStampedUUIDModel):
    """
    Template for fast content entry.
    
    Allows admins to quickly apply consistent spec_layout and features
    to multiple products.
    """
    
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Template name (e.g., 'Gazlı Ocak Şablonu')",
    )
    spec_layout = models.JSONField(
        default=list,
        blank=True,
        help_text="Ordered list of SpecKey slugs for table display",
    )
    default_general_features = models.JSONField(
        default=list,
        blank=True,
        help_text="Default general features to apply (if product has none)",
    )
    default_notes = models.JSONField(
        default=list,
        blank=True,
        help_text="Default notes to apply (if product has none)",
    )
    applies_to_series = models.ForeignKey(
        Series,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="spec_templates",
        help_text="Optional: limit this template to a specific series",
    )
    applies_to_parent_taxonomy_slug = models.CharField(
        max_length=160,
        blank=True,
        help_text="Optional: limit to products under this taxonomy node slug",
    )
    
    class Meta:
        verbose_name = "spec template"
        verbose_name_plural = "spec templates"
        ordering = ["name"]
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate spec_layout contains valid SpecKey slugs."""
        super().clean()
        if self.spec_layout:
            valid_slugs = set(SpecKey.objects.values_list("slug", flat=True))
            invalid_slugs = [s for s in self.spec_layout if s not in valid_slugs]
            if invalid_slugs:
                raise ValidationError({
                    "spec_layout": f"Invalid SpecKey slugs: {', '.join(invalid_slugs)}"
                })
    
    def apply_to_product(self, product, overwrite=False):
        """
        Apply this template to a product.
        
        Args:
            product: Product instance to update
            overwrite: If True, overwrite existing values. If False, only set if empty.
        
        Returns:
            List of fields that were updated
        """
        updated_fields = []
        
        # Apply spec_layout
        if self.spec_layout and (overwrite or not product.spec_layout):
            product.spec_layout = self.spec_layout
            updated_fields.append("spec_layout")
        
        # Apply general_features
        if self.default_general_features and (overwrite or not product.general_features):
            product.general_features = self.default_general_features
            updated_fields.append("general_features")
        
        # Apply notes
        if self.default_notes and (overwrite or not product.notes):
            product.notes = self.default_notes
            updated_fields.append("notes")
        
        if updated_fields:
            product.save(update_fields=updated_fields + ["updated_at"])
        
        return updated_fields
