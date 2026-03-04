"""
Bulk upload product images from filesystem directories.

Matches image filenames to Variant.model_code (case-insensitive).
Handles _2, _3 suffixes as additional images for the same variant.
First image (no suffix) becomes primary.

Usage:
    python manage.py bulk_upload_images --dry-run
    python manage.py bulk_upload_images
    python manage.py bulk_upload_images --limit 50
"""
import hashlib
import os
import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Media, Product, ProductMedia, Variant


# Directories to scan
IMAGE_DIRS = [
    Path(r"D:\mutaş fotolar (1)"),
    Path(r"D:\Fotolar\Fotolar"),
]

# Files/names to skip (not product images)
SKIP_NAMES = {
    "fiyat listesi", "list", "list 1", "list 2", "liste", "bicaklar",
    "monoblok soğutma cihazı", "hava perdeli̇ si̇stem", "çıkarılabilir üst döküm",
    "opsiyonel köşe kurutma", "elektrikli erişte makarna", "erişte - makarna makinesi",
}

# Content type mapping
CONTENT_TYPE_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


def normalize(s):
    """Normalize string: remove spaces, hyphens, underscores; uppercase."""
    return re.sub(r"[\s\-_./()]", "", s).upper()


def extract_model_code_and_order(filename):
    """
    Extract model code and sort order from filename.

    Examples:
        gko7010.png     -> ('GKO7010', 0)    # primary
        gko7010_2.png   -> ('GKO7010', 1)    # second image
        gko7010_3.png   -> ('GKO7010', 2)    # third image
        iko7010t.png    -> ('IKO7010T', 0)   # variant suffix (not _N)
        GKO7010.png     -> ('GKO7010', 0)
        MAESTRO061G-TOUCH.png -> ('MAESTRO061G-TOUCH', 0)
    """
    stem = Path(filename).stem

    # Check for _N suffix (where N is a digit) indicating additional image
    match = re.match(r"^(.+?)_(\d+)$", stem)
    if match:
        base = match.group(1)
        order = int(match.group(2)) - 1  # _2 becomes order 1
        return base.upper(), order

    return stem.upper(), 0


class Command(BaseCommand):
    help = "Bulk upload product images by matching filenames to variant model codes"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
        parser.add_argument("--limit", type=int, default=None, help="Limit uploads (for testing)")
        parser.add_argument("--force", action="store_true", help="Re-upload even if variant already has images")

    def handle(self, *args, **options):
        try:
            from PIL import Image as PILImage
        except ImportError:
            self.stderr.write(self.style.ERROR("Pillow required: pip install pillow"))
            return

        dry_run = options["dry_run"]
        limit = options["limit"]
        force = options["force"]

        if dry_run:
            self.stdout.write(self.style.WARNING("=== DRY RUN MODE ===\n"))

        # Step 1: Build variant lookup maps
        self.stdout.write("Building variant lookup maps...")
        variant_by_code = {}        # exact: 'GKO7010' -> Variant
        variant_by_normalized = {}  # normalized: 'GKO7010' -> Variant

        for v in Variant.objects.select_related("product").all():
            variant_by_code[v.model_code.upper()] = v
            variant_by_normalized[normalize(v.model_code)] = v

        self.stdout.write(f"  {len(variant_by_code)} variants loaded")

        # Step 2: Get existing checksums to avoid duplicate media
        existing_checksums = set(
            Media.objects.filter(kind="image").values_list("checksum_sha256", flat=True)
        )
        self.stdout.write(f"  {len(existing_checksums)} existing image checksums")

        # Step 3: Get products that already have images
        products_with_images = set(
            ProductMedia.objects.values_list("product_id", flat=True).distinct()
        )
        self.stdout.write(f"  {len(products_with_images)} products already have images")

        # Step 4: Scan all image files from both directories
        self.stdout.write("\nScanning image directories...")
        image_files = []
        for src_dir in IMAGE_DIRS:
            if not src_dir.exists():
                self.stdout.write(self.style.WARNING(f"  Directory not found: {src_dir}"))
                continue
            count = 0
            for root, dirs, files in os.walk(src_dir):
                for f in sorted(files):
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")):
                        image_files.append({
                            "path": os.path.join(root, f),
                            "filename": f,
                            "folder": os.path.basename(root),
                            "source": str(src_dir),
                        })
                        count += 1
            self.stdout.write(f"  {src_dir.name}: {count} images found")

        self.stdout.write(f"  Total: {len(image_files)} image files\n")

        # Step 5: Match and upload
        stats = {
            "matched": 0,
            "uploaded": 0,
            "skipped_existing": 0,
            "skipped_no_match": 0,
            "skipped_skip_name": 0,
            "skipped_checksum_dup": 0,
            "skipped_numeric": 0,
            "errors": 0,
            "match_exact": 0,
            "match_normalized": 0,
            "match_multi": 0,
        }
        unmatched = []
        uploaded_count = 0

        # Group files by model code for proper ordering
        model_code_files = {}  # model_code -> [(order, file_info), ...]

        for img in image_files:
            name_no_ext = Path(img["filename"]).stem

            # Skip known non-product files
            if name_no_ext.lower() in SKIP_NAMES:
                stats["skipped_skip_name"] += 1
                continue

            # Skip pure numeric filenames (page numbers like 1.png, 2.png)
            if name_no_ext.isdigit() and len(name_no_ext) <= 2:
                stats["skipped_numeric"] += 1
                continue

            code_upper, order = extract_model_code_and_order(img["filename"])

            # Try matching
            variant = None
            method = None

            # Strategy 1: Exact match
            if code_upper in variant_by_code:
                variant = variant_by_code[code_upper]
                method = "exact"

            # Strategy 2: Normalized match
            if not variant:
                norm = normalize(code_upper)
                if norm in variant_by_normalized:
                    variant = variant_by_normalized[norm]
                    method = "normalized"

            # Strategy 3: Multi-variant filename (e.g. "TNS-622D&TNS-634D")
            if not variant and ("&" in name_no_ext or "," in name_no_ext):
                parts = re.split(r"[&,]", name_no_ext)
                for part in parts:
                    part = part.strip()
                    part_upper = part.upper()
                    if part_upper in variant_by_code:
                        variant = variant_by_code[part_upper]
                        method = "multi"
                        break
                    norm_part = normalize(part)
                    if norm_part in variant_by_normalized:
                        variant = variant_by_normalized[norm_part]
                        method = "multi"
                        break

            if not variant:
                stats["skipped_no_match"] += 1
                unmatched.append(f"{img['folder']}/{img['filename']}")
                continue

            stats["matched"] += 1
            stats[f"match_{method}"] += 1

            product = variant.product

            # Skip if product already has images and --force not set
            if not force and product.id in products_with_images:
                stats["skipped_existing"] += 1
                continue

            # Group by (product_id, variant_id) for proper ordering
            key = (product.id, variant.id)
            if key not in model_code_files:
                model_code_files[key] = []
            model_code_files[key].append((order, img, variant, product))

        # Now process grouped files
        for key, files in model_code_files.items():
            if limit and uploaded_count >= limit:
                break

            # Sort by order (primary first)
            files.sort(key=lambda x: x[0])

            # Check if this product already has any images
            product = files[0][3]
            existing_count = ProductMedia.objects.filter(product=product).count()

            for idx, (order, img, variant, product) in enumerate(files):
                if limit and uploaded_count >= limit:
                    break

                is_primary = (existing_count == 0 and idx == 0)
                sort_order = (existing_count + idx) * 10

                if dry_run:
                    primary_tag = " [PRIMARY]" if is_primary else ""
                    self.stdout.write(
                        f"  [DRY-RUN] {img['filename']} -> "
                        f"'{variant.model_code}' / '{product.name}'{primary_tag}"
                    )
                    stats["uploaded"] += 1
                    uploaded_count += 1
                    continue

                try:
                    self._upload_image(
                        product=product,
                        variant=variant,
                        image_path=Path(img["path"]),
                        sort_order=sort_order,
                        is_primary=is_primary,
                        existing_checksums=existing_checksums,
                        stats=stats,
                    )
                    uploaded_count += 1
                except Exception as e:
                    stats["errors"] += 1
                    self.stderr.write(self.style.ERROR(
                        f"  ERROR: {img['filename']}: {e}"
                    ))

        # Print report
        self._print_report(stats, unmatched, dry_run)

    def _upload_image(self, product, variant, image_path, sort_order, is_primary,
                      existing_checksums, stats):
        """Upload a single image and create ProductMedia link."""
        from PIL import Image as PILImage

        # Read content
        with open(image_path, "rb") as f:
            content = f.read()

        # Compute checksum
        checksum = hashlib.sha256(content).hexdigest()

        # Check for duplicate by checksum
        if checksum in existing_checksums:
            # Reuse existing Media object
            media = Media.objects.filter(checksum_sha256=checksum).first()
            if media:
                # Still create the ProductMedia link if it doesn't exist
                if ProductMedia.objects.filter(product=product, media=media).exists():
                    stats["skipped_checksum_dup"] += 1
                    return
                with transaction.atomic():
                    if is_primary:
                        ProductMedia.objects.filter(
                            product=product, is_primary=True
                        ).update(is_primary=False)
                    ProductMedia.objects.create(
                        product=product,
                        media=media,
                        variant=variant,
                        alt=f"{product.name} - {variant.model_code}",
                        sort_order=sort_order,
                        is_primary=is_primary,
                    )
                stats["uploaded"] += 1
                self.stdout.write(
                    f"  LINKED (existing media): {image_path.name} -> "
                    f"'{variant.model_code}'"
                )
                return

        # Get image dimensions
        width = None
        height = None
        try:
            with PILImage.open(image_path) as img:
                width, height = img.size
        except Exception:
            pass  # Continue without dimensions

        # Determine content type
        ext = image_path.suffix.lower()
        content_type = CONTENT_TYPE_MAP.get(ext, "image/png")

        with transaction.atomic():
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

            # Set primary flag
            if is_primary:
                ProductMedia.objects.filter(
                    product=product, is_primary=True
                ).update(is_primary=False)

            # Create ProductMedia link
            ProductMedia.objects.create(
                product=product,
                media=media,
                variant=variant,
                alt=f"{product.name} - {variant.model_code}",
                sort_order=sort_order,
                is_primary=is_primary,
            )

        existing_checksums.add(checksum)
        stats["uploaded"] += 1
        primary_tag = " [PRIMARY]" if is_primary else ""
        self.stdout.write(self.style.SUCCESS(
            f"  UPLOADED: {image_path.name} -> '{variant.model_code}'{primary_tag}"
        ))

    def _print_report(self, stats, unmatched, dry_run):
        """Print summary report."""
        self.stdout.write("\n" + "=" * 70)
        mode = "DRY RUN" if dry_run else "UPLOAD COMPLETE"
        self.stdout.write(self.style.SUCCESS(f"  {mode} - SUMMARY REPORT"))
        self.stdout.write("=" * 70)

        self.stdout.write(f"\n  Matched to variants:    {stats['matched']}")
        self.stdout.write(f"    - Exact match:        {stats['match_exact']}")
        self.stdout.write(f"    - Normalized match:   {stats['match_normalized']}")
        self.stdout.write(f"    - Multi-variant:      {stats['match_multi']}")
        self.stdout.write(f"  Uploaded/linked:        {stats['uploaded']}")
        self.stdout.write(f"  Skipped (already has):  {stats['skipped_existing']}")
        self.stdout.write(f"  Skipped (checksum dup): {stats['skipped_checksum_dup']}")
        self.stdout.write(f"  Skipped (skip name):    {stats['skipped_skip_name']}")
        self.stdout.write(f"  Skipped (numeric):      {stats['skipped_numeric']}")
        self.stdout.write(f"  No match found:         {stats['skipped_no_match']}")
        self.stdout.write(f"  Errors:                 {stats['errors']}")

        if unmatched:
            self.stdout.write(self.style.WARNING(
                f"\n  Unmatched files ({len(unmatched)}):"
            ))
            for u in unmatched[:50]:
                self.stdout.write(f"    - {u}")
            if len(unmatched) > 50:
                self.stdout.write(f"    ... and {len(unmatched) - 50} more")

        self.stdout.write("\n" + "=" * 70)
