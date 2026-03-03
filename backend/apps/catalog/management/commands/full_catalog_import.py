"""
Full catalog reset & import from a flat JSON product list.

Usage:
    python manage.py full_catalog_import --file data.json --dry-run
    python manage.py full_catalog_import --file data.json
"""

import json
import os
import shutil
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models.signals import post_delete, post_save

from apps.catalog.models import (
    Brand,
    BrandCategory,
    Category,
    CategoryLogoGroup,
    LogoGroupSeries,
    Product,
    ProductMedia,
    ProductNode,
    Series,
    SpecKey,
    SpecTemplate,
    TaxonomyNode,
    Variant,
)
from apps.catalog.signals import (
    invalidate_category_cache,
    invalidate_product_cache,
    invalidate_series_cache,
    invalidate_spec_keys_cache,
    invalidate_taxonomy_cache,
)
from apps.common.slugify_tr import slugify_tr

# Brand slug mapping (JSON value -> DB value)
BRAND_SLUG_MAP = {
    "gtech": "gastrotech",
}


@contextmanager
def disabled_signals():
    """Temporarily disconnect catalog cache signals to avoid Redis timeouts."""
    receivers = [
        (post_save, "catalog.Category", invalidate_category_cache),
        (post_delete, "catalog.Category", invalidate_category_cache),
        (post_save, "catalog.Series", invalidate_series_cache),
        (post_delete, "catalog.Series", invalidate_series_cache),
        (post_save, "catalog.TaxonomyNode", invalidate_taxonomy_cache),
        (post_delete, "catalog.TaxonomyNode", invalidate_taxonomy_cache),
        (post_save, "catalog.SpecKey", invalidate_spec_keys_cache),
        (post_delete, "catalog.SpecKey", invalidate_spec_keys_cache),
        (post_save, "catalog.Product", invalidate_product_cache),
        (post_delete, "catalog.Product", invalidate_product_cache),
    ]
    for signal, sender, receiver in receivers:
        signal.disconnect(receiver, sender=sender)
    try:
        yield
    finally:
        for signal, sender, receiver in receivers:
            signal.connect(receiver, sender=sender)


class Command(BaseCommand):
    help = "Reset all product data and import from a flat JSON product list."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file", type=str, required=True, help="Path to the JSON file."
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate without saving changes.",
        )
        parser.add_argument(
            "--no-backup",
            action="store_true",
            help="Skip database backup.",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Skip confirmation prompts.",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        self.dry_run = options["dry_run"]
        no_backup = options["no_backup"]
        no_input = options["no_input"]

        self.line("=" * 70)
        self.line("FULL CATALOG IMPORT")
        self.line("=" * 70)

        if self.dry_run:
            self.warn("DRY RUN MODE: No changes will be saved.")

        # ── Load & validate JSON ──────────────────────────────────────
        data = self.load_json(file_path)
        errors = self.validate_json(data)

        if errors:
            self.err(f"Validation failed with {len(errors)} errors:")
            for e in errors[:20]:
                self.err(f"  - {e}")
            if len(errors) > 20:
                self.err(f"  ... and {len(errors) - 20} more.")
            raise CommandError("Fix validation errors before importing.")

        self.ok("Validation passed.")
        self.print_json_stats(data)

        # ── Confirm ───────────────────────────────────────────────────
        if not no_input and not self.dry_run:
            self.warn(
                "\nThis will DELETE all existing products, variants, series, "
                "taxonomy nodes, and related data, then import from JSON."
            )
            answer = input("Type 'yes' to continue: ")
            if answer.strip().lower() != "yes":
                self.warn("Aborted.")
                return

        # ── Backup ────────────────────────────────────────────────────
        if not no_backup and not self.dry_run:
            self.backup_database()

        # ── Pre-analyze JSON ──────────────────────────────────────────
        all_spec_slugs = self.collect_spec_slugs(data)
        all_brand_slugs = self.collect_brand_slugs(data)
        series_category_map = self.collect_series_info(data)

        # ── Execute in single transaction ─────────────────────────────
        stats = self.make_stats()

        try:
            with disabled_signals(), transaction.atomic():
                sid = transaction.savepoint()

                # Phase 2: Delete
                self.phase_delete(stats)

                # Phase 3: Ensure SpecKeys
                self.phase_ensure_spec_keys(all_spec_slugs, stats)

                # Phase 4: Ensure Brands
                self.phase_ensure_brands(all_brand_slugs, stats)

                # Phase 5: Pre-cache lookups
                categories = {c.slug: c for c in Category.objects.all()}
                brands = {b.slug: b for b in Brand.objects.all()}
                spec_keys_map = {s.slug: s for s in SpecKey.objects.all()}

                # Phase 6: Create Series
                series_map = self.phase_create_series(
                    series_category_map, categories, stats
                )

                # Phase 7: Create TaxonomyNodes
                node_map = self.phase_create_taxonomy_nodes(
                    data, series_map, stats
                )

                # Phase 8: Create Products
                product_map = self.phase_create_products(
                    data, categories, series_map, brands, node_map,
                    spec_keys_map, stats
                )

                # Phase 9: Create Variants
                self.phase_create_variants(data, product_map, stats)

                # Phase 10: Ensure BrandCategory links
                self.phase_ensure_brand_categories(data, brands, categories, stats)

                if self.dry_run:
                    transaction.savepoint_rollback(sid)
                    self.warn("\nDry run complete. All changes rolled back.")
                else:
                    transaction.savepoint_commit(sid)
                    self.ok("\nImport committed successfully.")

        except Exception as e:
            self.err(f"\nImport failed: {e}")
            if options.get("verbosity", 1) > 1:
                raise
            return

        # Phase 11: Report
        self.print_final_report(stats)

        if not self.dry_run:
            self.clear_caches()

    # ══════════════════════════════════════════════════════════════════
    # JSON Loading & Validation
    # ══════════════════════════════════════════════════════════════════

    def load_json(self, file_path: str) -> List[Dict]:
        if not os.path.exists(file_path):
            raise CommandError(f"File not found: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON: {e}")

        if not isinstance(data, list):
            raise CommandError("JSON root must be a list of products.")

        return data

    def validate_json(self, data: List[Dict]) -> List[str]:
        errors = []
        seen_slugs: Set[str] = set()
        seen_model_codes: Set[str] = set()

        for idx, item in enumerate(data):
            prefix = f"Item[{idx}]"

            # Required fields
            slug = item.get("slug")
            if not slug:
                errors.append(f"{prefix}: missing 'slug'")
                continue

            if slug in seen_slugs:
                errors.append(f"{prefix}: duplicate slug '{slug}'")
            seen_slugs.add(slug)

            if not item.get("category"):
                errors.append(f"{prefix} ({slug}): missing 'category'")

            if not item.get("brand"):
                errors.append(f"{prefix} ({slug}): missing 'brand'")

            variants = item.get("variants", [])
            if not variants:
                errors.append(f"{prefix} ({slug}): no variants")
                continue

            for vi, v in enumerate(variants):
                mc = v.get("model_code")
                if not mc:
                    errors.append(f"{prefix} ({slug}) variant[{vi}]: missing model_code")
                    continue

                if mc in seen_model_codes:
                    errors.append(
                        f"{prefix} ({slug}) variant[{vi}]: duplicate model_code '{mc}'"
                    )
                seen_model_codes.add(mc)

        # Check category references against DB
        cat_slugs = {item.get("category") for item in data if item.get("category")}
        existing_cats = set(
            Category.objects.filter(slug__in=cat_slugs).values_list("slug", flat=True)
        )
        missing_cats = cat_slugs - existing_cats
        if missing_cats:
            errors.append(
                f"Categories not found in DB: {', '.join(sorted(missing_cats))}"
            )

        return errors

    # ══════════════════════════════════════════════════════════════════
    # Pre-analysis helpers
    # ══════════════════════════════════════════════════════════════════

    def collect_spec_slugs(self, data: List[Dict]) -> Set[str]:
        slugs = set()
        for item in data:
            for v in item.get("variants", []):
                for key in v.get("specs", {}).keys():
                    slugs.add(key)
        return slugs

    def collect_brand_slugs(self, data: List[Dict]) -> Set[str]:
        slugs = set()
        for item in data:
            raw = item.get("brand", "")
            mapped = BRAND_SLUG_MAP.get(raw, raw)
            slugs.add(mapped)
        return slugs

    def collect_series_info(self, data: List[Dict]) -> Dict[str, Set[str]]:
        """Returns {series_raw_value: set_of_category_slugs}.

        Empty series values are stored per-category as ("", cat_slug) keys
        so each category gets its own default series.
        """
        info: Dict[str, Set[str]] = {}
        for item in data:
            series_raw = (item.get("series") or "").strip()
            cat_slug = item.get("category", "")
            if not series_raw:
                # Per-category default key
                key = ("", cat_slug)
            else:
                key = series_raw
            if key not in info:
                info[key] = set()
            if cat_slug:
                info[key].add(cat_slug)
        return info

    # ══════════════════════════════════════════════════════════════════
    # Phase 2: Delete
    # ══════════════════════════════════════════════════════════════════

    def phase_delete(self, stats: Dict):
        self.section("PHASE 2: DELETE EXISTING DATA")

        delete_steps = []

        # Cart items
        try:
            from apps.orders.models import CartItem
            count = CartItem.objects.count()
            if count:
                CartItem.objects.all().delete()
            delete_steps.append(("CartItem", count))
        except ImportError:
            delete_steps.append(("CartItem", "skip (model not found)"))

        # Inquiry items
        try:
            from apps.inquiries.models import InquiryItem
            count = InquiryItem.objects.count()
            if count:
                InquiryItem.objects.all().delete()
            delete_steps.append(("InquiryItem", count))
        except ImportError:
            delete_steps.append(("InquiryItem", "skip (model not found)"))

        # Catalog models in FK order
        models_to_delete = [
            ("ProductMedia", ProductMedia),
            ("ProductNode", ProductNode),
            ("Variant", Variant),
            ("Product", Product),
            ("LogoGroupSeries", LogoGroupSeries),
            ("CategoryLogoGroup", CategoryLogoGroup),
            ("TaxonomyNode", TaxonomyNode),
            ("Series", Series),
        ]

        for name, model in models_to_delete:
            count = model.objects.count()
            if count:
                model.objects.all().delete()
            delete_steps.append((name, count))

        # SpecTemplate - clear series FK (don't delete templates)
        st_count = SpecTemplate.objects.filter(
            applies_to_series__isnull=False
        ).update(applies_to_series=None)
        delete_steps.append(("SpecTemplate (series FK cleared)", st_count))

        stats["deleted"] = delete_steps
        for name, count in delete_steps:
            self.line(f"  {name}: {count}")

    # ══════════════════════════════════════════════════════════════════
    # Phase 3: Ensure SpecKeys
    # ══════════════════════════════════════════════════════════════════

    def phase_ensure_spec_keys(self, all_slugs: Set[str], stats: Dict):
        self.section("PHASE 3: ENSURE SPEC KEYS")
        existing = set(SpecKey.objects.values_list("slug", flat=True))
        missing = all_slugs - existing
        created = 0

        for slug in sorted(missing):
            label = slug.replace("_", " ").title()
            SpecKey.objects.create(
                slug=slug,
                label_tr=label,
                label_en=label,
                value_type="text",
                sort_order=0,
            )
            created += 1

        stats["spec_keys_existing"] = len(existing & all_slugs)
        stats["spec_keys_created"] = created
        self.line(f"  Existing: {len(existing & all_slugs)}, Created: {created}")

    # ══════════════════════════════════════════════════════════════════
    # Phase 4: Ensure Brands
    # ══════════════════════════════════════════════════════════════════

    def phase_ensure_brands(self, all_slugs: Set[str], stats: Dict):
        self.section("PHASE 4: ENSURE BRANDS")
        existing = set(Brand.objects.values_list("slug", flat=True))
        missing = all_slugs - existing
        created = 0

        for slug in sorted(missing):
            Brand.objects.create(
                name=slug.replace("-", " ").title(),
                slug=slug,
                is_active=True,
                order=0,
            )
            created += 1

        stats["brands_existing"] = len(existing & all_slugs)
        stats["brands_created"] = created
        self.line(f"  Existing: {len(existing & all_slugs)}, Created: {created}")

    # ══════════════════════════════════════════════════════════════════
    # Phase 6: Create Series
    # ══════════════════════════════════════════════════════════════════

    def phase_create_series(
        self,
        series_category_map: Dict,
        categories: Dict[str, Category],
        stats: Dict,
    ) -> Dict:
        """Create series. Keys can be str (named series) or tuple ("", cat_slug) for defaults."""
        self.section("PHASE 6: CREATE SERIES")
        series_map: Dict = {}
        created = 0

        for key, cat_slugs in sorted(
            series_category_map.items(), key=lambda x: str(x[0])
        ):
            # Determine if this is a per-category default (tuple key)
            if isinstance(key, tuple):
                _, cat_slug = key
                category = categories.get(cat_slug)
                if not category:
                    continue
                slug = f"{cat_slug}-genel"
                name = f"{category.name} Genel"
            else:
                raw_value = key
                cat_slug = sorted(cat_slugs)[0] if cat_slugs else None
                category = categories.get(cat_slug) if cat_slug else None
                if not category:
                    self.warn(f"  Skipping series '{raw_value}': no valid category")
                    continue
                slug = slugify_tr(raw_value)
                if not slug:
                    slug = slugify_tr(raw_value.lower().replace(" ", "-"))
                name = raw_value

            # Handle duplicate slugs within same category
            if Series.objects.filter(slug=slug, category=category).exists():
                existing = Series.objects.get(slug=slug, category=category)
                series_map[key] = existing
                continue

            series = Series.objects.create(
                category=category,
                name=name,
                slug=slug,
                description_short="",
                order=created,
                is_featured=False,
            )
            series_map[key] = series
            created += 1

        stats["series_created"] = created
        self.line(f"  Created: {created}")
        return series_map

    # ══════════════════════════════════════════════════════════════════
    # Phase 7: Create TaxonomyNodes
    # ══════════════════════════════════════════════════════════════════

    def phase_create_taxonomy_nodes(
        self,
        data: List[Dict],
        series_map: Dict[str, Series],
        stats: Dict,
    ) -> Dict[str, TaxonomyNode]:
        self.section("PHASE 7: CREATE TAXONOMY NODES")
        node_map: Dict[str, TaxonomyNode] = {}
        created = 0
        # Track (series_id, slug) to avoid duplicates
        seen: Set[tuple] = set()

        for item in data:
            pn_slug = item.get("primary_node")
            if not pn_slug:
                continue

            series = self.resolve_series(item, series_map)
            if not series:
                continue

            node_slug = slugify_tr(pn_slug)
            if not node_slug:
                continue

            key = (series.id, node_slug)
            if key in seen:
                continue
            seen.add(key)

            # Use the original value as name, cleaned up
            node_name = pn_slug.replace("-", " ").replace("_", " ")
            # Capitalize first letter of each word
            node_name = " ".join(w.capitalize() for w in node_name.split())

            node = TaxonomyNode.objects.create(
                series=series,
                parent=None,
                name=node_name,
                slug=node_slug,
                order=created,
            )
            node_map[pn_slug] = node
            created += 1

        stats["taxonomy_nodes_created"] = created
        self.line(f"  Created: {created}")
        return node_map

    # ══════════════════════════════════════════════════════════════════
    # Phase 8: Create Products
    # ══════════════════════════════════════════════════════════════════

    def phase_create_products(
        self,
        data: List[Dict],
        categories: Dict[str, Category],
        series_map: Dict[str, Series],
        brands: Dict[str, Brand],
        node_map: Dict[str, TaxonomyNode],
        spec_keys_map: Dict[str, SpecKey],
        stats: Dict,
    ) -> Dict[str, Product]:
        self.section("PHASE 8: CREATE PRODUCTS")
        product_map: Dict[str, Product] = {}
        batch: List[Product] = []

        for item in data:
            slug = item["slug"]
            cat_slug = item.get("category", "")
            brand_raw = item.get("brand", "")
            brand_slug = BRAND_SLUG_MAP.get(brand_raw, brand_raw)

            category = categories.get(cat_slug)
            series = self.resolve_series(item, series_map)
            brand = brands.get(brand_slug)
            primary_node = node_map.get(item.get("primary_node"))

            # Build spec_layout from variant spec keys
            spec_layout = self.build_spec_layout(item.get("variants", []))

            product = Product(
                name=item.get("name", slug),
                slug=slug,
                title_tr=item.get("title_tr", item.get("name", slug)),
                title_en=item.get("title_en", ""),
                status=item.get("status", "draft"),
                is_featured=item.get("is_featured", False),
                series=series,
                category=category,
                brand=brand,
                primary_node=primary_node,
                general_features=item.get("general_features", []),
                short_specs=item.get("short_specs", []),
                notes=item.get("notes", []),
                spec_layout=spec_layout,
                long_description=item.get("long_description", ""),
                seo_title=item.get("seo_title", ""),
                seo_description=item.get("seo_description", ""),
            )
            batch.append(product)

        # bulk_create in batches
        Product.objects.bulk_create(batch, batch_size=100)

        # Reload to get DB-assigned UUIDs
        for p in Product.objects.filter(
            slug__in=[b.slug for b in batch]
        ).iterator():
            product_map[p.slug] = p

        # Create ProductNode links for primary_node
        product_nodes = []
        for item in data:
            slug = item["slug"]
            pn_slug = item.get("primary_node")
            if pn_slug and pn_slug in node_map and slug in product_map:
                product_nodes.append(
                    ProductNode(
                        product=product_map[slug],
                        node=node_map[pn_slug],
                    )
                )
        if product_nodes:
            ProductNode.objects.bulk_create(
                product_nodes, batch_size=200, ignore_conflicts=True
            )

        stats["products_created"] = len(batch)
        self.line(f"  Created: {len(batch)}")
        self.line(f"  ProductNode links: {len(product_nodes)}")
        return product_map

    # ══════════════════════════════════════════════════════════════════
    # Phase 9: Create Variants
    # ══════════════════════════════════════════════════════════════════

    def phase_create_variants(
        self,
        data: List[Dict],
        product_map: Dict[str, Product],
        stats: Dict,
    ):
        self.section("PHASE 9: CREATE VARIANTS")
        batch: List[Variant] = []

        for item in data:
            product = product_map.get(item["slug"])
            if not product:
                self.warn(f"  Product not found for slug: {item['slug']}")
                continue

            for v_data in item.get("variants", []):
                model_code = v_data.get("model_code")
                if not model_code:
                    continue

                list_price = self.extract_price(v_data.get("list_price"))
                price_override = self.extract_price(v_data.get("price_override"))
                weight = self.parse_decimal(v_data.get("weight_kg"))

                variant = Variant(
                    product=product,
                    model_code=model_code,
                    name_tr=v_data.get("name_tr") or model_code,
                    name_en=v_data.get("name_en") or "",
                    sku=v_data.get("sku") or "",
                    dimensions=v_data.get("dimensions") or "",
                    weight_kg=weight,
                    list_price=list_price,
                    price_override=price_override,
                    stock_qty=v_data.get("stock_qty"),
                    specs=v_data.get("specs", {}),
                )
                batch.append(variant)

        Variant.objects.bulk_create(batch, batch_size=200)

        stats["variants_created"] = len(batch)
        self.line(f"  Created: {len(batch)}")

    # ══════════════════════════════════════════════════════════════════
    # Phase 10: Ensure BrandCategory links
    # ══════════════════════════════════════════════════════════════════

    def phase_ensure_brand_categories(
        self,
        data: List[Dict],
        brands: Dict[str, Brand],
        categories: Dict[str, Category],
        stats: Dict,
    ):
        self.section("PHASE 10: ENSURE BRAND-CATEGORY LINKS")
        links: Set[tuple] = set()

        for item in data:
            brand_raw = item.get("brand", "")
            brand_slug = BRAND_SLUG_MAP.get(brand_raw, brand_raw)
            cat_slug = item.get("category", "")

            brand = brands.get(brand_slug)
            category = categories.get(cat_slug)

            if brand and category:
                links.add((brand.id, category.id))

        batch = []
        for idx, (brand_id, cat_id) in enumerate(links):
            if not BrandCategory.objects.filter(
                brand_id=brand_id, category_id=cat_id
            ).exists():
                batch.append(
                    BrandCategory(
                        brand_id=brand_id,
                        category_id=cat_id,
                        is_active=True,
                        order=idx,
                    )
                )

        if batch:
            BrandCategory.objects.bulk_create(batch, ignore_conflicts=True)

        stats["brand_category_links"] = len(batch)
        self.line(f"  New links: {len(batch)}")

    # ══════════════════════════════════════════════════════════════════
    # Helpers
    # ══════════════════════════════════════════════════════════════════

    def resolve_series(self, item: Dict, series_map: Dict) -> Optional[Series]:
        """Resolve series for a product item, handling empty series per-category."""
        series_raw = (item.get("series") or "").strip()
        if not series_raw:
            cat_slug = item.get("category", "")
            return series_map.get(("", cat_slug))
        return series_map.get(series_raw)

    def build_spec_layout(self, variants: List[Dict]) -> List[str]:
        """Build ordered spec_layout from union of all variant spec keys."""
        keys: List[str] = []
        seen: Set[str] = set()
        for v in variants:
            for key in v.get("specs", {}).keys():
                if key not in seen:
                    keys.append(key)
                    seen.add(key)
        return keys

    def extract_price(self, value: Any) -> Optional[Decimal]:
        """Handle price as object {"amount": 827.0, "currency": "EUR"} or plain number."""
        if value is None:
            return None
        if isinstance(value, dict):
            amount = value.get("amount")
            return self.parse_decimal(amount)
        return self.parse_decimal(value)

    def parse_decimal(self, value: Any) -> Optional[Decimal]:
        if value is None:
            return None
        if isinstance(value, (float, int)):
            return Decimal(str(value))
        if isinstance(value, str) and value.strip():
            try:
                return Decimal(value.strip())
            except Exception:
                return None
        return None

    def backup_database(self):
        self.section("PHASE 1: DATABASE BACKUP")
        db_path = settings.DATABASES["default"].get("NAME", "")
        if not db_path or not os.path.exists(str(db_path)):
            self.warn("  Cannot backup: DB path not found or not SQLite.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_{timestamp}"
        shutil.copy2(str(db_path), backup_path)
        self.ok(f"  Backup created: {backup_path}")

    def clear_caches(self):
        """Clear Django caches for nav/spec data."""
        try:
            from django.core.cache import cache
            cache.clear()
            self.ok("Caches cleared.")
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════
    # Stats & Reporting
    # ══════════════════════════════════════════════════════════════════

    def make_stats(self) -> Dict[str, Any]:
        return {
            "deleted": [],
            "spec_keys_existing": 0,
            "spec_keys_created": 0,
            "brands_existing": 0,
            "brands_created": 0,
            "series_created": 0,
            "taxonomy_nodes_created": 0,
            "products_created": 0,
            "variants_created": 0,
            "brand_category_links": 0,
        }

    def print_json_stats(self, data: List[Dict]):
        cats = {item.get("category") for item in data}
        series = {item.get("series", "") for item in data}
        brands = {item.get("brand") for item in data}
        variants = sum(len(item.get("variants", [])) for item in data)

        self.line("\nJSON File Stats:")
        self.line(f"  Products:   {len(data)}")
        self.line(f"  Variants:   {variants}")
        self.line(f"  Categories: {len(cats)} (ref by slug)")
        self.line(f"  Series:     {len(series)}")
        self.line(f"  Brands:     {len(brands)}")

    def print_final_report(self, stats: Dict):
        self.line("\n" + "=" * 70)
        self.line("FINAL REPORT")
        self.line("=" * 70)

        self.line("\nDeletion:")
        for name, count in stats["deleted"]:
            self.line(f"  {name}: {count}")

        self.line(f"\nSpecKeys: {stats['spec_keys_existing']} existing, {stats['spec_keys_created']} created")
        self.line(f"Brands: {stats['brands_existing']} existing, {stats['brands_created']} created")
        self.line(f"Series created: {stats['series_created']}")
        self.line(f"TaxonomyNodes created: {stats['taxonomy_nodes_created']}")
        self.line(f"Products created: {stats['products_created']}")
        self.line(f"Variants created: {stats['variants_created']}")
        self.line(f"BrandCategory links: {stats['brand_category_links']}")

        # Verify counts
        if not self.dry_run:
            self.line("\nDB Verification:")
            self.line(f"  Product.count() = {Product.objects.count()}")
            self.line(f"  Variant.count() = {Variant.objects.count()}")
            self.line(f"  Series.count()  = {Series.objects.count()}")
            self.line(f"  TaxonomyNode.count() = {TaxonomyNode.objects.count()}")

    # ══════════════════════════════════════════════════════════════════
    # Output helpers
    # ══════════════════════════════════════════════════════════════════

    def line(self, msg: str):
        self.stdout.write(msg)

    def ok(self, msg: str):
        self.stdout.write(self.style.SUCCESS(msg))

    def warn(self, msg: str):
        self.stdout.write(self.style.WARNING(msg))

    def err(self, msg: str):
        self.stderr.write(self.style.ERROR(msg))

    def section(self, title: str):
        self.line(f"\n{'─' * 50}")
        self.line(title)
        self.line("─" * 50)
