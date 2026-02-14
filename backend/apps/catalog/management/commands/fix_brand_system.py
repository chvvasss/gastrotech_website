"""
Django management command to fix brand system issues.

This command:
1. Renames lowercase brands to proper case (e.g., rational -> Rational)
2. Fixes series-brand mappings for Fırın category products
3. Generates an audit report
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Brand, Product, Series


class Command(BaseCommand):
    help = "Fix brand system: rename brands to proper case and fix product-brand mappings"

    # Brand renaming map: current lowercase slug -> (new name, new slug)
    BRAND_RENAME_MAP = {
        "rational": ("Rational", "rational"),
        "thermospeed": ("Thermospeed", "thermospeed"),
        "skyline": ("Skyline", "skyline"),
        "maestro": ("MAESTRO", "maestro"),
        # prime is already uppercase as PRIME
    }

    # Series -> Brand mapping (series slug -> target brand slug)
    SERIES_BRAND_MAP = {
        # Rational series
        "i-combi-classic-serisi": "rational",
        "i-vario": "rational",
        "i-vario-serisi": "rational",
        "rational-aksesuarlar": "rational",
        "tepsiler-ve-tabletler": "rational",
        "i-combi-aksesuarlar": "rational",
        "i-vario-aksesuarlar": "rational",
        # Thermospeed series
        "thermospeed": "thermospeed",
        "thermospeed-serisi": "thermospeed",
        # Skyline series
        "skyline-premium-s-serisi": "skyline",
        # MAESTRO series
        "maestro-e-touch": "maestro",
        "maestro-gazli": "maestro",
        "maestro-elektrikli": "maestro",
        "maestro-serisi": "maestro",
        # PRIME series
        "prime-gp": "prime",
        "prime-ep": "prime",
        "prime-gpm": "prime",
        "prime-epm": "prime",
        "prime-serisi": "prime",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(self.style.NOTICE("BRAND SYSTEM FIX"))
        self.stdout.write(self.style.NOTICE("=" * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        # Step 1: Audit current state
        self._audit_brands()

        # Step 2: Rename lowercase brands to proper case
        self._rename_brands(dry_run)

        # Step 3: Fix series-based brand assignments
        self._fix_series_brand_mappings(dry_run)

        # Step 4: Final audit
        self.stdout.write(self.style.NOTICE("\n" + "=" * 60))
        self.stdout.write(self.style.NOTICE("FINAL STATE"))
        self.stdout.write(self.style.NOTICE("=" * 60))
        self._audit_brands()

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN - No changes made. Run without --dry-run to apply."))
        else:
            self.stdout.write(self.style.SUCCESS("\n[OK] Brand system fix completed successfully!"))

    def _audit_brands(self):
        """Show current brand distribution."""
        self.stdout.write(self.style.NOTICE("\nBrand Distribution:"))
        
        brands = Brand.objects.all().order_by("name")
        for brand in brands:
            product_count = Product.objects.filter(brand=brand).count()
            needs_rename = brand.slug in self.BRAND_RENAME_MAP
            status = "[NEEDS RENAME]" if needs_rename else ""
            self.stdout.write(f"  {brand.name}: {product_count} products {status}")

    def _rename_brands(self, dry_run: bool):
        """Rename lowercase brands to proper case."""
        self.stdout.write(self.style.NOTICE("\n--- Phase 1: Rename brands to proper case ---"))

        renamed_count = 0
        for old_slug, (new_name, new_slug) in self.BRAND_RENAME_MAP.items():
            try:
                brand = Brand.objects.get(slug=old_slug)
                if brand.name != new_name:
                    self.stdout.write(f"  Renaming '{brand.name}' -> '{new_name}'")
                    if not dry_run:
                        with transaction.atomic():
                            brand.name = new_name
                            brand.save()
                    renamed_count += 1
                else:
                    self.stdout.write(f"  '{brand.name}' already has correct name")
            except Brand.DoesNotExist:
                self.stdout.write(f"  Brand with slug '{old_slug}' not found - skipping")

        self.stdout.write(self.style.SUCCESS(f"  Total brands renamed: {renamed_count}"))

    def _fix_series_brand_mappings(self, dry_run: bool):
        """Ensure products in specific series have the correct brand."""
        self.stdout.write(self.style.NOTICE("\n--- Phase 2: Fix series-brand mappings ---"))

        total_updated = 0
        for series_slug, brand_slug in self.SERIES_BRAND_MAP.items():
            try:
                series = Series.objects.get(slug=series_slug)
                # Handle PRIME special case (slug is 'prime' but we need to check variations)
                try:
                    brand = Brand.objects.get(slug=brand_slug)
                except Brand.DoesNotExist:
                    # Try uppercase slug for PRIME
                    brand = Brand.objects.filter(name__iexact=brand_slug.upper()).first()
                    if not brand:
                        continue
            except Series.DoesNotExist:
                continue

            # Find products in this series with wrong brand
            wrong_brand_products = Product.objects.filter(
                series=series
            ).exclude(brand=brand)

            count = wrong_brand_products.count()
            if count > 0:
                self.stdout.write(
                    f"  Series '{series_slug}' -> {brand.name}: {count} products to fix"
                )
                if not dry_run:
                    with transaction.atomic():
                        wrong_brand_products.update(brand=brand)
                total_updated += count

        self.stdout.write(self.style.SUCCESS(f"  Total products updated: {total_updated}"))

