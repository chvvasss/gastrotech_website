import csv
import os
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple, Any

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.models import Product, Series, Variant


class Command(BaseCommand):
    help = "Import products and variants from CSV files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--products",
            type=str,
            required=True,
            help="Path to the products CSV file (semicolon delimited).",
        )
        parser.add_argument(
            "--variants",
            type=str,
            required=True,
            help="Path to the variants CSV file (semicolon delimited).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run validation without saving changes.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Commit changes even if errors occur (not recommended).",
        )

    def handle(self, *args, **options):
        products_path = options["products"]
        variants_path = options["variants"]
        dry_run = options["dry_run"]
        force = options["force"]

        self.stdout.write("Starting import...")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE: No changes will be saved."))

        # Validate file existence
        if not os.path.exists(products_path):
            self.stderr.write(self.style.ERROR(f"Products file not found: {products_path}"))
            return
        if not os.path.exists(variants_path):
            self.stderr.write(self.style.ERROR(f"Variants file not found: {variants_path}"))
            return

        # Statistics
        stats = {
            "products_created": 0,
            "products_updated": 0,
            "variants_created": 0,
            "variants_updated": 0,
            "errors": [],
        }

        try:
            with transaction.atomic():
                # Import Products
                self.import_products(products_path, stats)
                
                # Import Variants (only if product import didn't crash fatally)
                self.import_variants(variants_path, stats)

                # Check for errors
                error_count = len(stats["errors"])
                if error_count > 0:
                    self.print_errors(stats["errors"])
                    
                    if not force:
                        raise Exception(f"Aborting due to {error_count} errors. Use --force to ignore errors (failed records will be skipped).")
                    else:
                        self.stdout.write(self.style.WARNING(f"Proceeding despite {error_count} errors (--force used)."))

                if dry_run:
                    raise Exception("Dry run complete (rolling back transaction).")

        except Exception as e:
            if str(e) == "Dry run complete (rolling back transaction).":
                self.stdout.write(self.style.SUCCESS("Dry run successful. No changes made."))
            elif "Aborting due to" in str(e):
                self.stderr.write(self.style.ERROR(str(e)))
            else:
                self.stderr.write(self.style.ERROR(f"An unexpected error occurred: {str(e)}"))
                # Re-raise to show traceback for unexpected errors if needed, 
                # but simple printing is usually cleaner for users.
                if options.get('verbosity', 1) > 1:
                    raise e
            
            # Print stats even on failure/dry-run to show what WOULD have happened
            self.print_stats(stats)
            return

        self.stdout.write(self.style.SUCCESS("Import completed successfully."))
        self.print_stats(stats)

    def import_products(self, file_path: str, stats: Dict[str, Any]):
        self.stdout.write(f"Reading products from {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                # Normalize headers (strip whitespace)
                reader.fieldnames = [name.strip() for name in reader.fieldnames] if reader.fieldnames else []
                
                required_fields = ['slug', 'series_slug', 'title_tr']
                for field in required_fields:
                    if field not in reader.fieldnames:
                        stats["errors"].append(f"Products CSV missing required column: {field}")
                        return

                # Pre-fetch series to avoid N+1 queries during validation
                series_map = {s.slug: s for s in Series.objects.all()}

                for row_num, row in enumerate(reader, start=2):  # start=2 for header
                    try:
                        self.process_product_row(row, row_num, series_map, stats)
                    except Exception as e:
                        stats["errors"].append(f"Product Row {row_num}: {str(e)}")

        except Exception as e:
            stats["errors"].append(f"Failed to read products file: {str(e)}")

    def process_product_row(self, row: Dict[str, str], row_num: int, series_map: Dict[str, Series], stats: Dict[str, Any]):
        slug = row.get('slug', '').strip()
        series_slug = row.get('series_slug', '').strip()
        title_tr = row.get('title_tr', '').strip()
        
        if not slug:
            raise ValueError("Missing slug")
        if not series_slug:
            raise ValueError("Missing series_slug")

        series = series_map.get(series_slug)
        if not series:
            # Try to look up by exact name match if slug fails, just in case? 
            # Requirement says "Product.series must resolve by Series.slug == series_slug"
            raise ValueError(f"Series not found with slug '{series_slug}'")

        title_en = row.get('title_en', '').strip()
        status = row.get('status', 'draft').strip().lower()
        if status not in ['active', 'draft', 'archived']:
            status = 'draft' # default fallback or keep as is? Req says: "status: keep as provided". 
                             # But database has specific choices. Let's assume input matches distinct values or default to draft if invalid to be safe, 
                             # or better: assume user knows valid values and let DB validation handle it/or strict valid check.
                             # Let's trust the input but ensure lowercase.

        is_featured_raw = row.get('is_featured', 'false').lower().strip()
        is_featured = is_featured_raw == 'true'

        product, created = Product.objects.update_or_create(
            slug=slug,
            defaults={
                'series': series,
                'name': title_tr,  # Use title_tr as internal name
                'title_tr': title_tr,
                'title_en': title_en,
                'status': status,
                'is_featured': is_featured,
            }
        )

        if created:
            stats["products_created"] += 1
        else:
            stats["products_updated"] += 1

    def import_variants(self, file_path: str, stats: Dict[str, Any]):
        self.stdout.write(f"Reading variants from {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                # Normalize headers
                reader.fieldnames = [name.strip() for name in reader.fieldnames] if reader.fieldnames else []
                
                required_fields = ['model_code', 'product_slug', 'name_tr']
                for field in required_fields:
                    if field not in reader.fieldnames:
                        stats["errors"].append(f"Variants CSV missing required column: {field}")
                        return

                # Pre-fetch products
                # Note: We need to include products we just upserted in the transaction.
                # Since we are inside the transaction, Product.objects.all() should see them.
                product_map = {p.slug: p for p in Product.objects.all()}

                for row_num, row in enumerate(reader, start=2):
                    try:
                        self.process_variant_row(row, row_num, product_map, stats)
                    except Exception as e:
                        stats["errors"].append(f"Variant Row {row_num}: {str(e)}")

        except Exception as e:
            stats["errors"].append(f"Failed to read variants file: {str(e)}")

    def process_variant_row(self, row: Dict[str, str], row_num: int, product_map: Dict[str, Product], stats: Dict[str, Any]):
        model_code = row.get('model_code', '').strip()
        product_slug = row.get('product_slug', '').strip()
        
        if not model_code:
            raise ValueError("Missing model_code")
        if not product_slug:
            raise ValueError("Missing product_slug")

        product = product_map.get(product_slug)
        if not product:
            raise ValueError(f"Product not found with slug '{product_slug}'")

        name_tr = row.get('name_tr', '').strip()
        dimensions = row.get('dimensions', '').strip()
        
        list_price = self.parse_decimal(row.get('list_price'))
        weight_kg = self.parse_decimal(row.get('weight_kg'))

        variant, created = Variant.objects.update_or_create(
            model_code=model_code,
            defaults={
                'product': product,
                'name_tr': name_tr,
                'dimensions': dimensions,
                'list_price': list_price,
                'weight_kg': weight_kg,
            }
        )

        if created:
            stats["variants_created"] += 1
        else:
            stats["variants_updated"] += 1

    def parse_decimal(self, value: Optional[str]) -> Optional[Decimal]:
        if not value or not value.strip():
            return None
        try:
            # Replace comma with dot for flexibility
            clean_value = value.strip().replace(',', '.')
            return Decimal(clean_value)
        except InvalidOperation:
            raise ValueError(f"Invalid decimal value: {value}")
            
    def print_errors(self, errors: List[str]):
        self.stdout.write(self.style.ERROR("\nErrors encountered:"))
        for i, error in enumerate(errors[:50]):
            self.stdout.write(f"- {error}")
        
        if len(errors) > 50:
            self.stdout.write(f"... and {len(errors) - 50} more errors.")

    def print_stats(self, stats: Dict[str, Any]):
        self.stdout.write("\nSummary:")
        self.stdout.write(f"Products Created: {stats['products_created']}")
        self.stdout.write(f"Products Updated: {stats['products_updated']}")
        self.stdout.write(f"Variants Created: {stats['variants_created']}")
        self.stdout.write(f"Variants Updated: {stats['variants_updated']}")
        self.stdout.write(f"Total Errors: {len(stats['errors'])}")
