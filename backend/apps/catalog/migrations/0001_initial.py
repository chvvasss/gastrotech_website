# Generated migration for Gastrotech catalog models

import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # Media model first (no dependencies)
        migrations.CreateModel(
            name="Media",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        help_text="Timestamp when this record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when this record was last updated",
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("image", "Image"),
                            ("pdf", "PDF"),
                            ("video", "Video"),
                        ],
                        db_index=True,
                        default="image",
                        help_text="Type of media file",
                        max_length=10,
                    ),
                ),
                (
                    "filename",
                    models.CharField(help_text="Original filename", max_length=255),
                ),
                (
                    "content_type",
                    models.CharField(
                        help_text="MIME type (e.g., image/jpeg)", max_length=100
                    ),
                ),
                (
                    "bytes",
                    models.BinaryField(help_text="Binary content stored in database"),
                ),
                (
                    "size_bytes",
                    models.PositiveIntegerField(help_text="File size in bytes"),
                ),
                (
                    "width",
                    models.PositiveIntegerField(
                        blank=True, help_text="Image width in pixels", null=True
                    ),
                ),
                (
                    "height",
                    models.PositiveIntegerField(
                        blank=True, help_text="Image height in pixels", null=True
                    ),
                ),
                (
                    "checksum_sha256",
                    models.CharField(
                        db_index=True,
                        help_text="SHA-256 hash of file content",
                        max_length=64,
                    ),
                ),
            ],
            options={
                "verbose_name": "media",
                "verbose_name_plural": "media",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="media",
            index=models.Index(fields=["kind"], name="catalog_med_kind_5e8e3b_idx"),
        ),
        migrations.AddIndex(
            model_name="media",
            index=models.Index(
                fields=["checksum_sha256"], name="catalog_med_checksu_8d9f9e_idx"
            ),
        ),
        # Category model
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        help_text="Timestamp when this record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when this record was last updated",
                    ),
                ),
                ("name", models.CharField(help_text="Category name", max_length=160)),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly identifier",
                        max_length=160,
                        unique=True,
                    ),
                ),
                (
                    "menu_label",
                    models.CharField(
                        blank=True,
                        help_text="Optional label for navigation menu",
                        max_length=100,
                    ),
                ),
                (
                    "description_short",
                    models.CharField(
                        blank=True,
                        help_text="Short description for cards/previews",
                        max_length=280,
                    ),
                ),
                (
                    "order",
                    models.PositiveIntegerField(
                        db_index=True,
                        default=0,
                        help_text="Display order (lower = first)",
                    ),
                ),
                (
                    "is_featured",
                    models.BooleanField(
                        db_index=True,
                        default=False,
                        help_text="Show in featured sections",
                    ),
                ),
                (
                    "cover_media",
                    models.ForeignKey(
                        blank=True,
                        help_text="Cover image for category",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="category_covers",
                        to="catalog.media",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        help_text="Parent category for hierarchical structure",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="children",
                        to="catalog.category",
                    ),
                ),
            ],
            options={
                "verbose_name": "category",
                "verbose_name_plural": "categories",
                "ordering": ["parent__order", "order", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="category",
            index=models.Index(fields=["order"], name="catalog_cat_order_2a1c5b_idx"),
        ),
        migrations.AddIndex(
            model_name="category",
            index=models.Index(
                fields=["is_featured"], name="catalog_cat_is_feat_3c9d7e_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="category",
            index=models.Index(
                fields=["parent", "order"], name="catalog_cat_parent__8f4e2a_idx"
            ),
        ),
        # Series model
        migrations.CreateModel(
            name="Series",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        help_text="Timestamp when this record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when this record was last updated",
                    ),
                ),
                ("name", models.CharField(help_text="Series name", max_length=160)),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly identifier", max_length=160
                    ),
                ),
                (
                    "description_short",
                    models.CharField(
                        blank=True,
                        help_text="Short description for cards/previews",
                        max_length=280,
                    ),
                ),
                (
                    "order",
                    models.PositiveIntegerField(
                        db_index=True,
                        default=0,
                        help_text="Display order within category",
                    ),
                ),
                (
                    "is_featured",
                    models.BooleanField(
                        db_index=True,
                        default=False,
                        help_text="Show in featured sections",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        help_text="Parent category",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="series",
                        to="catalog.category",
                    ),
                ),
                (
                    "cover_media",
                    models.ForeignKey(
                        blank=True,
                        help_text="Cover image for series",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="series_covers",
                        to="catalog.media",
                    ),
                ),
            ],
            options={
                "verbose_name": "series",
                "verbose_name_plural": "series",
                "ordering": ["category", "order", "name"],
            },
        ),
        migrations.AddConstraint(
            model_name="series",
            constraint=models.UniqueConstraint(
                fields=("category", "slug"), name="unique_series_slug_per_category"
            ),
        ),
        migrations.AddIndex(
            model_name="series",
            index=models.Index(fields=["order"], name="catalog_ser_order_7b3c1d_idx"),
        ),
        migrations.AddIndex(
            model_name="series",
            index=models.Index(
                fields=["is_featured"], name="catalog_ser_is_feat_9e2f4a_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="series",
            index=models.Index(
                fields=["category", "order"], name="catalog_ser_categor_5d8e3c_idx"
            ),
        ),
        # TaxonomyNode model
        migrations.CreateModel(
            name="TaxonomyNode",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        help_text="Timestamp when this record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when this record was last updated",
                    ),
                ),
                ("name", models.CharField(help_text="Node name", max_length=160)),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly identifier", max_length=160
                    ),
                ),
                (
                    "order",
                    models.PositiveIntegerField(
                        db_index=True,
                        default=0,
                        help_text="Display order within parent",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        help_text="Parent node for tree structure",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="children",
                        to="catalog.taxonomynode",
                    ),
                ),
                (
                    "series",
                    models.ForeignKey(
                        help_text="Parent series",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="taxonomy_nodes",
                        to="catalog.series",
                    ),
                ),
            ],
            options={
                "verbose_name": "taxonomy node",
                "verbose_name_plural": "taxonomy nodes",
                "ordering": ["series", "parent__order", "order", "name"],
            },
        ),
        migrations.AddConstraint(
            model_name="taxonomynode",
            constraint=models.UniqueConstraint(
                fields=("series", "slug"), name="unique_taxonomy_slug_per_series"
            ),
        ),
        migrations.AddIndex(
            model_name="taxonomynode",
            index=models.Index(fields=["order"], name="catalog_tax_order_4c7d2e_idx"),
        ),
        migrations.AddIndex(
            model_name="taxonomynode",
            index=models.Index(
                fields=["series", "order"], name="catalog_tax_series__8a5f1c_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="taxonomynode",
            index=models.Index(
                fields=["parent", "order"], name="catalog_tax_parent__2b6e9d_idx"
            ),
        ),
        # Product model
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        help_text="Timestamp when this record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when this record was last updated",
                    ),
                ),
                ("name", models.CharField(help_text="Product name", max_length=255)),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly identifier (globally unique)",
                        max_length=255,
                        unique=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("active", "Active"),
                            ("archived", "Archived"),
                        ],
                        db_index=True,
                        default="draft",
                        help_text="Publication status",
                        max_length=20,
                    ),
                ),
                (
                    "is_featured",
                    models.BooleanField(
                        db_index=True,
                        default=False,
                        help_text="Show in featured sections",
                    ),
                ),
                (
                    "short_specs",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="3-5 bullet specs for product cards",
                    ),
                ),
                (
                    "long_description",
                    models.TextField(
                        blank=True, help_text="Detailed product description"
                    ),
                ),
                (
                    "seo_title",
                    models.CharField(
                        blank=True, help_text="SEO title (max 70 chars)", max_length=70
                    ),
                ),
                (
                    "seo_description",
                    models.CharField(
                        blank=True,
                        help_text="SEO meta description (max 160 chars)",
                        max_length=160,
                    ),
                ),
                (
                    "og_media",
                    models.ForeignKey(
                        blank=True,
                        help_text="Open Graph image for social sharing",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="product_og_images",
                        to="catalog.media",
                    ),
                ),
                (
                    "primary_node",
                    models.ForeignKey(
                        blank=True,
                        help_text="Primary taxonomy node for categorization",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="primary_products",
                        to="catalog.taxonomynode",
                    ),
                ),
                (
                    "series",
                    models.ForeignKey(
                        help_text="Primary series for this product",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="products",
                        to="catalog.series",
                    ),
                ),
            ],
            options={
                "verbose_name": "product",
                "verbose_name_plural": "products",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["status"], name="catalog_pro_status_7e4a2b_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["is_featured"], name="catalog_pro_is_feat_8c3d5f_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["series", "status"], name="catalog_pro_series__9f2e6a_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["-created_at"], name="catalog_pro_created_4b7c8d_idx"
            ),
        ),
        # ProductNode through model
        migrations.CreateModel(
            name="ProductNode",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "node",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="node_products",
                        to="catalog.taxonomynode",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_nodes",
                        to="catalog.product",
                    ),
                ),
            ],
            options={
                "verbose_name": "product node",
                "verbose_name_plural": "product nodes",
            },
        ),
        migrations.AddConstraint(
            model_name="productnode",
            constraint=models.UniqueConstraint(
                fields=("product", "node"), name="unique_product_node"
            ),
        ),
        # Add M2M field to Product
        migrations.AddField(
            model_name="product",
            name="nodes",
            field=models.ManyToManyField(
                blank=True,
                help_text="All taxonomy nodes this product belongs to",
                related_name="products",
                through="catalog.ProductNode",
                to="catalog.taxonomynode",
            ),
        ),
        # Variant model
        migrations.CreateModel(
            name="Variant",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        help_text="Timestamp when this record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when this record was last updated",
                    ),
                ),
                (
                    "sku",
                    models.CharField(
                        blank=True,
                        help_text="Stock Keeping Unit",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "size",
                    models.CharField(
                        blank=True,
                        help_text="Size variant (e.g., 60cm, 80cm)",
                        max_length=50,
                    ),
                ),
                (
                    "color",
                    models.CharField(
                        blank=True, help_text="Color variant", max_length=50
                    ),
                ),
                (
                    "stock_qty",
                    models.PositiveIntegerField(
                        default=0, help_text="Current stock quantity"
                    ),
                ),
                (
                    "price_override",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Override price for this variant",
                        max_digits=12,
                        null=True,
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        help_text="Parent product",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="variants",
                        to="catalog.product",
                    ),
                ),
            ],
            options={
                "verbose_name": "variant",
                "verbose_name_plural": "variants",
                "ordering": ["product", "size", "color"],
            },
        ),
        migrations.AddConstraint(
            model_name="variant",
            constraint=models.UniqueConstraint(
                condition=models.Q(("sku__isnull", False)),
                fields=("sku",),
                name="unique_variant_sku",
            ),
        ),
        migrations.AddIndex(
            model_name="variant",
            index=models.Index(fields=["product"], name="catalog_var_product_5e9a3c_idx"),
        ),
        migrations.AddIndex(
            model_name="variant",
            index=models.Index(fields=["sku"], name="catalog_var_sku_8f4b2d_idx"),
        ),
        # ProductMedia model
        migrations.CreateModel(
            name="ProductMedia",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "alt",
                    models.CharField(
                        blank=True,
                        help_text="Alt text for accessibility",
                        max_length=255,
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        db_index=True,
                        default=0,
                        help_text="Display order (lower = first)",
                    ),
                ),
                (
                    "is_primary",
                    models.BooleanField(
                        default=False, help_text="Primary image for product cards"
                    ),
                ),
                (
                    "media",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="media_products",
                        to="catalog.media",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_media",
                        to="catalog.product",
                    ),
                ),
            ],
            options={
                "verbose_name": "product media",
                "verbose_name_plural": "product media",
                "ordering": ["sort_order"],
            },
        ),
        migrations.AddIndex(
            model_name="productmedia",
            index=models.Index(
                fields=["sort_order"], name="catalog_pro_sort_or_7c8d4e_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="productmedia",
            index=models.Index(
                fields=["product", "sort_order"], name="catalog_pro_product_9e5f2a_idx"
            ),
        ),
    ]
