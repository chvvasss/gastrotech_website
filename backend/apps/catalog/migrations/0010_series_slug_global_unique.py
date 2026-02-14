# Generated migration for Series.slug global uniqueness
# Migration generated on 2026-01-14 for Import System Compatibility

from django.db import migrations, models
from apps.common.slugify_tr import slugify_tr


def deduplicate_series_slugs(apps, schema_editor):
    """
    Handle Series.slug collisions when moving from per-category to global uniqueness.

    Strategy:
    - If slug is unique across all categories → keep as-is
    - If slug appears in multiple categories → append category slug

    Example:
    - Category: "Pişirme", Series: "600-series" → "600-series" (unique)
    - Category: "Soğutma", Series: "600-series" → "600-series-sogutma" (collision)
    """
    Series = apps.get_model('catalog', 'Series')
    Category = apps.get_model('catalog', 'Category')

    from collections import defaultdict

    # Group series by slug to find collisions
    slug_groups = defaultdict(list)
    for series in Series.objects.select_related('category').all():
        slug_groups[series.slug].append(series)

    # Handle collisions
    for slug, series_list in slug_groups.items():
        if len(series_list) > 1:
            # Collision detected: rename all except first
            print(f"  [DEDUPE] Found {len(series_list)} series with slug '{slug}'")

            for i, series in enumerate(series_list):
                if i == 0:
                    # Keep first occurrence unchanged
                    print(f"    ✓ Keeping: {series.category.name} / {series.name} → '{series.slug}'")
                    continue

                # Append category slug to disambiguate
                category_slug = slugify_tr(series.category.name) if series.category else 'unknown'
                new_slug = f"{slug}-{category_slug}"[:160]  # Respect max_length

                # Handle edge case: new slug also collides
                counter = 2
                original_new_slug = new_slug
                while Series.objects.filter(slug=new_slug).exclude(pk=series.pk).exists():
                    new_slug = f"{original_new_slug}-{counter}"[:160]
                    counter += 1

                print(f"    → Renaming: {series.category.name} / {series.name}")
                print(f"      Old: '{series.slug}' → New: '{new_slug}'")

                series.slug = new_slug
                series.save(update_fields=['slug'])

    print(f"  [DEDUPE] Deduplication complete")


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0009_add_brand_model'),
    ]

    operations = [
        # Step 1: Data migration - handle collisions BEFORE changing constraint
        migrations.RunPython(
            code=deduplicate_series_slugs,
            reverse_code=migrations.RunPython.noop,
        ),

        # Step 2: Drop old per-category unique constraint
        migrations.RemoveConstraint(
            model_name='series',
            name='unique_series_slug_per_category',
        ),

        # Step 3: Make slug globally unique
        migrations.AlterField(
            model_name='series',
            name='slug',
            field=models.SlugField(
                max_length=160,
                unique=True,
                db_index=True,
                help_text="URL-friendly identifier (globally unique)",
            ),
        ),
    ]
