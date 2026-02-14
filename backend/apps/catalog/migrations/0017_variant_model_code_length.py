# Generated migration to increase model_code max_length from 32 to 64

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0016_category_slug_parent_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variant',
            name='model_code',
            field=models.CharField(
                db_index=True,
                help_text='Model code (e.g., GKO6010) - primary public identifier',
                max_length=64,
                unique=True,
            ),
        ),
    ]
