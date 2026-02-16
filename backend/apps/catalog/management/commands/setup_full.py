"""
Full database setup - single command to get a complete working site.

Usage:
    # Full setup (everything)
    python manage.py setup_full

    # Quick setup (skip images for speed)
    python manage.py setup_full --skip-images

    # Skip PDFs too
    python manage.py setup_full --skip-images --skip-pdfs

    # Dry run (show what would happen)
    python manage.py setup_full --dry-run

This will:
    1. Run migrations (ensure DB schema is ready)
    2. Load categories + catalog PDFs (setup_db)
    3. Seed master hierarchy (brands, series, logo groups)
    4. Import products from Excel (Gastrotech_Tum_Veriler.xlsx)
    5. Upload product images (from urunlerfotoupload/)
    6. Sync spec keys from imported data
    7. Set default site settings (show_prices, catalog_mode)
    8. Create dev admin user (dev mode only)
    9. Clear cache
"""

import time
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand


# Resolve project root (backend/)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
FIXTURES_DIR = BACKEND_DIR / "fixtures"
EXCEL_PATH = BACKEND_DIR / "Gastrotech_Tum_Veriler.xlsx"
IMAGES_EXCEL = BACKEND_DIR / "urunlerfotoupload" / "gastrotech_product_images_final3_summary.xlsx"
IMAGES_DIR = BACKEND_DIR / "urunlerfotoupload"


class Command(BaseCommand):
    help = "Full database setup: categories, brands, products, images, specs, settings, admin"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Skip product image upload (faster setup)",
        )
        parser.add_argument(
            "--skip-pdfs",
            action="store_true",
            help="Skip catalog PDF import",
        )
        parser.add_argument(
            "--skip-products",
            action="store_true",
            help="Skip product import from Excel",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        skip_images = options["skip_images"]
        skip_pdfs = options["skip_pdfs"]
        skip_products = options["skip_products"]
        total_start = time.time()

        self._banner("GASTROTECH FULL SETUP")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - no changes will be made\n"))

        # ── Step 1: Migrations ────────────────────────────
        self._step("1/9", "Running database migrations")
        if not dry_run:
            try:
                call_command("migrate", "--noinput", verbosity=0)
                self.stdout.write(self.style.SUCCESS("  Migrations applied"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  Migration failed: {e}"))
                return
        else:
            self.stdout.write("  Would run: python manage.py migrate --noinput")

        # ── Step 2: Categories + Catalog PDFs (setup_db) ──
        self._step("2/9", "Loading categories & catalog PDFs")
        if not dry_run:
            try:
                setup_db_args = []
                if skip_pdfs:
                    setup_db_args.append("--skip-pdfs")
                call_command("setup_db", *setup_db_args, verbosity=1)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  setup_db failed: {e}"))
                self.stderr.write("  Continuing with remaining steps...")
        else:
            msg = "  Would run: python manage.py setup_db"
            if skip_pdfs:
                msg += " --skip-pdfs"
            self.stdout.write(msg)

        # ── Step 3: Master Hierarchy (brands, series, logo groups) ──
        self._step("3/9", "Seeding master hierarchy (brands, series, categories)")
        if not dry_run:
            try:
                call_command("seed_master_hierarchy", verbosity=1)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  seed_master_hierarchy failed: {e}"))
                self.stderr.write("  Continuing with remaining steps...")
        else:
            self.stdout.write("  Would run: python manage.py seed_master_hierarchy")

        # ── Step 4: Import Products from Excel ────────────
        self._step("4/9", "Importing products from Excel")
        if skip_products:
            self.stdout.write(self.style.WARNING("  SKIPPED (--skip-products)"))
        elif not EXCEL_PATH.exists():
            self.stderr.write(self.style.WARNING(
                f"  Excel file not found: {EXCEL_PATH}\n"
                "  Skipping product import. Add the file and re-run."
            ))
        elif not dry_run:
            try:
                self._import_products_from_excel()
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  Product import failed: {e}"))
                self.stderr.write("  Continuing with remaining steps...")
        else:
            self.stdout.write(f"  Would import products from: {EXCEL_PATH}")

        # ── Step 5: Upload Product Images ─────────────────
        self._step("5/9", "Uploading product images")
        if skip_images:
            self.stdout.write(self.style.WARNING("  SKIPPED (--skip-images)"))
        elif not IMAGES_EXCEL.exists():
            self.stderr.write(self.style.WARNING(
                f"  Images Excel not found: {IMAGES_EXCEL}\n"
                "  Skipping image upload. Add the file and re-run."
            ))
        elif not dry_run:
            try:
                call_command(
                    "upload_product_images",
                    excel=str(IMAGES_EXCEL),
                    images=str(IMAGES_DIR),
                    skip_existing=True,
                    verbosity=1,
                )
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  Image upload failed: {e}"))
                self.stderr.write("  Continuing with remaining steps...")
        else:
            self.stdout.write(f"  Would upload images from: {IMAGES_DIR}")

        # ── Step 6: Sync Spec Keys ────────────────────────
        self._step("6/9", "Syncing spec keys from data")
        if not dry_run:
            try:
                call_command("seed_specs_from_data", verbosity=1)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  Spec key sync failed: {e}"))
        else:
            self.stdout.write("  Would run: python manage.py seed_specs_from_data")

        # ── Step 7: Site Settings ─────────────────────────
        self._step("7/9", "Configuring default site settings")
        if not dry_run:
            try:
                self._setup_site_settings()
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  Site settings failed: {e}"))
        else:
            self.stdout.write("  Would set: show_prices=False, catalog_mode=False")

        # ── Step 8: Dev Admin User ────────────────────────
        self._step("8/9", "Creating dev admin user")
        if not dry_run:
            try:
                call_command("ensure_dev_admin", verbosity=1)
            except Exception as e:
                self.stderr.write(self.style.WARNING(f"  Admin creation skipped: {e}"))
        else:
            self.stdout.write("  Would run: python manage.py ensure_dev_admin")

        # ── Step 9: Clear Cache ───────────────────────────
        self._step("9/9", "Clearing cache")
        if not dry_run:
            try:
                from django.core.cache import cache
                cache.clear()
                self.stdout.write(self.style.SUCCESS("  Cache cleared"))
            except Exception as e:
                self.stderr.write(self.style.WARNING(f"  Cache clear failed: {e}"))
        else:
            self.stdout.write("  Would clear Django cache")

        # ── Summary ───────────────────────────────────────
        elapsed = time.time() - total_start
        self.stdout.write("")
        self._banner("SETUP COMPLETE")
        self._print_summary(dry_run, elapsed)

    def _import_products_from_excel(self):
        """Import products from Gastrotech_Tum_Veriler.xlsx using pandas."""
        try:
            import pandas as pd
        except ImportError:
            self.stderr.write(self.style.ERROR(
                "  pandas not installed. Run: pip install pandas openpyxl"
            ))
            return

        from django.db import transaction
        from apps.catalog.models import (
            Brand, Category, Product, Series, Variant,
        )

        df = pd.read_excel(str(EXCEL_PATH), engine="openpyxl")
        self.stdout.write(f"  Loaded {len(df)} rows from Excel")

        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]

        # Pre-fetch lookups
        categories = {c.slug: c for c in Category.objects.all()}
        series_map = {s.slug: s for s in Series.objects.all()}
        brands = {b.slug: b for b in Brand.objects.all()}

        stats = {
            "products_created": 0,
            "products_updated": 0,
            "variants_created": 0,
            "variants_updated": 0,
            "errors": 0,
        }

        # Try to detect column mapping
        col_map = self._detect_columns(df)
        if not col_map:
            self.stderr.write(self.style.ERROR(
                "  Could not detect column mapping from Excel. "
                "Expected columns: model_code/kod, name/isim, series/seri, category/kategori"
            ))
            return

        with transaction.atomic():
            for idx, row in df.iterrows():
                try:
                    self._process_excel_row(
                        row, col_map, categories, series_map, brands, stats
                    )
                except Exception as e:
                    stats["errors"] += 1
                    if stats["errors"] <= 10:
                        self.stderr.write(f"  Row {idx}: {e}")

        self.stdout.write(self.style.SUCCESS(
            f"  Products: {stats['products_created']} created, {stats['products_updated']} updated"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"  Variants: {stats['variants_created']} created, {stats['variants_updated']} updated"
        ))
        if stats["errors"]:
            self.stderr.write(self.style.WARNING(f"  Errors: {stats['errors']}"))

    def _detect_columns(self, df):
        """Detect column mapping from Excel headers."""
        cols = set(df.columns)
        mapping = {}

        # Model code
        for candidate in ["model_code", "kod", "code", "model_kodu", "variant_code"]:
            if candidate in cols:
                mapping["model_code"] = candidate
                break

        # Product/variant name
        for candidate in ["name", "isim", "name_tr", "urun_adi", "adi", "ad"]:
            if candidate in cols:
                mapping["name"] = candidate
                break

        # Series
        for candidate in ["series", "seri", "series_slug", "seri_slug"]:
            if candidate in cols:
                mapping["series"] = candidate
                break

        # Category
        for candidate in ["category", "kategori", "category_slug", "kategori_slug"]:
            if candidate in cols:
                mapping["category"] = candidate
                break

        # Brand
        for candidate in ["brand", "marka", "brand_slug", "marka_slug"]:
            if candidate in cols:
                mapping["brand"] = candidate
                break

        # Dimensions
        for candidate in ["dimensions", "boyutlar", "olculer"]:
            if candidate in cols:
                mapping["dimensions"] = candidate
                break

        # Weight
        for candidate in ["weight_kg", "agirlik", "weight", "agirlik_kg"]:
            if candidate in cols:
                mapping["weight"] = candidate
                break

        # Price
        for candidate in ["list_price", "fiyat", "price", "liste_fiyat"]:
            if candidate in cols:
                mapping["price"] = candidate
                break

        # Product slug
        for candidate in ["product_slug", "slug", "urun_slug"]:
            if candidate in cols:
                mapping["slug"] = candidate
                break

        # Product title
        for candidate in ["title_tr", "baslik", "urun_baslik", "product_name", "product_title"]:
            if candidate in cols:
                mapping["title"] = candidate
                break

        # Must have at least model_code to proceed
        if "model_code" not in mapping:
            return None

        return mapping

    def _process_excel_row(self, row, col_map, categories, series_map, brands, stats):
        """Process a single Excel row into Product + Variant."""
        from decimal import Decimal, InvalidOperation
        from django.utils.text import slugify
        from apps.catalog.models import Product, Series, Variant

        model_code = str(row.get(col_map["model_code"], "")).strip()
        if not model_code or model_code == "nan":
            return

        # Get or detect series
        series = None
        if "series" in col_map:
            series_val = str(row.get(col_map["series"], "")).strip()
            if series_val and series_val != "nan":
                series_slug = slugify(series_val)
                series = series_map.get(series_slug)

        # Get name
        name = ""
        if "name" in col_map:
            name = str(row.get(col_map["name"], "")).strip()
            if name == "nan":
                name = ""

        # Get title
        title = ""
        if "title" in col_map:
            title = str(row.get(col_map["title"], "")).strip()
            if title == "nan":
                title = ""

        if not name and not title:
            name = model_code

        # Get product slug
        product_slug = ""
        if "slug" in col_map:
            product_slug = str(row.get(col_map["slug"], "")).strip()
            if product_slug == "nan":
                product_slug = ""

        if not product_slug:
            product_slug = slugify(title or name or model_code)

        # Dimensions
        dimensions = ""
        if "dimensions" in col_map:
            dimensions = str(row.get(col_map["dimensions"], "")).strip()
            if dimensions == "nan":
                dimensions = ""

        # Weight
        weight_kg = None
        if "weight" in col_map:
            try:
                w = row.get(col_map["weight"])
                if w and str(w) != "nan":
                    weight_kg = Decimal(str(w).replace(",", "."))
            except (InvalidOperation, ValueError):
                pass

        # Price
        list_price = None
        if "price" in col_map:
            try:
                p = row.get(col_map["price"])
                if p and str(p) != "nan":
                    list_price = Decimal(str(p).replace(",", "."))
            except (InvalidOperation, ValueError):
                pass

        # Find or create product
        product, p_created = Product.objects.update_or_create(
            slug=product_slug,
            defaults={
                "title_tr": title or name,
                "series": series,
                "status": "active",
            },
        )
        if p_created:
            stats["products_created"] += 1
        else:
            stats["products_updated"] += 1

        # Find or create variant
        variant, v_created = Variant.objects.update_or_create(
            model_code=model_code,
            defaults={
                "product": product,
                "name_tr": name or title,
                "dimensions": dimensions or None,
                "weight_kg": weight_kg,
                "list_price": list_price,
                "is_active": True,
            },
        )
        if v_created:
            stats["variants_created"] += 1
        else:
            stats["variants_updated"] += 1

    def _setup_site_settings(self):
        """Set default site settings."""
        from apps.common.models import SiteSetting

        defaults = [
            ("show_prices", {"value": False}, "Show prices on public site"),
            ("catalog_mode", {"value": False}, "Enable catalog-only mode (hides products)"),
        ]

        for key, value, description in defaults:
            setting, created = SiteSetting.objects.get_or_create(
                key=key,
                defaults={"value": value, "description": description},
            )
            status = "created" if created else "exists"
            self.stdout.write(f"  {key} = {value} ({status})")

    def _print_summary(self, dry_run, elapsed):
        """Print final summary with database counts."""
        if dry_run:
            self.stdout.write(self.style.WARNING(
                "  DRY RUN complete. No changes were made."
            ))
            self.stdout.write(f"  Elapsed: {elapsed:.1f}s")
            return

        from apps.catalog.models import (
            Brand, Category, CategoryCatalog, Media, Product,
            ProductMedia, Series, SpecKey, Variant,
        )

        self.stdout.write(f"  Categories:       {Category.objects.count()}")
        self.stdout.write(f"  Brands:           {Brand.objects.count()}")
        self.stdout.write(f"  Series:           {Series.objects.count()}")
        self.stdout.write(f"  Products:         {Product.objects.count()}")
        self.stdout.write(f"  Variants:         {Variant.objects.count()}")
        self.stdout.write(f"  Product Images:   {ProductMedia.objects.count()}")
        self.stdout.write(f"  Catalog PDFs:     {CategoryCatalog.objects.count()}")
        self.stdout.write(f"  Media Files:      {Media.objects.count()}")
        self.stdout.write(f"  Spec Keys:        {SpecKey.objects.count()}")
        self.stdout.write(f"  Elapsed:          {elapsed:.1f}s")
        self.stdout.write("")
        self.stdout.write("  Admin login: admin@gastrotech.com / admin123")
        self.stdout.write("")

    def _banner(self, text):
        """Print a banner line."""
        line = "=" * 56
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(line))
        self.stdout.write(self.style.SUCCESS(f"  {text}"))
        self.stdout.write(self.style.SUCCESS(line))
        self.stdout.write("")

    def _step(self, number, description):
        """Print a step header."""
        self.stdout.write(self.style.MIGRATE_HEADING(f"[{number}] {description}"))
