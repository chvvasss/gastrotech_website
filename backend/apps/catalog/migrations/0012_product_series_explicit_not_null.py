# Generated migration for Product.series explicit NOT NULL enforcement
# Migration generated on 2026-01-14 for Import System Compatibility

from django.db import migrations, models
import django.db.models.deletion


def validate_no_null_series(apps, schema_editor):
    """
    Pre-migration validation: Ensure no products have null series_id.
    If found, fail with clear error message.
    """
    Product = apps.get_model('catalog', 'Product')

    null_series_products = Product.objects.filter(series__isnull=True)

    if null_series_products.exists():
        count = null_series_products.count()
        examples = list(null_series_products.values_list('id', 'slug', 'name')[:5])
        raise ValueError(
            f"Migration blocked: Found {count} product(s) with NULL series_id. "
            f"Please assign series to these products before running migration.\n"
            f"Examples (id, slug, name): {examples}"
        )

    print(f"  [VALIDATE] No products with NULL series found. Safe to proceed.")


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0011_variant_model_code_check'),
    ]

    operations = [
        # Step 1: Validate no null series exists
        migrations.RunPython(
            code=validate_no_null_series,
            reverse_code=migrations.RunPython.noop,
        ),

        # Step 2: Make NOT NULL explicit (should be no-op, but documents intent)
        migrations.AlterField(
            model_name='product',
            name='series',
            field=models.ForeignKey(
                to='catalog.Series',
                on_delete=django.db.models.deletion.PROTECT,
                null=False,  # Explicit NOT NULL
                blank=False,  # Explicit form validation
                related_name='products',
                help_text='Primary series for this product group (REQUIRED)',
            ),
        ),

        # Step 3: Make Variant.product NOT NULL explicit as well
        migrations.AlterField(
            model_name='variant',
            name='product',
            field=models.ForeignKey(
                to='catalog.Product',
                on_delete=django.db.models.deletion.CASCADE,
                null=False,  # Explicit NOT NULL
                blank=False,  # Explicit form validation
                related_name='variants',
                help_text='Parent product group (REQUIRED)',
            ),
        ),
    ]
