"""
Management command to bulk upload product images from Excel file.

Usage:
    # Dry run (preview only, no changes)
    python manage.py upload_product_images --dry-run

    # Actual upload
    python manage.py upload_product_images

    # With custom paths
    python manage.py upload_product_images --excel /path/to/excel.xlsx --images /path/to/images/

    # Skip products that already have images
    python manage.py upload_product_images --skip-existing
"""

import hashlib
import os
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Media, Product, ProductMedia, Variant


class Command(BaseCommand):
    help = "Bulk upload product images from Excel file mapping code to image files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--excel",
            type=str,
            default=None,
            help="Path to Excel file (default: urunlerfotoupload/gastrotech_product_images_final3_summary.xlsx)",
        )
        parser.add_argument(
            "--images",
            type=str,
            default=None,
            help="Path to images directory (default: urunlerfotoupload/)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be uploaded without making changes",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Skip products that already have images",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of images to upload (for testing)",
        )

    def handle(self, *args, **options):
        try:
            import pandas as pd
            from PIL import Image
        except ImportError as e:
            self.stderr.write(self.style.ERROR(f"Required package missing: {e}"))
            self.stderr.write("Install with: pip install pandas openpyxl pillow")
            return

        dry_run = options["dry_run"]
        skip_existing = options["skip_existing"]
        limit = options["limit"]

        # Determine paths
        # Default: project_root/urunlerfotoupload (same level as backend, frontend, etc.)
        base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent  # backend/
        project_root = base_dir.parent  # gastrotech.com_cursor/
        images_dir = Path(options["images"]) if options["images"] else project_root / "urunlerfotoupload"
        excel_path = Path(options["excel"]) if options["excel"] else images_dir / "gastrotech_product_images_final3_summary.xlsx"

        self.stdout.write(f"Base directory: {base_dir}")
        self.stdout.write(f"Images directory: {images_dir}")
        self.stdout.write(f"Excel file: {excel_path}")

        if not excel_path.exists():
            self.stderr.write(self.style.ERROR(f"Excel file not found: {excel_path}"))
            return

        if not images_dir.exists():
            self.stderr.write(self.style.ERROR(f"Images directory not found: {images_dir}"))
            return

        # Read Excel
        self.stdout.write(f"\nReading Excel file...")
        df = pd.read_excel(excel_path)
        self.stdout.write(f"Found {len(df)} rows in Excel")
        self.stdout.write(f"Columns: {df.columns.tolist()}")

        # Statistics
        stats = {
            "total_rows": len(df),
            "unique_codes": df["code"].nunique(),
            "matched": 0,
            "not_found_code": [],
            "not_found_product": [],
            "not_found_image": [],
            "skipped_existing": 0,
            "uploaded": 0,
            "errors": [],
        }

        # Group by code to handle multiple images per product
        grouped = df.groupby("code")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n=== DRY RUN MODE - No changes will be made ===\n"))

        processed = 0

        for code, group in grouped:
            if limit and processed >= limit:
                self.stdout.write(f"\nLimit reached ({limit}), stopping...")
                break

            self.stdout.write(f"\nProcessing code: {code}")

            # Find Variant by model_code
            try:
                variant = Variant.objects.select_related("product").get(model_code=code)
                product = variant.product
                self.stdout.write(f"  Found product: {product.title_tr} (slug: {product.slug})")
                stats["matched"] += 1
            except Variant.DoesNotExist:
                # Try direct product search by name/title
                self.stdout.write(self.style.WARNING(f"  Variant not found for code: {code}"))
                stats["not_found_code"].append(code)
                continue
            except Variant.MultipleObjectsReturned:
                self.stdout.write(self.style.WARNING(f"  Multiple variants found for code: {code}"))
                variant = Variant.objects.filter(model_code=code).first()
                product = variant.product

            # Check if product already has images
            existing_count = product.product_media.count()
            if skip_existing and existing_count > 0:
                self.stdout.write(f"  Skipping - product already has {existing_count} images")
                stats["skipped_existing"] += 1
                continue

            # Process each image in the group
            is_first = existing_count == 0  # First image will be primary

            for _, row in group.iterrows():
                image_file = row["image_file"]
                image_path = images_dir / image_file

                if not image_path.exists():
                    self.stdout.write(self.style.WARNING(f"  Image not found: {image_file}"))
                    stats["not_found_image"].append(image_file)
                    continue

                self.stdout.write(f"  -> {image_file} {'(PRIMARY)' if is_first else ''}")

                if not dry_run:
                    try:
                        self._upload_image(product, image_path, is_primary=is_first)
                        stats["uploaded"] += 1
                    except Exception as e:
                        error_msg = f"Error uploading {image_file}: {str(e)}"
                        self.stderr.write(self.style.ERROR(f"  {error_msg}"))
                        stats["errors"].append({"code": code, "image": image_file, "error": str(e)})
                else:
                    stats["uploaded"] += 1  # Count as would-be-uploaded in dry run

                is_first = False  # Only first image is primary

            processed += 1

        # Print summary report
        self._print_report(stats, dry_run)

    def _upload_image(self, product: Product, image_path: Path, is_primary: bool = False):
        """Upload a single image to a product."""
        from PIL import Image as PILImage

        # Read file content
        with open(image_path, "rb") as f:
            content = f.read()

        # Get image dimensions
        with PILImage.open(image_path) as img:
            width, height = img.size

        # Determine content type
        ext = image_path.suffix.lower()
        content_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        content_type = content_type_map.get(ext, "image/png")

        # Compute checksum
        checksum = hashlib.sha256(content).hexdigest()

        # Check if media already exists (by checksum)
        existing_media = Media.objects.filter(checksum_sha256=checksum).first()

        if existing_media:
            media = existing_media
            self.stdout.write(f"    Using existing media: {media.id}")
        else:
            # Create Media object
            media = Media.objects.create(
                kind=Media.Kind.IMAGE,
                filename=image_path.name,
                content_type=content_type,
                bytes=content,
                size_bytes=len(content),
                width=width,
                height=height,
                checksum_sha256=checksum,
            )
            self.stdout.write(f"    Created media: {media.id}")

        # Check if this media is already attached to product
        existing_pm = ProductMedia.objects.filter(product=product, media=media).first()
        if existing_pm:
            self.stdout.write(f"    Media already attached to product")
            return

        # Calculate sort order
        max_order = product.product_media.order_by("-sort_order").values_list(
            "sort_order", flat=True
        ).first() or 0
        sort_order = max_order + 10

        # Handle primary flag
        with transaction.atomic():
            if is_primary:
                product.product_media.filter(is_primary=True).update(is_primary=False)

            # Create ProductMedia
            ProductMedia.objects.create(
                product=product,
                media=media,
                alt=f"{product.title_tr} - {image_path.stem}",
                sort_order=sort_order,
                is_primary=is_primary,
            )

    def _print_report(self, stats: dict, dry_run: bool):
        """Print summary report."""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("SUMMARY REPORT"))
        self.stdout.write("=" * 60)

        if dry_run:
            self.stdout.write(self.style.WARNING("MODE: DRY RUN (no actual changes made)"))
        else:
            self.stdout.write(self.style.SUCCESS("MODE: ACTUAL UPLOAD"))

        self.stdout.write(f"\nTotal rows in Excel: {stats['total_rows']}")
        self.stdout.write(f"Unique product codes: {stats['unique_codes']}")
        self.stdout.write(f"Matched products: {stats['matched']}")
        self.stdout.write(f"Images {'would be ' if dry_run else ''}uploaded: {stats['uploaded']}")

        if stats["skipped_existing"]:
            self.stdout.write(f"Skipped (already have images): {stats['skipped_existing']}")

        if stats["not_found_code"]:
            self.stdout.write(self.style.WARNING(f"\nCodes not found in database ({len(stats['not_found_code'])}):"))
            for code in stats["not_found_code"][:20]:
                self.stdout.write(f"  - {code}")
            if len(stats["not_found_code"]) > 20:
                self.stdout.write(f"  ... and {len(stats['not_found_code']) - 20} more")

        if stats["not_found_image"]:
            self.stdout.write(self.style.WARNING(f"\nImage files not found ({len(stats['not_found_image'])}):"))
            for img in stats["not_found_image"][:20]:
                self.stdout.write(f"  - {img}")
            if len(stats["not_found_image"]) > 20:
                self.stdout.write(f"  ... and {len(stats['not_found_image']) - 20} more")

        if stats["errors"]:
            self.stdout.write(self.style.ERROR(f"\nErrors ({len(stats['errors'])}):"))
            for err in stats["errors"][:10]:
                self.stdout.write(f"  - {err['code']}/{err['image']}: {err['error']}")

        self.stdout.write("\n" + "=" * 60)

        if not dry_run:
            self.stdout.write(self.style.SUCCESS("Upload complete!"))
        else:
            self.stdout.write(self.style.WARNING("Dry run complete. Run without --dry-run to perform actual upload."))
