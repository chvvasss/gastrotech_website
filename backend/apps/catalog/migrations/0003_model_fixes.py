# Migration for model fixes:
# 1. Fix Product index (created_at instead of -created_at)
# 2. Update TaxonomyNode constraint (series, parent, slug)
# 3. Update Variant SKU constraint to ignore empty string

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_catalog_group_update"),
    ]

    operations = [
        # Remove old Product index with -created_at (correct name from 0001_initial)
        migrations.RemoveIndex(
            model_name="product",
            name="catalog_pro_created_4b7c8d_idx",
        ),
        
        # Add new Product index with created_at (ascending)
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["created_at"],
                name="catalog_pro_created_asc_idx",
            ),
        ),
        
        # Remove old TaxonomyNode constraint
        migrations.RemoveConstraint(
            model_name="taxonomynode",
            name="unique_taxonomy_slug_per_series",
        ),
        
        # Add new TaxonomyNode constraint with parent included
        migrations.AddConstraint(
            model_name="taxonomynode",
            constraint=models.UniqueConstraint(
                fields=["series", "parent", "slug"],
                name="unique_taxonomy_slug_per_series_parent",
            ),
        ),
        
        # Remove old Variant SKU constraint
        migrations.RemoveConstraint(
            model_name="variant",
            name="unique_variant_sku",
        ),
        
        # Add new Variant SKU constraint that also excludes empty string
        migrations.AddConstraint(
            model_name="variant",
            constraint=models.UniqueConstraint(
                condition=models.Q(sku__isnull=False) & ~models.Q(sku=""),
                fields=["sku"],
                name="unique_variant_sku",
            ),
        ),
    ]
