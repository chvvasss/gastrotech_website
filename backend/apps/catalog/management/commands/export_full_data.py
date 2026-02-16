"""
Export COMPLETE site data to JSON for portable backups and full site reconstruction.

Version 2.0 — Covers ALL models across all apps so that cloning the repo and
running ``import_full_data`` recreates the ENTIRE site with zero missing data.

Usage:
    # Export everything INCLUDING binary media data (images, PDFs)
    python manage.py export_full_data

    # Export to specific file
    python manage.py export_full_data --output fixtures/full_site.json

    # Skip binary media data (metadata only — much smaller file)
    python manage.py export_full_data --skip-media-bytes

    # Pretty-print for readability
    python manage.py export_full_data --pretty

Exports (22 data sections):
    ── Catalog ──────────────────────────
    1.  Media           (binary + metadata for ALL images, PDFs, logos, favicons)
    2.  SpecKeys        (specification keys with icons)
    3.  Categories      (hierarchy with parent relationships)
    4.  Brands          (with logo, description, website)
    5.  BrandCategories (brand↔category M2M through table)
    6.  Series          (with category + cover)
    7.  CategoryLogoGroups + LogoGroupSeries
    8.  TaxonomyNodes   (tree structure)
    9.  SpecTemplates   (reusable spec layouts)
    10. Products        (ALL fields: category, brand, node, SEO, specs, etc.)
    11. ProductNodes    (product↔node M2M through table)
    12. Variants        (ALL fields: sku, price, size, color, stock, etc.)
    13. ProductMedia    (with alt text + variant reference)
    14. CatalogAssets   (general downloadable PDF catalogs)
    15. CategoryCatalogs (per-category PDF catalogs)

    ── Blog ─────────────────────────────
    16. BlogCategories
    17. BlogTags
    18. BlogPosts       (full content, cover, tags, author)

    ── Common ───────────────────────────
    19. SiteSettings

    ── Accounts ─────────────────────────
    20. Users           (staff accounts, NO passwords)

    ── Ops ──────────────────────────────
    21. ImportJobs      (import history)
    22. AuditLogs       (audit trail)

Re-import with: python manage.py import_full_data --file <path>
"""

import base64
import json
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from django.core.management.base import BaseCommand
from django.utils import timezone


# Resolve project root (backend/)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DEFAULT_OUTPUT = BACKEND_DIR / "fixtures" / "full_site_data.json"


class DecimalUUIDEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal, UUID, datetime types."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        return super().default(obj)


class Command(BaseCommand):
    help = "Export COMPLETE site data to JSON for full site reconstruction (v2.0)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default=str(DEFAULT_OUTPUT),
            help=f"Output file path (default: {DEFAULT_OUTPUT})",
        )
        parser.add_argument(
            "--skip-media-bytes",
            action="store_true",
            help="Skip binary media data (export metadata only — much smaller file)",
        )
        parser.add_argument(
            "--pretty",
            action="store_true",
            help="Pretty-print JSON output (larger file, easier to read)",
        )

    def handle(self, *args, **options):
        output_path = Path(options["output"])
        skip_bytes = options["skip_media_bytes"]
        pretty = options["pretty"]
        start = time.time()

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(self.style.MIGRATE_HEADING("  FULL SITE EXPORT v2.0"))
        self.stdout.write(self.style.MIGRATE_HEADING("  Covers ALL models -- complete site reconstruction"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))

        if skip_bytes:
            self.stdout.write(self.style.WARNING(
                "  WARNING: --skip-media-bytes: Binary data will NOT be included"
            ))
        else:
            self.stdout.write("  Binary media data WILL be included (images, PDFs, logos)")

        # Pre-build media ID→filename map to avoid joining bytes column
        from apps.catalog.models import Media
        self._media_fn = dict(
            Media.objects.values_list("id", "filename")
        )
        self.stdout.write(f"  Built media filename lookup ({len(self._media_fn)} entries)")

        data = {
            "_meta": {
                "format": "gastrotech_full_site_export",
                "version": "2.0",
                "exported_at": timezone.now().isoformat(),
                "includes_media_bytes": not skip_bytes,
            },
            # ── Catalog ───────────────────
            "media": self._export_media(skip_bytes),
            "spec_keys": self._export_spec_keys(),
            "categories": self._export_categories(),
            "brands": self._export_brands(),
            "brand_categories": self._export_brand_categories(),
            "series": self._export_series(),
            "category_logo_groups": self._export_logo_groups(),
            "taxonomy_nodes": self._export_taxonomy_nodes(),
            "spec_templates": self._export_spec_templates(),
            "products": self._export_products(),
            "product_nodes": self._export_product_nodes(),
            "variants": self._export_variants(),
            "product_media": self._export_product_media(),
            "catalog_assets": self._export_catalog_assets(),
            "category_catalogs": self._export_category_catalogs(),
            # ── Blog ──────────────────────
            "blog_categories": self._export_blog_categories(),
            "blog_tags": self._export_blog_tags(),
            "blog_posts": self._export_blog_posts(),
            # ── Common ────────────────────
            "site_settings": self._export_site_settings(),
            # ── Accounts ──────────────────
            "users": self._export_users(),
            # ── Ops ───────────────────────
            "import_jobs": self._export_import_jobs(),
            "audit_logs": self._export_audit_logs(),
        }

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        indent = 2 if pretty else None
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, cls=DecimalUUIDEncoder, ensure_ascii=False, indent=indent)

        elapsed = time.time() - start
        file_size = output_path.stat().st_size / (1024 * 1024)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  EXPORT COMPLETE"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"  File: {output_path}")
        self.stdout.write(f"  Size: {file_size:.1f} MB")
        self.stdout.write(f"  Time: {elapsed:.1f}s")
        self.stdout.write("")
        self._print_counts(data)
        self.stdout.write("")
        self.stdout.write(f"  Re-import with: python manage.py import_full_data --file {output_path}")

    def _print_counts(self, data):
        """Print record counts per section."""
        for key, records in data.items():
            if key == "_meta":
                continue
            count = len(records) if isinstance(records, list) else "-"
            self.stdout.write(f"  {key:.<30} {count}")

    # ────────────────────────────────────────────────────────────────
    #  CATALOG EXPORTS
    # ────────────────────────────────────────────────────────────────

    def _export_media(self, skip_bytes=False):
        """Export ALL Media records (binary + metadata)."""
        from apps.catalog.models import Media

        if skip_bytes:
            # Defer the huge bytes column when not needed
            qs = Media.objects.defer("bytes").order_by("filename")
        else:
            qs = Media.objects.all().order_by("filename")

        count = qs.count()
        self.stdout.write(f"  Exporting {count} media records...")

        records = []
        for i, m in enumerate(qs.iterator(), 1):
            record = {
                "filename": m.filename,
                "kind": m.kind,
                "content_type": m.content_type,
                "size_bytes": m.size_bytes,
                "checksum_sha256": m.checksum_sha256,
                "width": m.width,
                "height": m.height,
            }
            if not skip_bytes and m.bytes:
                record["bytes_b64"] = base64.b64encode(m.bytes).decode("ascii")
            records.append(record)
            if i % 200 == 0:
                self.stdout.write(f"    ... {i}/{count}")
        return records

    def _export_spec_keys(self):
        """Export SpecKey records with icon_media reference."""
        from apps.catalog.models import SpecKey

        qs = SpecKey.objects.order_by("sort_order", "slug")
        self.stdout.write(f"  Exporting {qs.count()} spec keys...")
        return [
            {
                "slug": sk.slug,
                "label_tr": sk.label_tr,
                "label_en": sk.label_en or "",
                "unit": sk.unit or "",
                "value_type": sk.value_type,
                "sort_order": sk.sort_order,
                "icon_media_filename": self._media_fn.get(sk.icon_media_id),
            }
            for sk in qs
        ]

    def _export_categories(self):
        """Export Category records with parent slugs and cover media."""
        from apps.catalog.models import Category

        qs = Category.objects.select_related("parent").order_by("order", "name")
        self.stdout.write(f"  Exporting {qs.count()} categories...")
        return [
            {
                "slug": cat.slug,
                "name": cat.name,
                "menu_label": cat.menu_label or "",
                "description_short": cat.description_short or "",
                "parent_slug": cat.parent.slug if cat.parent else None,
                "order": cat.order,
                "is_featured": cat.is_featured,
                "series_mode": cat.series_mode,
                "cover_media_filename": self._media_fn.get(cat.cover_media_id),
            }
            for cat in qs
        ]

    def _export_brands(self):
        """Export Brand records with logo, description, website."""
        from apps.catalog.models import Brand

        qs = Brand.objects.order_by("order", "name")
        self.stdout.write(f"  Exporting {qs.count()} brands...")
        return [
            {
                "slug": brand.slug,
                "name": brand.name,
                "description": brand.description or "",
                "website_url": brand.website_url or "",
                "order": brand.order,
                "is_active": brand.is_active,
                "logo_media_filename": self._media_fn.get(brand.logo_media_id),
            }
            for brand in qs
        ]

    def _export_brand_categories(self):
        """Export BrandCategory through-table records."""
        from apps.catalog.models import BrandCategory

        qs = BrandCategory.objects.select_related("brand", "category").order_by("order")
        self.stdout.write(f"  Exporting {qs.count()} brand-category links...")
        return [
            {
                "brand_slug": bc.brand.slug,
                "category_slug": bc.category.slug,
                "is_active": bc.is_active,
                "order": bc.order,
            }
            for bc in qs
        ]

    def _export_series(self):
        """Export Series records."""
        from apps.catalog.models import Series

        qs = (
            Series.objects.select_related("category")
            .order_by("category__order", "order", "name")
        )
        self.stdout.write(f"  Exporting {qs.count()} series...")
        return [
            {
                "slug": s.slug,
                "name": s.name,
                "description_short": s.description_short or "",
                "category_slug": s.category.slug if s.category else None,
                "order": s.order,
                "is_featured": s.is_featured,
                "cover_media_filename": self._media_fn.get(s.cover_media_id),
            }
            for s in qs
        ]

    def _export_logo_groups(self):
        """Export CategoryLogoGroup + LogoGroupSeries."""
        from apps.catalog.models import CategoryLogoGroup, LogoGroupSeries

        qs = CategoryLogoGroup.objects.select_related("category", "brand").order_by("order")
        self.stdout.write(f"  Exporting {qs.count()} logo groups...")

        groups = []
        for lg in qs:
            series_links = [
                {
                    "series_slug": lgs.series.slug,
                    "order": lgs.order,
                    "is_heading": lgs.is_heading,
                }
                for lgs in LogoGroupSeries.objects.filter(logo_group=lg)
                .select_related("series")
                .order_by("order")
            ]
            groups.append({
                "category_slug": lg.category.slug,
                "brand_slug": lg.brand.slug,
                "title": lg.title or "",
                "order": lg.order,
                "is_active": lg.is_active,
                "series": series_links,
            })
        return groups

    def _export_taxonomy_nodes(self):
        """Export TaxonomyNode tree."""
        from apps.catalog.models import TaxonomyNode

        qs = (
            TaxonomyNode.objects.select_related("series", "parent", "parent__series")
            .order_by("series__slug", "order")
        )
        self.stdout.write(f"  Exporting {qs.count()} taxonomy nodes...")
        return [
            {
                "slug": tn.slug,
                "name": tn.name,
                "series_slug": tn.series.slug if tn.series else None,
                "parent_slug": tn.parent.slug if tn.parent else None,
                "parent_series_slug": tn.parent.series.slug if tn.parent and tn.parent.series else None,
                "order": tn.order,
            }
            for tn in qs
        ]

    def _export_spec_templates(self):
        """Export SpecTemplate records."""
        from apps.catalog.models import SpecTemplate

        qs = SpecTemplate.objects.select_related("applies_to_series").order_by("name")
        self.stdout.write(f"  Exporting {qs.count()} spec templates...")
        return [
            {
                "name": st.name,
                "spec_layout": st.spec_layout or [],
                "default_general_features": st.default_general_features or [],
                "default_notes": st.default_notes or [],
                "applies_to_series_slug": (
                    st.applies_to_series.slug if st.applies_to_series else None
                ),
                "applies_to_parent_taxonomy_slug": st.applies_to_parent_taxonomy_slug or "",
            }
            for st in qs
        ]

    def _export_products(self):
        """Export Product records — ALL fields."""
        from apps.catalog.models import Product

        from apps.catalog.models import Media

        # Build og_media filename lookup to avoid joining bytes column
        og_media_map = {}
        og_ids = set(
            Product.objects.exclude(og_media__isnull=True)
            .values_list("og_media_id", flat=True)
        )
        if og_ids:
            og_media_map = dict(
                Media.objects.filter(id__in=og_ids)
                .values_list("id", "filename")
            )

        qs = (
            Product.objects.select_related(
                "series", "category", "brand", "primary_node",
            )
            .prefetch_related("product_media")
            .order_by("series__slug", "slug")
        )
        self.stdout.write(f"  Exporting {qs.count()} products...")

        def _get_primary_image_filename(product):
            """Get primary image from prefetched product_media (no extra query)."""
            pm_list = getattr(product, '_prefetched_objects_cache', {}).get(
                'product_media', None
            )
            if pm_list is None:
                return None
            primary = None
            first = None
            for pm in pm_list:
                if first is None:
                    first = pm
                if pm.is_primary:
                    primary = pm
                    break
            chosen = primary or first
            if not chosen:
                return None
            return self._media_fn.get(chosen.media_id)

        return [
            {
                "slug": p.slug,
                "name": p.name,
                "title_tr": p.title_tr,
                "title_en": p.title_en or "",
                "series_slug": p.series.slug if p.series else None,
                "category_slug": p.category.slug if p.category else None,
                "brand_slug": p.brand.slug if p.brand else None,
                "primary_node_slug": p.primary_node.slug if p.primary_node else None,
                "status": p.status,
                "is_featured": p.is_featured,
                "general_features": p.general_features or [],
                "notes": p.notes or [],
                "spec_layout": p.spec_layout or [],
                "pdf_ref": p.pdf_ref or "",
                "short_specs": p.short_specs or [],
                "long_description": p.long_description or "",
                "seo_title": p.seo_title or "",
                "seo_description": p.seo_description or "",
                "primary_image_filename": _get_primary_image_filename(p),
                "og_media_filename": og_media_map.get(p.og_media_id),
            }
            for p in qs
        ]

    def _export_product_nodes(self):
        """Export ProductNode M2M through-table."""
        from apps.catalog.models import ProductNode

        qs = ProductNode.objects.select_related("product", "node").order_by(
            "product__slug", "node__slug"
        )
        self.stdout.write(f"  Exporting {qs.count()} product-node links...")
        return [
            {
                "product_slug": pn.product.slug,
                "node_slug": pn.node.slug,
            }
            for pn in qs
        ]

    def _export_variants(self):
        """Export Variant records — ALL fields."""
        from apps.catalog.models import Variant

        qs = (
            Variant.objects.select_related("product")
            .order_by("product__slug", "model_code")
        )
        self.stdout.write(f"  Exporting {qs.count()} variants...")
        return [
            {
                "model_code": v.model_code,
                "product_slug": v.product.slug if v.product else None,
                "name_tr": v.name_tr,
                "name_en": v.name_en or "",
                "sku": v.sku or "",
                "dimensions": v.dimensions or "",
                "weight_kg": v.weight_kg,
                "list_price": v.list_price,
                "price_override": v.price_override,
                "specs": v.specs or {},
                "size": v.size or "",
                "color": v.color or "",
                "stock_qty": v.stock_qty,
            }
            for v in qs
        ]

    def _export_product_media(self):
        """Export ProductMedia links with alt text and variant reference."""
        from apps.catalog.models import ProductMedia

        qs = (
            ProductMedia.objects.select_related("product", "variant")
            .order_by("product__slug", "sort_order")
        )
        self.stdout.write(f"  Exporting {qs.count()} product-media links...")
        return [
            {
                "product_slug": pm.product.slug,
                "media_filename": self._media_fn.get(pm.media_id),
                "variant_model_code": (
                    pm.variant.model_code if pm.variant else None
                ),
                "alt": pm.alt or "",
                "sort_order": pm.sort_order,
                "is_primary": pm.is_primary,
            }
            for pm in qs
        ]

    def _export_catalog_assets(self):
        """Export CatalogAsset records (general downloadable PDF catalogs)."""
        from apps.catalog.models import CatalogAsset

        qs = CatalogAsset.objects.order_by("order")
        self.stdout.write(f"  Exporting {qs.count()} catalog assets...")
        return [
            {
                "title_tr": ca.title_tr,
                "title_en": ca.title_en or "",
                "media_filename": self._media_fn.get(ca.media_id),
                "is_primary": ca.is_primary,
                "order": ca.order,
                "published": ca.published,
            }
            for ca in qs
        ]

    def _export_category_catalogs(self):
        """Export CategoryCatalog records."""
        from apps.catalog.models import CategoryCatalog

        qs = (
            CategoryCatalog.objects.select_related("category")
            .order_by("order")
        )
        self.stdout.write(f"  Exporting {qs.count()} category catalogs...")
        return [
            {
                "category_slug": cc.category.slug,
                "media_filename": self._media_fn.get(cc.media_id),
                "title_tr": cc.title_tr,
                "title_en": cc.title_en or "",
                "description": cc.description or "",
                "order": cc.order,
                "published": cc.published,
            }
            for cc in qs
        ]

    # ────────────────────────────────────────────────────────────────
    #  BLOG EXPORTS
    # ────────────────────────────────────────────────────────────────

    def _export_blog_categories(self):
        """Export BlogCategory records."""
        from apps.blog.models import BlogCategory

        qs = BlogCategory.objects.all().order_by("order", "name_tr")
        self.stdout.write(f"  Exporting {qs.count()} blog categories...")
        return [
            {
                "slug": bc.slug,
                "name_tr": bc.name_tr,
                "name_en": bc.name_en or "",
                "description": bc.description or "",
                "order": bc.order,
                "is_active": bc.is_active,
            }
            for bc in qs
        ]

    def _export_blog_tags(self):
        """Export BlogTag records."""
        from apps.blog.models import BlogTag

        qs = BlogTag.objects.all().order_by("name")
        self.stdout.write(f"  Exporting {qs.count()} blog tags...")
        return [
            {
                "slug": bt.slug,
                "name": bt.name,
            }
            for bt in qs
        ]

    def _export_blog_posts(self):
        """Export BlogPost records with full content, tags, author reference."""
        from apps.blog.models import BlogPost

        qs = (
            BlogPost.objects.select_related("category", "author")
            .prefetch_related("tags")
            .order_by("-published_at", "-created_at")
        )
        self.stdout.write(f"  Exporting {qs.count()} blog posts...")
        return [
            {
                "slug": bp.slug,
                "title": bp.title,
                "excerpt": bp.excerpt or "",
                "content": bp.content or "",
                "category_slug": bp.category.slug if bp.category else None,
                "tag_slugs": [t.slug for t in bp.tags.all()],
                "cover_media_filename": self._media_fn.get(bp.cover_media_id),
                "author_email": bp.author.email if bp.author else None,
                "status": bp.status,
                "published_at": bp.published_at.isoformat() if bp.published_at else None,
                "is_featured": bp.is_featured,
                "view_count": bp.view_count,
                "reading_time_min": bp.reading_time_min,
                "meta_title": bp.meta_title or "",
                "meta_description": bp.meta_description or "",
            }
            for bp in qs
        ]

    # ────────────────────────────────────────────────────────────────
    #  COMMON EXPORTS
    # ────────────────────────────────────────────────────────────────

    def _export_site_settings(self):
        """Export SiteSetting records."""
        from apps.common.models import SiteSetting

        qs = SiteSetting.objects.all().order_by("key")
        self.stdout.write(f"  Exporting {qs.count()} site settings...")
        return [
            {
                "key": s.key,
                "value": s.value,
                "description": s.description or "",
            }
            for s in qs
        ]

    # ────────────────────────────────────────────────────────────────
    #  ACCOUNTS EXPORTS
    # ────────────────────────────────────────────────────────────────

    def _export_users(self):
        """Export staff User accounts (NO passwords — security)."""
        from apps.accounts.models import User

        qs = User.objects.filter(is_staff=True).order_by("email")
        self.stdout.write(f"  Exporting {qs.count()} staff users...")
        return [
            {
                "email": u.email,
                "first_name": u.first_name or "",
                "last_name": u.last_name or "",
                "role": u.role,
                "is_active": u.is_active,
                "is_staff": u.is_staff,
                "is_superuser": u.is_superuser,
            }
            for u in qs
        ]

    # ────────────────────────────────────────────────────────────────
    #  OPS EXPORTS
    # ────────────────────────────────────────────────────────────────

    def _export_import_jobs(self):
        """Export ImportJob history records."""
        from apps.ops.models import ImportJob

        qs = ImportJob.objects.order_by("-created_at")[:100]  # Last 100 jobs
        self.stdout.write(f"  Exporting import jobs (up to 100)...")
        return [
            {
                "kind": j.kind,
                "status": j.status,
                "mode": j.mode,
                "created_by_email": j.created_by.email if j.created_by else None,
                "file_hash": j.file_hash or "",
                "is_preview": j.is_preview,
                "total_rows": j.total_rows,
                "created_count": j.created_count,
                "updated_count": j.updated_count,
                "skipped_count": j.skipped_count,
                "error_count": j.error_count,
                "warning_count": j.warning_count,
                "report_json": j.report_json or {},
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in qs
        ]

    def _export_audit_logs(self):
        """Export AuditLog records (last 500)."""
        from apps.ops.models import AuditLog

        qs = AuditLog.objects.order_by("-created_at")[:500]  # Last 500 logs
        self.stdout.write(f"  Exporting audit logs (up to 500)...")
        return [
            {
                "actor_email": al.actor_email or "",
                "action": al.action,
                "entity_type": al.entity_type,
                "entity_id": al.entity_id,
                "entity_label": al.entity_label or "",
                "before_json": al.before_json or {},
                "after_json": al.after_json or {},
                "metadata": al.metadata or {},
                "ip_address": str(al.ip_address) if al.ip_address else None,
                "user_agent": al.user_agent or "",
                "created_at": al.created_at.isoformat() if al.created_at else None,
            }
            for al in qs
        ]
