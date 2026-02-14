# Generated migration for Variant.model_code empty string check constraint
# Migration generated on 2026-01-14 for Import System Compatibility

from django.db import migrations, models


def validate_no_empty_model_codes(apps, schema_editor):
    """
    Pre-migration validation: Ensure no variants have empty model_code.
    If found, fail with clear error message.
    """
    Variant = apps.get_model('catalog', 'Variant')

    empty_variants = Variant.objects.filter(
        models.Q(model_code='') | models.Q(model_code__isnull=True)
    )

    if empty_variants.exists():
        count = empty_variants.count()
        examples = list(empty_variants.values_list('id', 'name_tr')[:5])
        raise ValueError(
            f"Migration blocked: Found {count} variant(s) with empty model_code. "
            f"Please fix these records before running migration.\n"
            f"Examples: {examples}\n"
            f"Fix: UPDATE catalog_variant SET model_code = 'TEMP-' || id::text WHERE model_code = '' OR model_code IS NULL;"
        )

    print(f"  [VALIDATE] No empty model_code variants found. Safe to proceed.")


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0010_series_slug_global_unique'),
    ]

    operations = [
        # Step 1: Validate no empty model_code exists
        migrations.RunPython(
            code=validate_no_empty_model_codes,
            reverse_code=migrations.RunPython.noop,
        ),

        # Step 2: Add database-level CHECK constraint
        migrations.AddConstraint(
            model_name='variant',
            constraint=models.CheckConstraint(
                check=~models.Q(model_code=''),
                name='variant_model_code_not_empty',
            ),
        ),
    ]
