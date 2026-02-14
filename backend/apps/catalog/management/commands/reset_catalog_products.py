from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Product, Variant, ProductMedia

class Command(BaseCommand):
    help = "Deletes all Products and Variants, preserving Categories, Brands, and Series. Useful for a clean slate before bulk import."

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Do not prompt the user for input of any kind.',
        )

    def handle(self, *args, **options):
        if not options['no_input']:
            self.stdout.write(self.style.WARNING("WARNING: This will delete ALL Products and Variants from the database."))
            self.stdout.write(self.style.WARNING("Categories, Brands, and Series will be preserved."))
            confirm = input("Are you sure you want to continue? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR("Operation cancelled."))
                return

        with transaction.atomic():
            # Delete Variants first (though cascade would handle it, explicit is better for reporting)
            variants_deleted = Variant.objects.all().delete()[0]
            
            # Delete Products
            products_deleted = Product.objects.all().delete()[0]

            # ProductMedia cascades from Product, but we can verify
            media_links_deleted = ProductMedia.objects.all().delete()[0] # Should be 0 if cascade works

        self.stdout.write(self.style.SUCCESS(f"Successfully deleted:"))
        self.stdout.write(f"- {variants_deleted} Variants")
        self.stdout.write(f"- {products_deleted} Products")
        self.stdout.write(self.style.SUCCESS("Database reset complete (Products cleaned)."))
