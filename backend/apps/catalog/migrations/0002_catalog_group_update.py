# Migration for catalog group/model line updates

import uuid

from django.db import migrations, models
import django.db.models.deletion


def populate_title_tr(apps, schema_editor):
    """Set title_tr from name for existing products."""
    Product = apps.get_model("catalog", "Product")
    for product in Product.objects.filter(title_tr=""):
        product.title_tr = product.name
        product.save(update_fields=["title_tr"])


def populate_variant_fields(apps, schema_editor):
    """Set model_code and name_tr for existing variants."""
    Variant = apps.get_model("catalog", "Variant")
    for i, variant in enumerate(Variant.objects.filter(model_code="")):
        variant.model_code = f"LEGACY-{variant.pk}"[:32]
        variant.name_tr = variant.sku or f"Variant {i+1}"
        variant.save(update_fields=["model_code", "name_tr"])


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        # Add SpecKey model
        migrations.CreateModel(
            name="SpecKey",
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
                    "slug",
                    models.SlugField(
                        help_text="Unique identifier for this spec key",
                        max_length=64,
                        unique=True,
                    ),
                ),
                (
                    "label_tr",
                    models.CharField(help_text="Turkish label", max_length=100),
                ),
                (
                    "label_en",
                    models.CharField(
                        blank=True, help_text="English label", max_length=100
                    ),
                ),
                (
                    "unit",
                    models.CharField(
                        blank=True,
                        help_text="Unit of measurement (e.g., kW, mm, kg)",
                        max_length=20,
                    ),
                ),
                (
                    "value_type",
                    models.CharField(
                        choices=[
                            ("text", "Text"),
                            ("int", "Integer"),
                            ("decimal", "Decimal"),
                            ("bool", "Boolean"),
                        ],
                        default="text",
                        help_text="Data type for this spec value",
                        max_length=10,
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        db_index=True,
                        default=0,
                        help_text="Display order in spec tables",
                    ),
                ),
                (
                    "icon_media",
                    models.ForeignKey(
                        blank=True,
                        help_text="Optional icon for UI display",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="spec_key_icons",
                        to="catalog.media",
                    ),
                ),
            ],
            options={
                "verbose_name": "spec key",
                "verbose_name_plural": "spec keys",
                "ordering": ["sort_order", "label_tr"],
            },
        ),
        # Add new fields to Product (with defaults for existing rows)
        migrations.AddField(
            model_name="product",
            name="title_tr",
            field=models.CharField(
                default="",
                help_text="Turkish title for catalog display",
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="title_en",
            field=models.CharField(
                blank=True,
                default="",
                help_text="English title for catalog display",
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="general_features",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Bullet list of general features (Genel Özellikler)",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="notes",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Footnotes and special notes",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="spec_layout",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Ordered list of SpecKey slugs for table display",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="pdf_ref",
            field=models.CharField(
                blank=True,
                default="",
                help_text="PDF catalog reference (e.g., 'p9')",
                max_length=50,
            ),
        ),
        # Populate title_tr for existing products
        migrations.RunPython(populate_title_tr, migrations.RunPython.noop),
        # Add new fields to Variant (with defaults for existing rows)
        migrations.AddField(
            model_name="variant",
            name="model_code",
            field=models.CharField(
                default="",
                help_text="Model code (e.g., GKO6010) - primary public identifier",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="variant",
            name="name_tr",
            field=models.CharField(
                default="",
                help_text="Turkish model name",
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name="variant",
            name="name_en",
            field=models.CharField(
                blank=True,
                default="",
                help_text="English model name",
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name="variant",
            name="dimensions",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Dimensions (e.g., '400x630x280')",
                max_length=64,
            ),
        ),
        migrations.AddField(
            model_name="variant",
            name="weight_kg",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                help_text="Weight in kilograms",
                max_digits=10,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="variant",
            name="list_price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="List price",
                max_digits=12,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="variant",
            name="specs",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Flexible specifications keyed by SpecKey slug",
            ),
        ),
        # Populate model_code and name_tr for existing variants
        migrations.RunPython(populate_variant_fields, migrations.RunPython.noop),
        # Now add the unique constraint and index for model_code
        migrations.AlterField(
            model_name="variant",
            name="model_code",
            field=models.CharField(
                db_index=True,
                help_text="Model code (e.g., GKO6010) - primary public identifier",
                max_length=32,
                unique=True,
            ),
        ),
    ]
