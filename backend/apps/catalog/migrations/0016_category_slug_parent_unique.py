# Generated migration for category slug uniqueness change
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0015_product_category_product_subcategory_and_more'),
    ]

    operations = [
        # Step 1: Remove the old unique constraint on slug
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(
                db_index=True,
                help_text='URL-friendly identifier (unique within same parent)',
                max_length=160,
            ),
        ),
        # Step 2: Add new unique constraint for (slug, parent)
        migrations.AddConstraint(
            model_name='category',
            constraint=models.UniqueConstraint(
                fields=['slug', 'parent'],
                name='uq_category_slug_parent',
            ),
        ),
        # Step 3: Add unique constraint for root categories (parent is NULL)
        migrations.AddConstraint(
            model_name='category',
            constraint=models.UniqueConstraint(
                condition=models.Q(parent__isnull=True),
                fields=['slug'],
                name='uq_category_slug_root',
            ),
        ),
    ]
