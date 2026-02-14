"""
Full database setup from fixtures.

Usage (on a fresh clone):
    python manage.py migrate
    python manage.py setup_db

This will:
    1. Load categories from catalog_metadata.json
    2. Import catalog PDFs from fixtures/catalog_pdfs/ into Media table
    3. Link CategoryCatalog entries to their categories and media
    4. Create the dev admin user

If --skip-pdfs is passed, PDF import is skipped (useful for quick setup).
"""

import hashlib
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.catalog.models import Category, CategoryCatalog, Media


FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "fixtures"


class Command(BaseCommand):
    help = "Set up database from fixtures (categories, catalog PDFs, admin user)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-pdfs",
            action="store_true",
            help="Skip importing catalog PDFs (faster setup)",
        )

    def handle(self, *args, **options):
        metadata_path = FIXTURES_DIR / "catalog_metadata.json"
        if not metadata_path.exists():
            self.stderr.write(self.style.ERROR(
                f"Fixture not found: {metadata_path}\n"
                "Make sure you cloned the repo correctly."
            ))
            return

        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # --- 1. Categories ---
        self.stdout.write(self.style.MIGRATE_HEADING("Creating categories..."))
        cat_map = {}
        for cat_data in data["categories"]:
            cat, created = Category.objects.update_or_create(
                slug=cat_data["slug"],
                defaults={
                    "name": cat_data.get("name", cat_data["slug"].replace("-", " ").title()),
                    "menu_label": cat_data.get("menu_label", ""),
                    "description_short": cat_data.get("description_short", ""),
                    "order": cat_data.get("order", 0),
                    "is_featured": cat_data.get("is_featured", True),
                    "series_mode": cat_data.get("series_mode", "disabled"),
                },
            )
            cat_map[cat.slug] = cat
            status = "created" if created else "exists"
            self.stdout.write(f"  {cat.slug} ({status})")

        # Set parent relationships
        for cat_data in data["categories"]:
            parent_slug = cat_data.get("parent_slug")
            if parent_slug and parent_slug in cat_map:
                cat = cat_map[cat_data["slug"]]
                cat.parent = cat_map[parent_slug]
                cat.save(update_fields=["parent"])

        self.stdout.write(self.style.SUCCESS(f"  -> {len(cat_map)} categories ready"))

        # --- 2. Catalog PDFs ---
        if options["skip_pdfs"]:
            self.stdout.write(self.style.WARNING("Skipping PDF import (--skip-pdfs)"))
        else:
            self.stdout.write(self.style.MIGRATE_HEADING("Importing catalog PDFs..."))
            pdfs_dir = FIXTURES_DIR / "catalog_pdfs"

            if not pdfs_dir.exists():
                self.stderr.write(self.style.WARNING(
                    f"PDF directory not found: {pdfs_dir}\n"
                    "Skipping PDF import. You can add PDFs manually via admin panel."
                ))
            else:
                media_map = {}
                pdf_files = list(pdfs_dir.glob("*.pdf"))
                for pdf_path in pdf_files:
                    pdf_bytes = pdf_path.read_bytes()
                    checksum = hashlib.sha256(pdf_bytes).hexdigest()

                    media, created = Media.objects.update_or_create(
                        filename=pdf_path.name,
                        defaults={
                            "kind": "document",
                            "content_type": "application/pdf",
                            "bytes": pdf_bytes,
                            "size_bytes": len(pdf_bytes),
                            "checksum_sha256": checksum,
                        },
                    )
                    media_map[pdf_path.name] = media
                    status = "imported" if created else "updated"
                    size_mb = len(pdf_bytes) / 1024 / 1024
                    self.stdout.write(f"  {pdf_path.name} ({size_mb:.1f} MB) - {status}")

                self.stdout.write(self.style.SUCCESS(f"  -> {len(pdf_files)} PDFs imported"))

                # --- 3. Link CategoryCatalogs ---
                self.stdout.write(self.style.MIGRATE_HEADING("Linking category catalogs..."))
                for cc_data in data["category_catalogs"]:
                    cat_slug = cc_data["category_slug"]
                    filename = cc_data.get("media_filename")

                    if cat_slug not in cat_map:
                        self.stderr.write(f"  SKIP: category '{cat_slug}' not found")
                        continue
                    if filename not in media_map:
                        self.stderr.write(f"  SKIP: media '{filename}' not found")
                        continue

                    cc, created = CategoryCatalog.objects.update_or_create(
                        category=cat_map[cat_slug],
                        media=media_map[filename],
                        defaults={
                            "title_tr": cc_data["title_tr"],
                            "title_en": cc_data.get("title_en", ""),
                            "description": cc_data.get("description", ""),
                            "order": cc_data.get("order", 0),
                            "published": cc_data.get("published", True),
                        },
                    )
                    status = "created" if created else "exists"
                    self.stdout.write(f"  {cc_data['title_tr']} -> {cat_slug} ({status})")

                self.stdout.write(self.style.SUCCESS("  -> Category catalogs linked"))

        # --- 4. Dev admin user ---
        self.stdout.write(self.style.MIGRATE_HEADING("Creating dev admin user..."))
        from django.core.management import call_command
        try:
            call_command("ensure_dev_admin")
        except Exception as e:
            self.stderr.write(f"  Admin user creation skipped: {e}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("Database setup complete!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"  Categories: {Category.objects.count()}")
        self.stdout.write(f"  Catalog PDFs: {Media.objects.filter(kind='document').count()}")
        self.stdout.write(f"  Category Catalogs: {CategoryCatalog.objects.count()}")
        self.stdout.write("")
        self.stdout.write("  Admin login: admin@gastrotech.com / admin123")
        self.stdout.write("")
