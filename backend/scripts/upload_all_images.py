"""
Photo matching & upload script for Gastrotech products.

Scans two photo directories, matches filenames to model codes (multi-layer),
and uploads images as Media with ProductMedia links.

Photo directories:
  - D:\\mutaş fotolar (1)\\   (~696 images, Pişirme/Fırın equipment)
  - C:\\Users\\emir\\Desktop\\Fotolar\\  (~286 images, Kafeterya/Bulaşık/Çamaşır)

Usage:
    cd backend
    python scripts/upload_all_images.py
"""
import os
import sys
import re
import hashlib
from collections import defaultdict

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
# If DATABASE_URL not set, default to Docker PostgreSQL
os.environ.setdefault("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/gastrotech")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Disable Django SQL debug logging (causes MemoryError with large binary data)
import logging
logging.getLogger("django.db.backends").setLevel(logging.WARNING)

import django
django.setup()

from django.db import transaction
from apps.catalog.models import Product, Variant, Media, ProductMedia


# ── Configuration ──────────────────────────────────────────────────────────
PHOTO_DIRS = [
    r"D:\mutaş fotolar (1)",
    r"C:\Users\emir\Desktop\Fotolar",
]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

CONTENT_TYPE_MAP = {
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".webp": "image/webp",
}


def scan_all_images():
    """Recursively scan all photo directories for image files."""
    images = []
    for base_dir in PHOTO_DIRS:
        if not os.path.exists(base_dir):
            print(f"  [!] Directory not found: {base_dir}")
            continue
        for root, dirs, files in os.walk(base_dir):
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    images.append(os.path.join(root, fname))
    return images


def build_variant_lookups():
    """Build multiple lookup dicts for flexible model code matching."""
    variants = Variant.objects.select_related("product").all()

    exact = {}       # model_code -> variant
    lower = {}       # model_code.lower() -> variant
    nohyphen = {}    # model_code without hyphens/spaces/colons, lower -> variant

    for v in variants:
        mc = v.model_code
        exact[mc] = v
        lower[mc.lower()] = v
        clean = mc.replace("-", "").replace(" ", "").replace(":", "").lower()
        nohyphen[clean] = v

    return exact, lower, nohyphen


def extract_code_from_filename(filename):
    """Extract potential model code from a filename (without extension)."""
    name = os.path.splitext(filename)[0]

    # Strip _2, _3, _4 suffix (alternate angles)
    name = re.sub(r"_\d+$", "", name)

    # Strip numeric prefix: "1-VBY500DC" → "VBY500DC"
    m = re.match(r"^\d+-(.+)$", name)
    if m:
        name = m.group(1)

    return name.strip()


def match_code_to_variant(code, exact, lower, nohyphen):
    """Multi-layer model code matching. Returns (variant, match_type) or (None, None)."""
    if not code:
        return None, None

    # 1. Exact match
    if code in exact:
        return exact[code], "exact"

    # 2. Case-insensitive
    code_lower = code.lower()
    if code_lower in lower:
        return lower[code_lower], "case-insensitive"

    # 3. No hyphens/spaces/colons
    clean = code.replace("-", "").replace(" ", "").replace(":", "").lower()
    if clean in nohyphen:
        return nohyphen[clean], "no-hyphen"

    # 4. ECO variant: "gkf100eco" → try "GKF100-ECO"
    eco_match = re.match(r"^([a-z]{2,4}\d{3,5})(eco)$", code_lower)
    if eco_match:
        with_hyphen = f"{eco_match.group(1)}-ECO".upper()
        if with_hyphen in exact:
            return exact[with_hyphen], "eco-variant"
        if with_hyphen.lower() in lower:
            return lower[with_hyphen.lower()], "eco-variant"

    # 5. Color/appearance suffix: "GT-E8 BLACK" -> "GT-E8"
    color_suffixes = [
        "BLACK", "WHITE", "RED", "SS", "GREY", "GREEN",
        "CHROME", "GOLD", "SILVER", "INOX",
        "chrome", "black", "gold", "green", "grey", "white",
    ]
    for suffix in color_suffixes:
        if code.endswith(f" {suffix}"):
            base = code[:-(len(suffix) + 1)].strip()
            if base in exact:
                return exact[base], "color-stripped"
            if base.lower() in lower:
                return lower[base.lower()], "color-stripped"

    # 5b. "tartisiz" suffix for Acaia scales: "Artic White Matt tartisiz" -> skip
    #     (these are variant photos without scale, match base color name via product name)
    if "tartisiz" in code.lower() or "tart\u0131s\u0131z" in code.lower():
        base = re.sub(r"\s+tart[ıi]s[ıi]z$", "", code, flags=re.IGNORECASE).strip()
        if base.lower() in lower:
            return lower[base.lower()], "tartisiz-stripped"

    # 5c. "front" / "side" suffix: "Gtech AC-517 EC front" -> "Gtech AC-517 EC"
    for view_suffix in ["front", "side", "top", "back"]:
        if code.lower().endswith(f" {view_suffix}"):
            base = code[:-(len(view_suffix) + 1)].strip()
            if base in exact:
                return exact[base], "view-stripped"
            if base.lower() in lower:
                return lower[base.lower()], "view-stripped"

    # 6. Composite filenames: "VLRI32180G&VLRI55200G" → first code
    if "&" in code:
        parts = code.split("&")
        for part in parts:
            part = part.strip()
            if part in exact:
                return exact[part], "composite"
            if part.lower() in lower:
                return lower[part.lower()], "composite"

    # 7. Partial prefix match (min 5 chars) - model code starts with our code
    if len(clean) >= 5:
        for mc, v in exact.items():
            mc_clean = mc.replace("-", "").replace(" ", "").replace(":", "").lower()
            if mc_clean.startswith(clean):
                return v, "prefix"

    # 8. Our code starts with a model code (for variants like GO-85K -> GO-85)
    if len(clean) >= 4:
        best_match = None
        best_len = 0
        for mc, v in exact.items():
            mc_clean = mc.replace("-", "").replace(" ", "").replace(":", "").lower()
            if clean.startswith(mc_clean) and len(mc_clean) > best_len:
                best_match = v
                best_len = len(mc_clean)
        if best_match and best_len >= 4:
            return best_match, "suffix-strip"

    return None, None


def match_file_to_variants(filepath, exact, lower, nohyphen):
    """Match a file to one or more variants. Returns list of (variant, match_type)."""
    filename = os.path.basename(filepath)
    code = extract_code_from_filename(filename)

    if not code:
        return []

    # Handle composite filenames (e.g., "VLRI32180G&VLRI55200G")
    if "&" in code:
        results = []
        for part in code.split("&"):
            part = part.strip()
            v, mt = match_code_to_variant(part, exact, lower, nohyphen)
            if v:
                results.append((v, mt))
        return results

    # Single code match
    v, mt = match_code_to_variant(code, exact, lower, nohyphen)
    if v:
        return [(v, mt)]

    return []


def upload_photo(file_path, product, sort_order=0, is_primary=False):
    """Upload a photo as Media and link to Product. Returns True if new upload."""
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    content_type = CONTENT_TYPE_MAP.get(ext, "image/png")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    checksum = hashlib.sha256(file_bytes).hexdigest()

    # Deduplicate by checksum
    media = Media.objects.filter(checksum_sha256=checksum).first()
    if not media:
        media = Media.objects.create(
            kind=Media.Kind.IMAGE,
            filename=filename,
            content_type=content_type,
            bytes=file_bytes,
            size_bytes=len(file_bytes),
            checksum_sha256=checksum,
        )

    # Check if already linked
    if ProductMedia.objects.filter(product=product, media=media).exists():
        return False

    # Get next sort order
    existing_count = ProductMedia.objects.filter(product=product).count()
    ProductMedia.objects.create(
        product=product,
        media=media,
        sort_order=existing_count,
        is_primary=is_primary and existing_count == 0,
        alt=product.title_tr,
    )
    return True


def run():
    print("=" * 60)
    print("GASTROTECH PHOTO MATCHING & UPLOAD")
    print("=" * 60)

    # ── Phase 1: Scan all images ───────────────────────────────────────────
    print("\n1. Scanning photo directories...")
    all_images = scan_all_images()
    print(f"   Found {len(all_images)} image files")

    # ── Phase 2: Build lookups ─────────────────────────────────────────────
    print("\n2. Building variant lookups...")
    exact, lower, nohyphen = build_variant_lookups()
    print(f"   {len(exact)} variants in database")

    if not exact:
        print("   [!] No variants found. Run import_all_products.py first!")
        return

    # ── Phase 3: Match files to variants ───────────────────────────────────
    print("\n3. Matching files to model codes...")
    by_product = defaultdict(list)  # product_id → [(file_path, variant, match_type)]
    unmatched = []
    match_type_counts = defaultdict(int)

    for filepath in all_images:
        matches = match_file_to_variants(filepath, exact, lower, nohyphen)
        if matches:
            for variant, match_type in matches:
                by_product[variant.product_id].append((filepath, variant.product, match_type))
                match_type_counts[match_type] += 1
        else:
            unmatched.append(filepath)

    total_matched = sum(len(v) for v in by_product.values())
    print(f"   Matched: {total_matched} files -> {len(by_product)} products")
    print(f"   Unmatched: {len(unmatched)} files")
    print(f"\n   Match type breakdown:")
    for mt, count in sorted(match_type_counts.items(), key=lambda x: -x[1]):
        print(f"     {mt}: {count}")

    # ── Phase 4: Upload ────────────────────────────────────────────────────
    print(f"\n4. Uploading {total_matched} images...")
    uploaded = 0
    skipped_dup = 0
    errors = []
    count = 0

    for product_id, items in by_product.items():
        # Deduplicate: same file might appear for same product via different matches
        seen_files = set()
        unique_items = []
        for filepath, product, match_type in items:
            if filepath not in seen_files:
                seen_files.add(filepath)
                unique_items.append((filepath, product, match_type))

        for i, (filepath, product, match_type) in enumerate(unique_items):
            if not os.path.exists(filepath):
                errors.append(f"File not found: {filepath}")
                continue
            try:
                with transaction.atomic():
                    result = upload_photo(
                        filepath,
                        product,
                        sort_order=i,
                        is_primary=(i == 0),
                    )
                if result:
                    uploaded += 1
                else:
                    skipped_dup += 1
                count += 1
                if count % 50 == 0:
                    print(f"   ... {count}/{total_matched} processed ({uploaded} uploaded)")
            except Exception as e:
                errors.append(f"{os.path.basename(filepath)}: {e}")

    # ── Phase 5: Summary ───────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("UPLOAD SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total images scanned:    {len(all_images)}")
    print(f"Matched to products:     {total_matched}")
    print(f"Uploaded (new):          {uploaded}")
    print(f"Skipped (duplicate):     {skipped_dup}")
    print(f"Unmatched files:         {len(unmatched)}")
    print(f"Errors:                  {len(errors)}")

    # DB stats
    products_with_images = Product.objects.filter(
        product_media__isnull=False
    ).distinct().count()
    products_without_images = Product.objects.filter(
        product_media__isnull=True
    ).count()
    total_media = Media.objects.filter(kind="image").count()
    total_pm = ProductMedia.objects.count()

    print(f"\nDatabase stats:")
    print(f"  Products with images:    {products_with_images}")
    print(f"  Products without images: {products_without_images}")
    print(f"  Total Media objects:     {total_media}")
    print(f"  Total ProductMedia links:{total_pm}")

    if errors:
        print(f"\nFirst 15 errors:")
        for e in errors[:15]:
            print(f"  - {e}")

    if unmatched:
        print(f"\nFirst 30 unmatched files:")
        for f in sorted(unmatched)[:30]:
            fname = os.path.basename(f)
            print(f"  - {fname}")


if __name__ == "__main__":
    run()
