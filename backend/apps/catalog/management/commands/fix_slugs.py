
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Category, Series, Brand
from apps.common.slugify_tr import slugify_tr

class Command(BaseCommand):
    help = 'Fixes inconsistent slugs for Categories, Series, and Brands'

    def handle(self, *args, **options):
        self.stdout.write("Starting slug fix process...")
        
        with transaction.atomic():
            self.fix_models(Category, "Category")
            self.fix_models(Series, "Series")
            self.fix_models(Brand, "Brand")
            
        self.stdout.write(self.style.SUCCESS("Slug fix process completed!"))

    def fix_models(self, model_class, model_name):
        self.stdout.write(f"\nProcessing {model_name}...")
        count = 0
        updated = 0
        
        for obj in model_class.objects.all():
            count += 1
            expected_slug = slugify_tr(obj.name)
            
            # Skip if slug is already correct
            if obj.slug == expected_slug:
                continue
                
            # Check for collisions
            if model_class.objects.filter(slug=expected_slug).exclude(id=obj.id).exists():
                self.stdout.write(self.style.WARNING(
                    f"  SKIP: Cannot update {obj.name} (Current: {obj.slug}) -> Expected: {expected_slug} (ALREADY EXISTS)"
                ))
                continue
                
            old_slug = obj.slug
            obj.slug = expected_slug
            obj.save()
            updated += 1
            self.stdout.write(f"  FIXED: {obj.name} | {old_slug} -> {obj.slug}")

        self.stdout.write(f"Done {model_name}: {updated}/{count} updated.")
