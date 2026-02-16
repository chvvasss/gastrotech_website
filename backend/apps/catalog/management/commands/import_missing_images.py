"""
Comprehensive image import: find ALL images in Fotolar, check which are
already in DB, and import the missing ones. Also reports unmatched files.

Run:
  python manage.py import_missing_images --dry-run
  python manage.py import_missing_images
"""
import hashlib
import mimetypes
from pathlib import Path

from PIL import Image as PILImage
from django.core.management.base import BaseCommand

from apps.catalog.models import Media, Product, ProductMedia, Variant


class Command(BaseCommand):
    help = "Import missing product images from Fotolar directory"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        photos_dir = Path(r"C:\Users\emir\Desktop\Fotolar")
        image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
        skip_filenames = {"liste.png", "liste.jpg", "thumbs.db", "desktop.ini"}

        if dry_run:
            self.stdout.write(self.style.WARNING("=== DRY RUN MODE ==="))

        if not photos_dir.exists():
            self.stdout.write(self.style.ERROR(f"Directory not found: {photos_dir}"))
            return

        # Build variant lookup cache
        self.stdout.write("Building variant lookup cache...")
        variant_cache = {}  # model_code_upper -> (variant, product)
        for v in Variant.objects.select_related("product").all():
            if v.model_code:
                variant_cache[v.model_code.upper()] = (v, v.product)
        self.stdout.write(f"  Cached {len(variant_cache)} variants")

        # Build slug/name caches
        slug_cache = {}
        name_cache = {}
        for p in Product.objects.all():
            slug_cache[p.slug.upper()] = p
            name_cache[p.name.upper()] = p

        # Build existing media filename cache
        existing_filenames = set(
            Media.objects.values_list("filename", flat=True)
        )
        self.stdout.write(f"  Existing media records: {len(existing_filenames)}")

        # Build existing checksum cache
        existing_checksums = set(
            Media.objects.values_list("checksum_sha256", flat=True)
        )

        # Build existing ProductMedia links: (product_id, media_id)
        existing_links = set(
            ProductMedia.objects.values_list("product_id", "media_id")
        )

        # Scan all images
        self.stdout.write("\nScanning image files...")
        all_images = []
        for folder in sorted(photos_dir.iterdir()):
            if not folder.is_dir():
                continue
            for img_file in sorted(folder.iterdir()):
                if not img_file.is_file():
                    continue
                if img_file.suffix.lower() not in image_extensions:
                    continue
                if img_file.name.lower() in skip_filenames:
                    continue
                all_images.append(img_file)

        self.stdout.write(f"  Total image files found: {len(all_images)}")

        # Categorize
        already_imported = []
        to_import = []
        unmatched = []

        for img_file in all_images:
            filename_stem = img_file.stem
            folder_name = img_file.parent.name

            # Find product match
            product, variant, method = self._find_product(
                filename_stem, folder_name, variant_cache, slug_cache, name_cache
            )

            if product is None:
                unmatched.append((img_file, filename_stem))
                continue

            # Check if already imported (by filename match + link)
            if img_file.name in existing_filenames:
                media_obj = Media.objects.filter(filename=img_file.name).first()
                if media_obj and (product.id, media_obj.id) in existing_links:
                    already_imported.append((img_file, product, method))
                    continue

            # Check by checksum
            file_bytes = img_file.read_bytes()
            checksum = hashlib.sha256(file_bytes).hexdigest()
            if checksum in existing_checksums:
                media_obj = Media.objects.filter(checksum_sha256=checksum).first()
                if media_obj and (product.id, media_obj.id) in existing_links:
                    already_imported.append((img_file, product, method))
                    continue

            to_import.append({
                "file": img_file,
                "product": product,
                "variant": variant,
                "method": method,
                "file_bytes": file_bytes,
                "checksum": checksum,
            })

        # Report
        self.stdout.write("\n=== SCAN RESULTS ===")
        self.stdout.write(f"Already imported: {len(already_imported)}")
        self.stdout.write(f"To import:        {len(to_import)}")
        self.stdout.write(f"Unmatched:        {len(unmatched)}")

        if to_import:
            self.stdout.write("\n--- FILES TO IMPORT (first 30) ---")
            for m in to_import[:30]:
                v_code = m["variant"].model_code if m["variant"] else "-"
                self.stdout.write(
                    f"  {m['file'].name:30s} -> {m['product'].name:40s}  "
                    f"variant={v_code}  method={m['method']}"
                )

        if unmatched:
            self.stdout.write("\n--- UNMATCHED FILES (first 30) ---")
            for path, stem in unmatched[:30]:
                self.stdout.write(f"  {stem:30s}  ({path})")

        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                "\n=== DRY RUN COMPLETE — no changes made ==="
            ))
            return

        # Import
        if not to_import:
            self.stdout.write(self.style.SUCCESS("\nNothing new to import!"))
            return

        self.stdout.write(f"\n=== IMPORTING {len(to_import)} IMAGES ===")
        created = 0
        errors = 0

        for i, m in enumerate(to_import):
            try:
                file_bytes = m["file_bytes"]
                checksum = m["checksum"]
                img_file = m["file"]
                product = m["product"]
                variant = m["variant"]

                content_type = mimetypes.guess_type(img_file.name)[0] or "image/png"
                width, height = self._get_dimensions(img_file)

                # Reuse existing media with same checksum
                media = Media.objects.filter(checksum_sha256=checksum).first()
                if not media:
                    media = Media(
                        kind=Media.Kind.IMAGE,
                        filename=img_file.name,
                        content_type=content_type,
                        bytes=file_bytes,
                        size_bytes=len(file_bytes),
                        width=width,
                        height=height,
                        checksum_sha256=checksum,
                    )
                    media.save()

                if not ProductMedia.objects.filter(
                    product=product, media=media
                ).exists():
                    max_order = (
                        ProductMedia.objects.filter(product=product)
                        .order_by("-sort_order")
                        .values_list("sort_order", flat=True)
                        .first()
                    )
                    sort_order = (max_order or 0) + 1
                    has_primary = ProductMedia.objects.filter(
                        product=product, is_primary=True
                    ).exists()

                    ProductMedia.objects.create(
                        product=product,
                        media=media,
                        variant=variant,
                        alt=product.title_tr or product.name,
                        sort_order=sort_order,
                        is_primary=not has_primary,
                    )

                created += 1
                if (i + 1) % 10 == 0:
                    self.stdout.write(f"  Imported {i + 1}/{len(to_import)}...")

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f"  ERROR {m['file'].name}: {e}")
                )

        self.stdout.write(self.style.SUCCESS("\n=== IMPORT COMPLETE ==="))
        self.stdout.write(f"Successfully imported: {created}")
        self.stdout.write(f"Errors: {errors}")

        # Final stats
        pw = Product.objects.filter(product_media__isnull=False).distinct().count()
        pwo = Product.objects.filter(product_media__isnull=True).distinct().count()
        self.stdout.write(f"\nProducts with images: {pw}")
        self.stdout.write(f"Products without images: {pwo}")

    def _find_product(self, stem, folder, variant_cache, slug_cache, name_cache):
        # 1. Exact variant match (case-insensitive)
        upper = stem.upper()
        if upper in variant_cache:
            v, p = variant_cache[upper]
            return p, v, "variant"

        # 2. PDF ref match for "0" named files
        if stem == "0":
            parts = folder.replace(".", "-").split("-")
            for part in parts:
                part = part.strip()
                if part.isdigit():
                    num = int(part)
                    for ref in [f"p{num}", f"p{part}", part]:
                        p = Product.objects.filter(pdf_ref=ref).first()
                        if p:
                            return p, None, f"pdf_ref:{ref}"

        # 3. Slug match
        if upper in slug_cache:
            return slug_cache[upper], None, "slug"

        # 4. Name match
        if upper in name_cache:
            return name_cache[upper], None, "name"

        return None, None, "no_match"

    def _get_dimensions(self, filepath):
        try:
            with PILImage.open(filepath) as img:
                return img.width, img.height
        except Exception:
            return None, None
