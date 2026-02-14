"""
Add PostgreSQL trigram extension and search indexes.

This migration enables fuzzy text search using pg_trgm extension
and adds GIN indexes on searchable fields for efficient fuzzy matching.
"""

from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


def add_trigram_extensions_and_indexes(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            
            # Product indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_title_tr_trgm ON catalog_product USING GIN (title_tr gin_trgm_ops);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_slug_trgm ON catalog_product USING GIN (slug gin_trgm_ops);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_name_trgm ON catalog_product USING GIN (name gin_trgm_ops);")
            
            # Category indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_category_name_trgm ON catalog_category USING GIN (name gin_trgm_ops);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_category_slug_trgm ON catalog_category USING GIN (slug gin_trgm_ops);")
            
            # Series indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_series_name_trgm ON catalog_series USING GIN (name gin_trgm_ops);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_series_slug_trgm ON catalog_series USING GIN (slug gin_trgm_ops);")
            
            # TaxonomyNode indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_taxonomynode_name_trgm ON catalog_taxonomynode USING GIN (name gin_trgm_ops);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_taxonomynode_slug_trgm ON catalog_taxonomynode USING GIN (slug gin_trgm_ops);")
            
            # Variant indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_variant_model_code_trgm ON catalog_variant USING GIN (model_code gin_trgm_ops);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_variant_name_tr_trgm ON catalog_variant USING GIN (name_tr gin_trgm_ops);")

def remove_trigram_extensions_and_indexes(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("DROP INDEX IF EXISTS idx_variant_name_tr_trgm;")
            cursor.execute("DROP INDEX IF EXISTS idx_variant_model_code_trgm;")
            cursor.execute("DROP INDEX IF EXISTS idx_taxonomynode_slug_trgm;")
            cursor.execute("DROP INDEX IF EXISTS idx_taxonomynode_name_trgm;")
            cursor.execute("DROP INDEX IF EXISTS idx_series_slug_trgm;")
            cursor.execute("DROP INDEX IF EXISTS idx_series_name_trgm;")
            cursor.execute("DROP INDEX IF EXISTS idx_category_slug_trgm;")
            cursor.execute("DROP INDEX IF EXISTS idx_category_name_trgm;")
            cursor.execute("DROP INDEX IF EXISTS idx_product_name_trgm;")
            cursor.execute("DROP INDEX IF EXISTS idx_product_slug_trgm;")
            cursor.execute("DROP INDEX IF EXISTS idx_product_title_tr_trgm;")
            cursor.execute("DROP EXTENSION IF EXISTS pg_trgm;")

class Migration(migrations.Migration):
    """Enable pg_trgm extension and add trigram indexes for search."""

    dependencies = [
        ("catalog", "0006_alter_media_kind"),
    ]

    operations = [
        migrations.RunPython(
            code=add_trigram_extensions_and_indexes,
            reverse_code=remove_trigram_extensions_and_indexes,
        ),
    ]
