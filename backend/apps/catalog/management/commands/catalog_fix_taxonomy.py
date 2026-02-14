"""
Fix taxonomy issues around Firinlar and align catalog relationships.

Default mode is DRY RUN. Use --apply to persist changes.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, F, Q

from apps.catalog.models import BrandCategory, Category, Product


ROOT_CATEGORY_SLUG = "firinlar"
LEGACY_PARENT_SLUG = "pisirme-ekipmanlari"

# Known oven-related categories that should sit under Firinlar if currently under legacy parent.
OVEN_SUBCATEGORY_SLUGS = [
    "kwik-co-konveksiyonel",
    "kwik-pro-wash",
    "elektrikli-firinlar",
    "elektrikli-firin",
    "tas-tabanli-bakery",
    "tas-tabanli-bakery-firinlar",
    "pizza-firinlari",
    "pizza-firini",
    "hizli-pisirme-firinlari",
    "mikrodalgalar",
]


class Command(BaseCommand):
    help = "Fix Firinlar taxonomy and align product/category/brand relationships."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply changes (default: dry-run)",
        )
        parser.add_argument(
            "--skip-subcategory-moves",
            action="store_true",
            help="Skip moving oven subcategories under Firinlar",
        )
        parser.add_argument(
            "--skip-product-sync",
            action="store_true",
            help="Skip syncing product.category from series.category",
        )
        parser.add_argument(
            "--skip-brand-links",
            action="store_true",
            help="Skip backfilling BrandCategory links from products",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        dry_run = not apply_changes

        self.stdout.write("=" * 70)
        self.stdout.write("CATALOG TAXONOMY FIX")
        self.stdout.write("=" * 70)
        self.stdout.write(f"Mode: {'APPLY' if apply_changes else 'DRY RUN'}\n")

        legacy_parent = Category.objects.filter(slug=LEGACY_PARENT_SLUG).first()
        firinlar_candidates = list(Category.objects.filter(slug=ROOT_CATEGORY_SLUG))

        if not firinlar_candidates:
            self.stdout.write(self.style.WARNING(
                f"Category '{ROOT_CATEGORY_SLUG}' not found. Nothing to fix."
            ))
            return

        canonical_firinlar = self._pick_canonical_firinlar(firinlar_candidates)
        duplicates = [c for c in firinlar_candidates if c.id != canonical_firinlar.id]

        if duplicates:
            self.stdout.write(self.style.WARNING(
                f"Found {len(duplicates)} duplicate '{ROOT_CATEGORY_SLUG}' categories. "
                "Only the canonical one will be modified."
            ))
            for dup in duplicates:
                self.stdout.write(
                    f"  - id={dup.id} name='{dup.name}' parent='{dup.parent.slug if dup.parent else None}'"
                )

        planned = {}

        # 1) Ensure Firinlar is a root category
        if canonical_firinlar.parent_id is not None:
            planned["reparent_root"] = {
                "id": canonical_firinlar.id,
                "from": canonical_firinlar.parent.slug if canonical_firinlar.parent else None,
                "to": None,
            }

        # 2) Move oven subcategories under Firinlar if they are under legacy parent
        if not options["skip_subcategory_moves"] and legacy_parent:
            for slug in OVEN_SUBCATEGORY_SLUGS:
                category = Category.objects.filter(slug=slug).first()
                if not category or category.id == canonical_firinlar.id:
                    continue
                if category.parent_id == legacy_parent.id and category.parent_id != canonical_firinlar.id:
                    planned.setdefault("reparent_subcategories", []).append({
                        "slug": category.slug,
                        "id": category.id,
                        "from": legacy_parent.slug,
                        "to": canonical_firinlar.slug,
                    })

        # 3) Sync product.category to series.category
        if not options["skip_product_sync"]:
            mismatched_products = (
                Product.objects
                .select_related("series__category")
                .filter(series__category__isnull=False)
                .filter(Q(category__isnull=True) | ~Q(category_id=F("series__category_id")))
            )
            planned["sync_products_count"] = mismatched_products.count()

        # 4) Backfill BrandCategory links from products
        if not options["skip_brand_links"]:
            brand_pairs = (
                Product.objects
                .filter(
                    brand__isnull=False,
                    category__isnull=False,
                    status=Product.Status.ACTIVE,
                )
                .values("brand_id", "category_id")
                .distinct()
            )
            planned["brand_pair_count"] = brand_pairs.count()

        # Print planned changes
        self._print_plan(planned, canonical_firinlar, legacy_parent)

        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] No changes applied."))
            return

        # Apply changes in transaction
        with transaction.atomic():
            if planned.get("reparent_root"):
                canonical_firinlar.parent = None
                canonical_firinlar.save(update_fields=["parent", "updated_at"])

            if planned.get("reparent_subcategories"):
                for item in planned["reparent_subcategories"]:
                    Category.objects.filter(id=item["id"]).update(parent=canonical_firinlar)

            if not options["skip_product_sync"]:
                self._apply_product_sync()

            if not options["skip_brand_links"]:
                self._apply_brand_links()

        self.stdout.write(self.style.SUCCESS("\nTaxonomy fix applied successfully."))

    def _pick_canonical_firinlar(self, candidates):
        """Choose the canonical Firinlar category (prefer root)."""
        root_candidates = [c for c in candidates if c.parent_id is None]
        if root_candidates:
            return root_candidates[0]

        # Fallback: pick the one with most series/products
        annotated = (
            Category.objects
            .filter(id__in=[c.id for c in candidates])
            .annotate(
                series_count=Count("series", distinct=True),
                product_count=Count("series__products", distinct=True),
            )
            .order_by("-product_count", "-series_count", "created_at")
        )
        return annotated.first()

    def _print_plan(self, planned, firinlar, legacy_parent):
        self.stdout.write("\nPlanned changes:")
        self.stdout.write("-" * 60)

        if planned.get("reparent_root"):
            item = planned["reparent_root"]
            self.stdout.write(
                f"Reparent '{firinlar.slug}' to root (from '{item['from']}')"
            )
        else:
            self.stdout.write(f"Firinlar already root: {firinlar.slug}")

        if legacy_parent:
            if planned.get("reparent_subcategories"):
                self.stdout.write("Move oven subcategories under Firinlar:")
                for item in planned["reparent_subcategories"]:
                    self.stdout.write(
                        f"  - {item['slug']} ({item['from']} -> {item['to']})"
                    )
            else:
                self.stdout.write("No oven subcategories to move from legacy parent.")
        else:
            self.stdout.write(
                f"Legacy parent '{LEGACY_PARENT_SLUG}' not found; subcategory move skipped."
            )

        if planned.get("sync_products_count") is not None:
            self.stdout.write(
                f"Products to sync category from series: {planned['sync_products_count']}"
            )

        if planned.get("brand_pair_count") is not None:
            self.stdout.write(
                f"Brand-category pairs to ensure (active products): {planned['brand_pair_count']}"
            )

    def _apply_product_sync(self):
        """Sync product.category to series.category where mismatched."""
        products = (
            Product.objects
            .select_related("series__category")
            .filter(series__category__isnull=False)
            .filter(Q(category__isnull=True) | ~Q(category_id=F("series__category_id")))
        )

        updated = 0
        for product in products:
            if product.series and product.series.category:
                product.category = product.series.category
                product.save(update_fields=["category", "updated_at"])
                updated += 1

        self.stdout.write(f"Updated {updated} products with series.category")

    def _apply_brand_links(self):
        """Ensure BrandCategory links for active products."""
        pairs = (
            Product.objects
            .filter(
                brand__isnull=False,
                category__isnull=False,
                status=Product.Status.ACTIVE,
            )
            .values("brand_id", "category_id")
            .distinct()
        )

        created = 0
        for pair in pairs:
            _, was_created = BrandCategory.objects.get_or_create(
                brand_id=pair["brand_id"],
                category_id=pair["category_id"],
                defaults={"is_active": True, "order": 0},
            )
            if was_created:
                created += 1

        self.stdout.write(f"Created {created} BrandCategory links")
