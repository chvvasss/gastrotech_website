"""
Upload all matched product photos to the database.
Handles: exact match, case-insensitive, prefix-stripped VBY, partial model codes,
and description-based category/series photos.
"""
import os
import re
import json
import hashlib
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.db import transaction
from apps.catalog.models import (
    Category, Series, Product, Variant, Media, ProductMedia
)


def load_matching_report():
    with open('foto_eslestirme_raporu.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def get_all_model_codes():
    """Build lookup dicts for model codes."""
    variants = Variant.objects.select_related('product').all()
    exact = {}       # model_code -> variant
    lower = {}       # model_code.lower() -> variant
    nohyphen = {}    # model_code without hyphens/spaces, lower -> variant

    for v in variants:
        exact[v.model_code] = v
        lower[v.model_code.lower()] = v
        clean = v.model_code.replace('-', '').replace(' ', '').lower()
        nohyphen[clean] = v

    return exact, lower, nohyphen


def match_code_to_variant(code, exact, lower, nohyphen):
    """Try to match extracted code to a variant."""
    if not code:
        return None

    # 1. Exact
    if code in exact:
        return exact[code]

    # 2. Case-insensitive
    if code.lower() in lower:
        return lower[code.lower()]

    # 3. Strip numeric prefix (e.g., "3-VBY1000D" -> "VBY1000D")
    m = re.match(r'^\d+-(.+)$', code)
    if m:
        stripped = m.group(1)
        if stripped in exact:
            return exact[stripped]
        if stripped.lower() in lower:
            return lower[stripped.lower()]

    # 4. No hyphens/spaces
    clean = code.replace('-', '').replace(' ', '').lower()
    if clean in nohyphen:
        return nohyphen[clean]

    # 5. Partial match - code is prefix of a model code
    for mc, v in exact.items():
        if mc.replace('-', '').replace(' ', '').lower().startswith(clean) and len(clean) >= 5:
            return v

    return None


def match_description_to_product(filename, code):
    """Try to match description-based filenames to products/series."""
    # Known patterns: "esi6010-esi6010" -> ESI6010
    m = re.match(r'^([a-z]{2,4}\d{4}[a-z]?)-\1', code or '', re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # Patterns like "efp6020-electric-fryer-efp6020"
    m = re.match(r'^([a-z]{2,4}\d{4}[a-z]?)-', code or '', re.IGNORECASE)
    if m:
        return m.group(1).upper()

    return None


def upload_photo(file_path, product, sort_order=0, is_primary=False):
    """Upload a photo file as Media and link to Product."""
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()

    content_type_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }
    content_type = content_type_map.get(ext, 'image/png')

    with open(file_path, 'rb') as f:
        file_bytes = f.read()

    checksum = hashlib.sha256(file_bytes).hexdigest()

    # Check if already uploaded (by checksum)
    existing = Media.objects.filter(checksum_sha256=checksum).first()
    if existing:
        media = existing
    else:
        media = Media.objects.create(
            kind='image',
            filename=filename,
            content_type=content_type,
            bytes=file_bytes,
            size_bytes=len(file_bytes),
            checksum_sha256=checksum,
        )

    # Link to product if not already linked
    if not ProductMedia.objects.filter(product=product, media=media).exists():
        # Get next sort order
        max_sort = ProductMedia.objects.filter(product=product).count()
        ProductMedia.objects.create(
            product=product,
            media=media,
            sort_order=max_sort,
            is_primary=is_primary and max_sort == 0,
        )
        return True
    return False


def main():
    print("=" * 60)
    print("FOTO YUKLEME ISLEMI")
    print("=" * 60)

    data = load_matching_report()
    exact, lower, nohyphen = get_all_model_codes()

    matched_items = data['matched']
    unmatched_items = data['unmatched']

    # Phase 1: Process already-matched photos
    print(f"\n1. Onceden eslestirilmis fotolar: {len(matched_items)}")

    uploaded = 0
    skipped = 0
    errors = []

    # Group by model_code to set primary correctly
    from collections import defaultdict
    by_product = defaultdict(list)

    for item in matched_items:
        code = item['model_code']
        variant = exact.get(code) or lower.get(code.lower())
        if variant:
            by_product[variant.product_id].append((item['file'], variant.product))

    for item in unmatched_items:
        code = item.get('extracted_code', '')
        variant = match_code_to_variant(code, exact, lower, nohyphen)
        if variant:
            by_product[variant.product_id].append((item['file'], variant.product))
            continue

        # Try description-based matching
        desc_code = match_description_to_product(item.get('filename', ''), code)
        if desc_code:
            variant = match_code_to_variant(desc_code, exact, lower, nohyphen)
            if variant:
                by_product[variant.product_id].append((item['file'], variant.product))

    total_to_upload = sum(len(v) for v in by_product.values())
    print(f"\n2. Toplam yuklenecek foto: {total_to_upload} ({len(by_product)} urun)")

    count = 0
    with transaction.atomic():
        for product_id, items in by_product.items():
            for i, (file_path, product) in enumerate(items):
                if not os.path.exists(file_path):
                    errors.append(f"Dosya bulunamadi: {file_path}")
                    continue
                try:
                    result = upload_photo(file_path, product, sort_order=i, is_primary=(i == 0))
                    if result:
                        uploaded += 1
                    else:
                        skipped += 1
                    count += 1
                    if count % 100 == 0:
                        print(f"  ... {count}/{total_to_upload} islendi ({uploaded} yuklendi, {skipped} atandi)")
                except Exception as e:
                    errors.append(f"{file_path}: {str(e)}")

    print(f"\n{'=' * 60}")
    print("SONUC")
    print(f"{'=' * 60}")
    print(f"Yuklenen foto: {uploaded}")
    print(f"Zaten mevcut (atlandi): {skipped}")
    print(f"Hata: {len(errors)}")
    if errors:
        print("\nHatalar:")
        for e in errors[:20]:
            print(f"  - {e}")

    # Show stats
    products_with_images = Product.objects.filter(product_media__isnull=False).distinct().count()
    products_without_images = Product.objects.filter(product_media__isnull=True).distinct().count()
    total_media = Media.objects.filter(kind='image').count()
    print(f"\nResimli urun: {products_with_images}")
    print(f"Resimsiz urun: {products_without_images}")
    print(f"Toplam media: {total_media}")


if __name__ == '__main__':
    main()
