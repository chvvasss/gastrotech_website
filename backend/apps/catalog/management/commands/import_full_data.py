"""
Import COMPLETE site data from JSON export — full site reconstruction.

Version 2.1 — Fixed composite-key lookups for Series, TaxonomyNode, Category.
All operations are idempotent (safe to re-run multiple times).

Usage:
    # Import from default location
    python manage.py import_full_data

    # Import from specific file
    python manage.py import_full_data --file fixtures/full_site_data.json

    # Dry run (show what would happen, no changes)
    python manage.py import_full_data --dry-run

Imports (22 data sections in dependency order):
    1.  Media           → binary + metadata (images, PDFs, logos, favicons)
    2.  SpecKeys        → with icon_media FK
    3.  Categories      → hierarchy (two-pass for parent refs)
    4.  Brands          → with logo_media FK
    5.  BrandCategories → M2M through table
    6.  Series          → with category FK + cover FK
    7.  LogoGroups      → CategoryLogoGroup + LogoGroupSeries
    8.  TaxonomyNodes   → tree (two-pass for parent refs)
    9.  SpecTemplates   → with series FK
    10. Products        → ALL fields, FKs resolved
    11. ProductNodes    → M2M through table
    12. Variants        → ALL fields
    13. ProductMedia    → with alt + variant FK
    14. CatalogAssets   → general PDF catalogs
    15. CategoryCatalogs
    16. SiteSettings
    17. Users           → staff only, no passwords
    18. BlogCategories
    19. BlogTags
    20. BlogPosts       → with tags M2M + author FK
    21. ImportJobs
    22. AuditLogs

Data source: python manage.py export_full_data
"""

import base64
import json
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.dateparse import parse_datetime


BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DEFAULT_INPUT = BACKEND_DIR / "fixtures" / "full_site_data.json"


class Command(BaseCommand):
    help = "Import COMPLETE site data from JSON export — full reconstruction (v2.1)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=str(DEFAULT_INPUT),
            help=f"Input JSON file (default: {DEFAULT_INPUT})",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without making changes",
        )

    def handle(self, *args, **options):
        input_path = Path(options["file"])
        dry_run = options["dry_run"]
        start = time.time()

        if not input_path.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {input_path}"))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(self.style.MIGRATE_HEADING("  FULL SITE IMPORT v2.1"))
        self.stdout.write(self.style.MIGRATE_HEADING("  Reconstructs ALL site data from export"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(f"  Source: {input_path}")

        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data.get("_meta", {})
        self.stdout.write(f"  Format: {meta.get('format', 'unknown')}")
        self.stdout.write(f"  Version: {meta.get('version', 'unknown')}")
        self.stdout.write(f"  Exported at: {meta.get('exported_at', 'unknown')}")
        self.stdout.write(f"  Includes media bytes: {meta.get('includes_media_bytes', False)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n  DRY RUN — no changes will be made\n"))
            self._print_dry_run_summary(data)
            return

        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

        with transaction.atomic():
            # ── Order matters: dependencies first ──
            # 1. Media (no deps)
            self._import_media(data.get("media", []), stats)

            # Build media cache ONCE after importing media — used by all subsequent steps.
            # Uses only("id", "filename") to avoid loading the bytes column.
            from apps.catalog.models import Media
            self._media_cache = {}
            for m in Media.objects.only("id", "filename").iterator():
                # If duplicate filenames exist, keep the first occurrence
                if m.filename not in self._media_cache:
                    self._media_cache[m.filename] = m

            self.stdout.write(f"  Built media cache ({len(self._media_cache)} unique filenames)")

            # 2. SpecKeys (needs media for icon)
            self._import_spec_keys(data.get("spec_keys", []), stats)
            # 3. Categories (self-referential parent)
            self._import_categories(data.get("categories", []), stats)
            # 4. Brands (needs media for logo)
            self._import_brands(data.get("brands", []), stats)
            # 5. BrandCategories (needs brand + category)
            self._import_brand_categories(data.get("brand_categories", []), stats)
            # 6. Series (needs category + media)
            self._import_series(data.get("series", []), stats)
            # 7. LogoGroups (needs category + brand + series)
            self._import_logo_groups(data.get("category_logo_groups", []), stats)
            # 8. TaxonomyNodes (needs series, self-referential parent)
            self._import_taxonomy_nodes(data.get("taxonomy_nodes", []), stats)
            # 9. SpecTemplates (needs series)
            self._import_spec_templates(data.get("spec_templates", []), stats)
            # 10. Products (needs series, category, brand, node, media)
            self._import_products(data.get("products", []), stats)
            # 11. ProductNodes (needs product + node)
            self._import_product_nodes(data.get("product_nodes", []), stats)
            # 12. Variants (needs product)
            self._import_variants(data.get("variants", []), stats)
            # 13. ProductMedia (needs product + media + variant)
            self._import_product_media(data.get("product_media", []), stats)
            # 14. CatalogAssets (needs media)
            self._import_catalog_assets(data.get("catalog_assets", []), stats)
            # 15. CategoryCatalogs (needs category + media)
            self._import_category_catalogs(data.get("category_catalogs", []), stats)
            # 16. SiteSettings (no deps)
            self._import_site_settings(data.get("site_settings", []), stats)
            # 17. Users (needed by blog posts for author FK, and by ops)
            self._import_users(data.get("users", []), stats)
            # 18. BlogCategories (no deps)
            self._import_blog_categories(data.get("blog_categories", []), stats)
            # 19. BlogTags (no deps)
            self._import_blog_tags(data.get("blog_tags", []), stats)
            # 20. BlogPosts (needs blog_category + blog_tags + media + user)
            self._import_blog_posts(data.get("blog_posts", []), stats)
            # 21-22. Ops (informational, usually not critical for reconstruction)
            self._import_import_jobs(data.get("import_jobs", []), stats)
            self._import_audit_logs(data.get("audit_logs", []), stats)

        elapsed = time.time() - start
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  IMPORT COMPLETE"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"  Created: {stats['created']}")
        self.stdout.write(f"  Updated: {stats['updated']}")
        self.stdout.write(f"  Skipped: {stats['skipped']}")
        self.stdout.write(f"  Errors:  {stats['errors']}")
        self.stdout.write(f"  Time:    {elapsed:.1f}s")

    def _print_dry_run_summary(self, data):
        """Print summary of what would be imported."""
        total = 0
        for key, records in data.items():
            if key == "_meta":
                continue
            count = len(records) if isinstance(records, list) else 0
            self.stdout.write(f"  {key:.<30} {count} records")
            total += count
        self.stdout.write(f"\n  Total: {total} records across {len(data) - 1} sections")

    def _track(self, stats, created):
        """Track created/updated stats."""
        if created:
            stats["created"] += 1
        else:
            stats["updated"] += 1

    def _safe_decimal(self, value):
        """Safely convert to Decimal or return None."""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None

    # ────────────────────────────────────────────────────────────────
    #  CATALOG IMPORTS
    # ────────────────────────────────────────────────────────────────

    def _import_media(self, records, stats):
        """Import Media records with optional binary data."""
        from apps.catalog.models import Media

        count = len(records)
        self.stdout.write(f"  Importing {count} media records...")

        for i, r in enumerate(records, 1):
            if i % 200 == 0:
                self.stdout.write(f"    ... {i}/{count}")

            defaults = {
                "kind": r.get("kind", "image"),
                "content_type": r.get("content_type", ""),
                "size_bytes": r.get("size_bytes", 0),
                "checksum_sha256": r.get("checksum_sha256", ""),
            }
            if r.get("width") is not None:
                defaults["width"] = r["width"]
            if r.get("height") is not None:
                defaults["height"] = r["height"]
            if r.get("bytes_b64"):
                defaults["bytes"] = base64.b64decode(r["bytes_b64"])

            _, created = Media.objects.update_or_create(
                filename=r["filename"],
                defaults=defaults,
            )
            self._track(stats, created)

    def _import_spec_keys(self, records, stats):
        """Import SpecKey records with icon_media FK."""
        from apps.catalog.models import SpecKey

        self.stdout.write(f"  Importing {len(records)} spec keys...")

        for r in records:
            defaults = {
                "label_tr": r.get("label_tr", r["slug"]),
                "label_en": r.get("label_en", ""),
                "unit": r.get("unit", ""),
                "value_type": r.get("value_type", "text"),
                "sort_order": r.get("sort_order", 999),
            }
            icon_fn = r.get("icon_media_filename")
            if icon_fn:
                media_obj = self._media_cache.get(icon_fn)
                if media_obj:
                    defaults["icon_media"] = media_obj

            _, created = SpecKey.objects.update_or_create(
                slug=r["slug"],
                defaults=defaults,
            )
            self._track(stats, created)

    def _import_categories(self, records, stats):
        """Import Category records (two-pass for parent relationships).

        DB constraints:
        - unique(slug) WHERE parent IS NULL  (root categories)
        - unique(slug, parent)               (subcategories)

        Strategy: Pass 1 creates roots, pass 2 creates children + sets parents.
        """
        from apps.catalog.models import Category

        self.stdout.write(f"  Importing {len(records)} categories...")

        # Separate roots from children
        roots = [r for r in records if not r.get("parent_slug")]
        children = [r for r in records if r.get("parent_slug")]

        cat_map = {}  # slug → Category object (for roots)
        # For subcategories with same slug under different parents, we track (slug, parent_slug)
        cat_full_map = {}  # (slug, parent_slug_or_None) → Category

        # Pass 1: Create/update root categories
        for r in roots:
            defaults = {
                "name": r["name"],
                "menu_label": r.get("menu_label", ""),
                "description_short": r.get("description_short", ""),
                "order": r.get("order", 0),
                "is_featured": r.get("is_featured", True),
                "series_mode": r.get("series_mode", "disabled"),
                "parent": None,
            }
            cover_fn = r.get("cover_media_filename")
            if cover_fn:
                media_obj = self._media_cache.get(cover_fn)
                if media_obj:
                    defaults["cover_media"] = media_obj

            cat, created = Category.objects.update_or_create(
                slug=r["slug"],
                parent__isnull=True,
                defaults=defaults,
            )
            cat_map[r["slug"]] = cat
            cat_full_map[(r["slug"], None)] = cat
            self._track(stats, created)

        # Pass 2: Create/update child categories (with parent)
        for r in children:
            parent_slug = r["parent_slug"]
            parent = cat_map.get(parent_slug)
            if not parent:
                # Parent might be a child itself — look up from full map or DB
                parent = Category.objects.filter(slug=parent_slug).first()
                if not parent:
                    self.stderr.write(
                        self.style.WARNING(
                            f"    SKIP category '{r['slug']}': parent '{parent_slug}' not found"
                        )
                    )
                    stats["errors"] += 1
                    continue

            defaults = {
                "name": r["name"],
                "menu_label": r.get("menu_label", ""),
                "description_short": r.get("description_short", ""),
                "order": r.get("order", 0),
                "is_featured": r.get("is_featured", True),
                "series_mode": r.get("series_mode", "disabled"),
                "parent": parent,
            }
            cover_fn = r.get("cover_media_filename")
            if cover_fn:
                media_obj = self._media_cache.get(cover_fn)
                if media_obj:
                    defaults["cover_media"] = media_obj

            cat, created = Category.objects.update_or_create(
                slug=r["slug"],
                parent=parent,
                defaults=defaults,
            )
            cat_map[r["slug"]] = cat
            cat_full_map[(r["slug"], parent_slug)] = cat
            self._track(stats, created)

    def _import_brands(self, records, stats):
        """Import Brand records with logo_media, description, website."""
        from apps.catalog.models import Brand

        self.stdout.write(f"  Importing {len(records)} brands...")

        for r in records:
            defaults = {
                "name": r["name"],
                "description": r.get("description", ""),
                "website_url": r.get("website_url", ""),
                "order": r.get("order", 0),
                "is_active": r.get("is_active", True),
            }
            logo_fn = r.get("logo_media_filename")
            if logo_fn:
                media_obj = self._media_cache.get(logo_fn)
                if media_obj:
                    defaults["logo_media"] = media_obj

            _, created = Brand.objects.update_or_create(
                slug=r["slug"],
                defaults=defaults,
            )
            self._track(stats, created)

    def _import_brand_categories(self, records, stats):
        """Import BrandCategory through-table records."""
        from apps.catalog.models import Brand, BrandCategory, Category

        self.stdout.write(f"  Importing {len(records)} brand-category links...")
        brand_cache = {b.slug: b for b in Brand.objects.all()}
        cat_cache = {c.slug: c for c in Category.objects.all()}

        for r in records:
            brand = brand_cache.get(r.get("brand_slug"))
            category = cat_cache.get(r.get("category_slug"))
            if not brand or not category:
                stats["errors"] += 1
                continue

            _, created = BrandCategory.objects.update_or_create(
                brand=brand,
                category=category,
                defaults={
                    "is_active": r.get("is_active", True),
                    "order": r.get("order", 0),
                },
            )
            self._track(stats, created)

    def _import_series(self, records, stats):
        """Import Series records.

        DB constraint: unique(category, slug)
        Lookup key: (category, slug) — NOT slug alone.
        """
        from apps.catalog.models import Category, Series

        self.stdout.write(f"  Importing {len(records)} series...")
        cat_cache = {c.slug: c for c in Category.objects.all()}

        for r in records:
            category = cat_cache.get(r.get("category_slug"))
            if not category:
                self.stderr.write(
                    self.style.WARNING(
                        f"    SKIP series '{r['slug']}': category '{r.get('category_slug')}' not found"
                    )
                )
                stats["errors"] += 1
                continue

            defaults = {
                "name": r["name"],
                "description_short": r.get("description_short", ""),
                "order": r.get("order", 0),
                "is_featured": r.get("is_featured", False),
            }
            cover_fn = r.get("cover_media_filename")
            if cover_fn:
                media_obj = self._media_cache.get(cover_fn)
                if media_obj:
                    defaults["cover_media"] = media_obj

            _, created = Series.objects.update_or_create(
                category=category,
                slug=r["slug"],
                defaults=defaults,
            )
            self._track(stats, created)

    def _import_logo_groups(self, records, stats):
        """Import CategoryLogoGroup + LogoGroupSeries."""
        from apps.catalog.models import (
            Brand, Category, CategoryLogoGroup, LogoGroupSeries, Series,
        )

        self.stdout.write(f"  Importing {len(records)} logo groups...")
        cat_cache = {c.slug: c for c in Category.objects.all()}
        brand_cache = {b.slug: b for b in Brand.objects.all()}
        # Series slug is unique per category, so build composite cache
        series_cache = {}
        for s in Series.objects.select_related("category"):
            series_cache[(s.category.slug, s.slug)] = s
            # Also store by slug alone as fallback
            if s.slug not in series_cache:
                series_cache[s.slug] = s

        for r in records:
            category = cat_cache.get(r.get("category_slug"))
            brand = brand_cache.get(r.get("brand_slug"))
            if not category or not brand:
                stats["errors"] += 1
                continue

            lg, created = CategoryLogoGroup.objects.update_or_create(
                category=category,
                brand=brand,
                defaults={
                    "title": r.get("title", ""),
                    "order": r.get("order", 0),
                    "is_active": r.get("is_active", True),
                },
            )
            self._track(stats, created)

            # Recreate series links
            LogoGroupSeries.objects.filter(logo_group=lg).delete()
            for sl in r.get("series", []):
                series_slug = sl.get("series_slug")
                # Try composite lookup first (category_slug, series_slug)
                series = series_cache.get((category.slug, series_slug))
                if not series:
                    series = series_cache.get(series_slug)
                if series:
                    LogoGroupSeries.objects.create(
                        logo_group=lg,
                        series=series,
                        order=sl.get("order", 0),
                        is_heading=sl.get("is_heading", False),
                    )

    def _import_taxonomy_nodes(self, records, stats):
        """Import TaxonomyNode records (two-pass for parent).

        DB constraint: unique(series, parent, slug)
        Strategy: Pass 1 uses (series, slug) lookup, pass 2 sets parents.
        """
        from apps.catalog.models import Series, TaxonomyNode

        self.stdout.write(f"  Importing {len(records)} taxonomy nodes...")
        # Build series cache with composite key support
        series_cache = {}
        for s in Series.objects.select_related("category"):
            series_cache[s.slug] = s
            series_cache[(s.category.slug, s.slug)] = s

        # Pass 1: Create/update all nodes without parent
        node_map = {}  # (series_slug, slug) → Node, for disambiguation
        for r in records:
            series_slug = r.get("series_slug")
            series = series_cache.get(series_slug)
            if not series:
                stats["errors"] += 1
                continue

            defaults = {
                "name": r["name"],
                "order": r.get("order", 0),
            }

            # Try finding existing node by (series, slug) — without parent in pass 1
            try:
                node = TaxonomyNode.objects.get(series=series, slug=r["slug"], parent__isnull=True)
                for k, v in defaults.items():
                    setattr(node, k, v)
                node.save(update_fields=list(defaults.keys()) + ["updated_at"])
                created = False
            except TaxonomyNode.DoesNotExist:
                # Could be a child node — check if it exists with any parent
                existing = TaxonomyNode.objects.filter(series=series, slug=r["slug"]).first()
                if existing:
                    for k, v in defaults.items():
                        setattr(existing, k, v)
                    existing.save(update_fields=list(defaults.keys()) + ["updated_at"])
                    node = existing
                    created = False
                else:
                    node = TaxonomyNode.objects.create(
                        series=series,
                        slug=r["slug"],
                        **defaults,
                    )
                    created = True
            except TaxonomyNode.MultipleObjectsReturned:
                # If multiple exist, use the first one
                node = TaxonomyNode.objects.filter(series=series, slug=r["slug"]).first()
                for k, v in defaults.items():
                    setattr(node, k, v)
                node.save(update_fields=list(defaults.keys()) + ["updated_at"])
                created = False

            node_map[(series_slug, r["slug"])] = node
            self._track(stats, created)

        # Pass 2: Set parent relationships
        for r in records:
            parent_slug = r.get("parent_slug")
            if not parent_slug:
                continue

            series_slug = r.get("series_slug")
            parent_series_slug = r.get("parent_series_slug", series_slug)

            node = node_map.get((series_slug, r["slug"]))
            parent = node_map.get((parent_series_slug, parent_slug))

            if node and parent and node.parent_id != parent.pk:
                node.parent = parent
                node.save(update_fields=["parent", "updated_at"])

    def _import_spec_templates(self, records, stats):
        """Import SpecTemplate records."""
        from apps.catalog.models import Series, SpecTemplate

        self.stdout.write(f"  Importing {len(records)} spec templates...")
        series_cache = {s.slug: s for s in Series.objects.all()}

        for r in records:
            series = series_cache.get(r.get("applies_to_series_slug"))
            defaults = {
                "spec_layout": r.get("spec_layout", []),
                "default_general_features": r.get("default_general_features", []),
                "default_notes": r.get("default_notes", []),
                "applies_to_series": series,
                "applies_to_parent_taxonomy_slug": r.get(
                    "applies_to_parent_taxonomy_slug", ""
                ),
            }
            _, created = SpecTemplate.objects.update_or_create(
                name=r["name"],
                defaults=defaults,
            )
            self._track(stats, created)

    def _import_products(self, records, stats):
        """Import Product records — ALL fields."""
        from apps.catalog.models import (
            Brand, Category, Product, Series, TaxonomyNode,
        )

        self.stdout.write(f"  Importing {len(records)} products...")
        series_cache = {s.slug: s for s in Series.objects.all()}
        cat_cache = {c.slug: c for c in Category.objects.all()}
        brand_cache = {b.slug: b for b in Brand.objects.all()}
        node_cache = {n.slug: n for n in TaxonomyNode.objects.all()}

        for r in records:
            series = series_cache.get(r.get("series_slug"))
            category = cat_cache.get(r.get("category_slug"))
            brand = brand_cache.get(r.get("brand_slug"))
            primary_node = node_cache.get(r.get("primary_node_slug"))

            defaults = {
                "name": r.get("name", ""),
                "title_tr": r.get("title_tr", ""),
                "title_en": r.get("title_en", ""),
                "series": series,
                "category": category,
                "brand": brand,
                "primary_node": primary_node,
                "status": r.get("status", "active"),
                "is_featured": r.get("is_featured", False),
                "general_features": r.get("general_features", []),
                "notes": r.get("notes", []),
                "spec_layout": r.get("spec_layout", []),
                "pdf_ref": r.get("pdf_ref", ""),
                "short_specs": r.get("short_specs", []),
                "long_description": r.get("long_description", ""),
                "seo_title": r.get("seo_title", ""),
                "seo_description": r.get("seo_description", ""),
            }

            og_fn = r.get("og_media_filename")
            if og_fn:
                media_obj = self._media_cache.get(og_fn)
                if media_obj:
                    defaults["og_media"] = media_obj

            _, created = Product.objects.update_or_create(
                slug=r["slug"],
                defaults=defaults,
            )
            self._track(stats, created)

    def _import_product_nodes(self, records, stats):
        """Import ProductNode M2M through-table."""
        from apps.catalog.models import Product, ProductNode, TaxonomyNode

        self.stdout.write(f"  Importing {len(records)} product-node links...")
        product_cache = {p.slug: p for p in Product.objects.all()}
        node_cache = {n.slug: n for n in TaxonomyNode.objects.all()}

        for r in records:
            product = product_cache.get(r.get("product_slug"))
            node = node_cache.get(r.get("node_slug"))
            if not product or not node:
                stats["errors"] += 1
                continue

            _, created = ProductNode.objects.get_or_create(
                product=product,
                node=node,
            )
            self._track(stats, created)

    def _import_variants(self, records, stats):
        """Import Variant records — ALL fields."""
        from apps.catalog.models import Product, Variant

        self.stdout.write(f"  Importing {len(records)} variants...")
        product_cache = {p.slug: p for p in Product.objects.all()}

        for r in records:
            product = product_cache.get(r.get("product_slug"))

            defaults = {
                "product": product,
                "name_tr": r.get("name_tr", ""),
                "name_en": r.get("name_en", ""),
                "sku": r.get("sku", "") or "",
                "dimensions": r.get("dimensions", ""),
                "weight_kg": self._safe_decimal(r.get("weight_kg")),
                "list_price": self._safe_decimal(r.get("list_price")),
                "price_override": self._safe_decimal(r.get("price_override")),
                "specs": r.get("specs", {}),
                "size": r.get("size", ""),
                "color": r.get("color", ""),
                "stock_qty": r.get("stock_qty"),
            }
            _, created = Variant.objects.update_or_create(
                model_code=r["model_code"],
                defaults=defaults,
            )
            self._track(stats, created)

    def _import_product_media(self, records, stats):
        """Import ProductMedia links with alt text and variant reference."""
        from apps.catalog.models import Product, ProductMedia, Variant

        self.stdout.write(f"  Importing {len(records)} product-media links...")
        product_cache = {p.slug: p for p in Product.objects.all()}
        variant_cache = {v.model_code: v for v in Variant.objects.all()}

        for r in records:
            product = product_cache.get(r.get("product_slug"))
            media = self._media_cache.get(r.get("media_filename"))
            if not product or not media:
                stats["errors"] += 1
                continue

            variant = variant_cache.get(r.get("variant_model_code"))

            _, created = ProductMedia.objects.update_or_create(
                product=product,
                media=media,
                defaults={
                    "variant": variant,
                    "alt": r.get("alt", ""),
                    "sort_order": r.get("sort_order", 0),
                    "is_primary": r.get("is_primary", False),
                },
            )
            self._track(stats, created)

    def _import_catalog_assets(self, records, stats):
        """Import CatalogAsset records (general downloadable catalogs)."""
        from apps.catalog.models import CatalogAsset

        self.stdout.write(f"  Importing {len(records)} catalog assets...")

        for r in records:
            media = self._media_cache.get(r.get("media_filename"))
            if not media:
                stats["errors"] += 1
                continue

            _, created = CatalogAsset.objects.update_or_create(
                title_tr=r["title_tr"],
                media=media,
                defaults={
                    "title_en": r.get("title_en", ""),
                    "is_primary": r.get("is_primary", False),
                    "order": r.get("order", 0),
                    "published": r.get("published", True),
                },
            )
            self._track(stats, created)

    def _import_category_catalogs(self, records, stats):
        """Import CategoryCatalog records."""
        from apps.catalog.models import Category, CategoryCatalog

        self.stdout.write(f"  Importing {len(records)} category catalogs...")
        cat_cache = {c.slug: c for c in Category.objects.all()}

        for r in records:
            category = cat_cache.get(r.get("category_slug"))
            media = self._media_cache.get(r.get("media_filename"))
            if not category:
                stats["errors"] += 1
                continue

            defaults = {
                "title_en": r.get("title_en", ""),
                "description": r.get("description", ""),
                "order": r.get("order", 0),
                "published": r.get("published", True),
            }
            if media:
                defaults["media"] = media

            _, created = CategoryCatalog.objects.update_or_create(
                category=category,
                title_tr=r.get("title_tr", ""),
                defaults=defaults,
            )
            self._track(stats, created)

    # ────────────────────────────────────────────────────────────────
    #  COMMON IMPORTS
    # ────────────────────────────────────────────────────────────────

    def _import_site_settings(self, records, stats):
        """Import SiteSetting records."""
        from apps.common.models import SiteSetting

        self.stdout.write(f"  Importing {len(records)} site settings...")
        for r in records:
            _, created = SiteSetting.objects.update_or_create(
                key=r["key"],
                defaults={
                    "value": r.get("value", {}),
                    "description": r.get("description", ""),
                },
            )
            self._track(stats, created)

    # ────────────────────────────────────────────────────────────────
    #  ACCOUNTS IMPORTS
    # ────────────────────────────────────────────────────────────────

    def _import_users(self, records, stats):
        """Import staff User accounts (no passwords — they must be reset)."""
        from apps.accounts.models import User

        self.stdout.write(f"  Importing {len(records)} staff users...")
        for r in records:
            user, created = User.objects.get_or_create(
                email=r["email"],
                defaults={
                    "first_name": r.get("first_name", ""),
                    "last_name": r.get("last_name", ""),
                    "role": r.get("role", "editor"),
                    "is_active": r.get("is_active", True),
                    "is_staff": r.get("is_staff", True),
                    "is_superuser": r.get("is_superuser", False),
                },
            )
            if created:
                # Set unusable password — admin must reset
                user.set_unusable_password()
                user.save(update_fields=["password"])
                stats["created"] += 1
            else:
                stats["skipped"] += 1

    # ────────────────────────────────────────────────────────────────
    #  BLOG IMPORTS
    # ────────────────────────────────────────────────────────────────

    def _import_blog_categories(self, records, stats):
        """Import BlogCategory records."""
        from apps.blog.models import BlogCategory

        self.stdout.write(f"  Importing {len(records)} blog categories...")
        for r in records:
            _, created = BlogCategory.objects.update_or_create(
                slug=r["slug"],
                defaults={
                    "name_tr": r.get("name_tr", ""),
                    "name_en": r.get("name_en", ""),
                    "description": r.get("description", ""),
                    "order": r.get("order", 0),
                    "is_active": r.get("is_active", True),
                },
            )
            self._track(stats, created)

    def _import_blog_tags(self, records, stats):
        """Import BlogTag records."""
        from apps.blog.models import BlogTag

        self.stdout.write(f"  Importing {len(records)} blog tags...")
        for r in records:
            _, created = BlogTag.objects.update_or_create(
                slug=r["slug"],
                defaults={
                    "name": r.get("name", r["slug"]),
                },
            )
            self._track(stats, created)

    def _import_blog_posts(self, records, stats):
        """Import BlogPost records with tags M2M and author FK."""
        from apps.accounts.models import User
        from apps.blog.models import BlogCategory, BlogPost, BlogTag

        self.stdout.write(f"  Importing {len(records)} blog posts...")
        cat_cache = {c.slug: c for c in BlogCategory.objects.all()}
        tag_cache = {t.slug: t for t in BlogTag.objects.all()}
        user_cache = {u.email: u for u in User.objects.all()}

        for r in records:
            category = cat_cache.get(r.get("category_slug"))
            cover = self._media_cache.get(r.get("cover_media_filename"))
            author = user_cache.get(r.get("author_email"))

            published_at = None
            if r.get("published_at"):
                published_at = parse_datetime(r["published_at"])

            defaults = {
                "title": r.get("title", ""),
                "excerpt": r.get("excerpt", ""),
                "content": r.get("content", ""),
                "category": category,
                "cover_media": cover,
                "author": author,
                "status": r.get("status", "draft"),
                "published_at": published_at,
                "is_featured": r.get("is_featured", False),
                "view_count": r.get("view_count", 0),
                "reading_time_min": r.get("reading_time_min", 1),
                "meta_title": r.get("meta_title", ""),
                "meta_description": r.get("meta_description", ""),
            }

            post, created = BlogPost.objects.update_or_create(
                slug=r["slug"],
                defaults=defaults,
            )
            self._track(stats, created)

            # Set tags M2M
            tag_slugs = r.get("tag_slugs", [])
            if tag_slugs:
                tags = [tag_cache[s] for s in tag_slugs if s in tag_cache]
                post.tags.set(tags)

    # ────────────────────────────────────────────────────────────────
    #  OPS IMPORTS
    # ────────────────────────────────────────────────────────────────

    def _import_import_jobs(self, records, stats):
        """Import ImportJob history (informational)."""
        from apps.accounts.models import User
        from apps.ops.models import ImportJob

        self.stdout.write(f"  Importing {len(records)} import jobs...")
        user_cache = {u.email: u for u in User.objects.all()}

        for r in records:
            created_by = user_cache.get(r.get("created_by_email"))
            started_at = parse_datetime(r["started_at"]) if r.get("started_at") else None
            completed_at = parse_datetime(r["completed_at"]) if r.get("completed_at") else None

            defaults = {
                "status": r.get("status", "success"),
                "mode": r.get("mode", "strict"),
                "created_by": created_by,
                "file_hash": r.get("file_hash", ""),
                "is_preview": r.get("is_preview", True),
                "total_rows": r.get("total_rows", 0),
                "created_count": r.get("created_count", 0),
                "updated_count": r.get("updated_count", 0),
                "skipped_count": r.get("skipped_count", 0),
                "error_count": r.get("error_count", 0),
                "warning_count": r.get("warning_count", 0),
                "report_json": r.get("report_json", {}),
                "started_at": started_at,
                "completed_at": completed_at,
            }

            # ImportJob doesn't have a natural key — use kind + file_hash
            file_hash = r.get("file_hash", "")
            if file_hash:
                _, created = ImportJob.objects.update_or_create(
                    kind=r["kind"],
                    file_hash=file_hash,
                    defaults=defaults,
                )
                self._track(stats, created)
            else:
                stats["skipped"] += 1

    def _import_audit_logs(self, records, stats):
        """Import AuditLog records (informational, append-only)."""
        from apps.ops.models import AuditLog

        self.stdout.write(f"  Importing {len(records)} audit logs...")
        # Audit logs are append-only — skip if already exists
        existing = set()
        for al in AuditLog.objects.values_list("entity_type", "entity_id", "action"):
            existing.add(al)

        created_count = 0
        for r in records:
            key = (r.get("entity_type", ""), r.get("entity_id", ""), r.get("action", ""))
            if key in existing:
                stats["skipped"] += 1
                continue

            AuditLog.objects.create(
                actor_email=r.get("actor_email", ""),
                action=r.get("action", ""),
                entity_type=r.get("entity_type", ""),
                entity_id=r.get("entity_id", ""),
                entity_label=r.get("entity_label", ""),
                before_json=r.get("before_json", {}),
                after_json=r.get("after_json", {}),
                metadata=r.get("metadata", {}),
                ip_address=r.get("ip_address"),
                user_agent=r.get("user_agent", ""),
            )
            existing.add(key)
            stats["created"] += 1
            created_count += 1

        if created_count:
            self.stdout.write(f"    Created {created_count} new audit log entries")
