"""
Enhanced image import with fuzzy matching strategies.

Matching strategies (in order):
1. Exact variant model_code match (case-insensitive)
2. Variant starts-with match (e.g., "SOLE green" starts with variant "SOLE")
3. Product name starts-with match
4. PDF ref match for numeric filenames
5. Folder-level: assign numeric files (0,1,2,3...) to products already
   matched in the same folder

Run:
  python manage.py import_enhanced --dry-run
  python manage.py import_enhanced
"""
import hashlib
import mimetypes
from collections import defaultdict
from pathlib import Path

from PIL import Image as PILImage
from django.core.management.base import BaseCommand

from apps.catalog.models import Media, Product, ProductMedia, Variant


class Command(BaseCommand):
    help = "Enhanced import with fuzzy matching"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        photos_dir = Path(r"C:\Users\emir\Desktop\Fotolar")
        image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
        skip_filenames = {"liste.png", "liste.jpg", "thumbs.db", "desktop.ini"}

        if dry_run:
            self.stdout.write(self.style.WARNING("=== DRY RUN MODE ==="))

        # Build caches
        self.stdout.write("Building lookup caches...")

        # variant_code -> (variant, product)
        variant_map = {}
        for v in Variant.objects.select_related("product").all():
            if v.model_code:
                variant_map[v.model_code.upper().strip()] = (v, v.product)
        self.stdout.write(f"  Variants: {len(variant_map)}")

        # product name -> product (uppercased)
        name_map = {}
        for p in Product.objects.all():
            name_map[p.name.upper().strip()] = p

        # product slug -> product
        slug_map = {}
        for p in Product.objects.all():
            slug_map[p.slug.upper().strip()] = p

        # existing checksums
        existing_checksums = set(
            Media.objects.values_list("checksum_sha256", flat=True)
        )

        # existing links
        existing_links = set(
            ProductMedia.objects.values_list("product_id", "media_id")
        )

        # ---- PASS 1: scan all images and try exact + fuzzy matching ----
        self.stdout.write("\nPhase 1: Scanning and matching...")
        folder_data = defaultdict(list)  # folder_name -> list of (img_file, stem)

        matched = []
        unmatched_files = []
        already_imported = []

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

                stem = img_file.stem
                stem_upper = stem.upper().strip()
                folder_name = folder.name

                product, variant, method = self._match(
                    stem, stem_upper, folder_name, variant_map, name_map, slug_map
                )

                folder_data[folder_name].append({
                    "file": img_file,
                    "stem": stem,
                    "stem_upper": stem_upper,
                    "product": product,
                    "variant": variant,
                    "method": method,
                })

        # ---- PASS 2: assign unmatched numeric files to folder's product ----
        self.stdout.write("Phase 2: Folder-level numeric file assignment...")
        for folder_name, items in folder_data.items():
            # Find products matched in this folder
            folder_products = {}
            for item in items:
                if item["product"]:
                    pid = item["product"].id
                    if pid not in folder_products:
                        folder_products[pid] = item["product"]

            # If exactly 1 product in folder, assign numerics to it
            if len(folder_products) == 1:
                the_product = list(folder_products.values())[0]
                for item in items:
                    if item["product"] is None and (
                        item["stem"].isdigit() or item["stem_upper"] in ("0",)
                    ):
                        item["product"] = the_product
                        item["method"] = "folder_numeric"
            elif len(folder_products) > 1:
                # Multiple products: still assign numerics if they seem like
                # additional shots (just use first product in folder)
                for item in items:
                    if item["product"] is None and item["stem"].isdigit():
                        item["product"] = list(folder_products.values())[0]
                        item["method"] = "folder_numeric_multi"

        # Now categorize all
        for folder_name, items in folder_data.items():
            for item in items:
                if item["product"] is None:
                    unmatched_files.append(item)
                    continue

                # Check if already imported
                img_file = item["file"]
                file_bytes = img_file.read_bytes()
                checksum = hashlib.sha256(file_bytes).hexdigest()

                if checksum in existing_checksums:
                    media_obj = Media.objects.filter(checksum_sha256=checksum).first()
                    if media_obj and (item["product"].id, media_obj.id) in existing_links:
                        already_imported.append(item)
                        continue

                item["file_bytes"] = file_bytes
                item["checksum"] = checksum
                matched.append(item)

        # Report
        self.stdout.write("\n=== SCAN RESULTS ===")
        self.stdout.write(f"Already imported:  {len(already_imported)}")
        self.stdout.write(f"New to import:     {len(matched)}")
        self.stdout.write(f"Still unmatched:   {len(unmatched_files)}")

        # Group by method
        method_counts = defaultdict(int)
        for m in matched:
            method_counts[m["method"]] += 1
        self.stdout.write("\n--- Matched by method ---")
        for method, count in sorted(method_counts.items()):
            self.stdout.write(f"  {method}: {count}")

        if matched:
            self.stdout.write("\n--- NEW FILES TO IMPORT (first 30) ---")
            for m in matched[:30]:
                v_code = m["variant"].model_code if m["variant"] else "-"
                self.stdout.write(
                    f"  {m['file'].name:40s} -> {m['product'].name:40s}  method={m['method']}"
                )

        if unmatched_files:
            self.stdout.write(f"\n--- STILL UNMATCHED ({len(unmatched_files)} files, first 30) ---")
            for item in unmatched_files[:30]:
                self.stdout.write(f"  {item['stem']:40s}  ({item['file']})")

        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                "\n=== DRY RUN COMPLETE — no changes made ==="
            ))
            return

        if not matched:
            self.stdout.write(self.style.SUCCESS("\nNothing new to import!"))
            return

        # Import
        self.stdout.write(f"\n=== IMPORTING {len(matched)} IMAGES ===")
        created = 0
        errors = 0

        for i, m in enumerate(matched):
            try:
                file_bytes = m["file_bytes"]
                checksum = m["checksum"]
                img_file = m["file"]
                product = m["product"]
                variant = m.get("variant")

                content_type = mimetypes.guess_type(img_file.name)[0] or "image/png"
                width, height = self._dims(img_file)

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
                    self.stdout.write(f"  Imported {i + 1}/{len(matched)}...")

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"  ERROR {m['file'].name}: {e}"))

        self.stdout.write(self.style.SUCCESS("\n=== IMPORT COMPLETE ==="))
        self.stdout.write(f"Successfully imported: {created}")
        self.stdout.write(f"Errors: {errors}")

        pw = Product.objects.filter(product_media__isnull=False).distinct().count()
        pwo = Product.objects.filter(product_media__isnull=True).distinct().count()
        self.stdout.write(f"\nProducts with images: {pw}")
        self.stdout.write(f"Products without images: {pwo}")

    def _match(self, stem, stem_upper, folder_name, variant_map, name_map, slug_map):
        """Try to match an image file to a product."""

        # 1. Exact variant match
        if stem_upper in variant_map:
            v, p = variant_map[stem_upper]
            return p, v, "variant_exact"

        # 2. Startswith variant match (e.g., "SOLE green" -> "SOLE")
        # Try longest match first
        best_match = None
        best_len = 0
        for code, (v, p) in variant_map.items():
            if stem_upper.startswith(code) and len(code) > best_len:
                # Make sure remainder is a space or special char (not another code char)
                remainder = stem_upper[len(code):]
                if not remainder or remainder[0] in (" ", "-", "_", "(", "&"):
                    best_match = (p, v, "variant_startswith")
                    best_len = len(code)
        if best_match:
            return best_match

        # 3. Combined filename with & (e.g., "EF708&EF708-S") -> take first part
        if "&" in stem_upper:
            parts = stem_upper.split("&")
            first = parts[0].strip()
            if first in variant_map:
                v, p = variant_map[first]
                return p, v, "variant_ampersand"

        # 4. PDF ref match for "0" named files
        if stem == "0":
            parts = folder_name.replace(".", "-").split("-")
            for part in parts:
                part = part.strip()
                if part.isdigit():
                    num = int(part)
                    for ref in [f"p{num}", f"p{part}", part]:
                        p = Product.objects.filter(pdf_ref=ref).first()
                        if p:
                            return p, None, f"pdf_ref:{ref}"

        # 5. Product name exact match
        if stem_upper in name_map:
            return name_map[stem_upper], None, "name_exact"

        # 6. Product name startswith (e.g., "PUQ PRESS PRO" starts with product name)
        best_match = None
        best_len = 0
        for name, p in name_map.items():
            if stem_upper.startswith(name) and len(name) > best_len:
                remainder = stem_upper[len(name):]
                if not remainder or remainder[0] in (" ", "-", "_", "("):
                    best_match = (p, None, "name_startswith")
                    best_len = len(name)
        if best_match:
            return best_match

        # 7. Slug match
        if stem_upper in slug_map:
            return slug_map[stem_upper], None, "slug_exact"

        return None, None, "no_match"

    def _dims(self, filepath):
        try:
            with PILImage.open(filepath) as img:
                return img.width, img.height
        except Exception:
            return None, None
