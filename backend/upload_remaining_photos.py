"""
Second pass: upload remaining unmatched photos with manual code corrections.
GPI -> GPT/GP1, VBY500DC -> VBY500CD, description-based -> series photos.
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

# Manual code corrections
CODE_FIXES = {
    'GPI6010S': 'GP16010S',
    'GPI7010S': 'GPT7010S',
    'GPI7010R': 'GPT7010R',
    'GPI7020S': 'GPT7020S',
    'GPI7020R': 'GPT7020R',
    'GPI7020SR': 'GPT7020SR',
    'GPI7030S': 'GPT7030S',
    'GPI7030R': 'GPT7030R',
    'GPI7030SR': 'GPT7030SR',
    'GPI9010S': 'GP19010S',
    'GPI9010R': 'GP19010R',
    'GPI9020S': 'GP19020S',
    'GPI9020R': 'GP19020R',
    'GPI9020SR': 'GP19020SR',
    'GPI9030S': 'GP19030S',
    'GPI9030R': 'GP19030R',
    'GPI9030SR': 'GP19030SR',
    'VBY500DC': 'VBY500CD',
    'VBY500D': 'VBY500C',
    'gpi7010s': 'GPT7010S',
    'gpi7010r': 'GPT7010R',
    'gpi7020s': 'GPT7020S',
    'gpi7020r': 'GPT7020R',
    'gpi7020sr': 'GPT7020SR',
    'gpi7030s': 'GPT7030S',
    'gpi7030r': 'GPT7030R',
    'gpi7030sr': 'GPT7030SR',
    'gpi9010s': 'GP19010S',
    'gpi9010r': 'GP19010R',
    'gpi9020s': 'GP19020S',
    'gpi9020r': 'GP19020R',
    'gpi9020sr': 'GP19020SR',
    'gpi9030s': 'GP19030S',
    'gpi9030r': 'GP19030R',
    'gpi9030sr': 'GP19030SR',
}

# Description-based filenames -> Series name mapping
DESCRIPTION_SERIES_MAP = {
    'elektrikli-fritozler': 'Elektrikli Fritözler',
    'elektikli-fritozler': 'Elektrikli Fritözler',
    'gazli-fritozler': 'Gazlı Fritözler',
    'elektrikli-ocaklar': 'Elektrikli Ocaklar',
    'gazli-ocaklar': 'Gazlı Ocaklar',
    'elektrikli-kuzineler': 'Elektrikli Kuzineler',
    'gazli-kuzineler': 'Gazlı Kuzineler',
    'elektrikli-benmariler': 'Elektrikli Benmariler',
    'gazli-benmariler': 'Gazlı Benmariler',
    'elektrikli-izgaralar': 'Elektrikli Izgaralar',
    'gazli-izgaralar': 'Gazlı Izgaralar',
    'elektrikli-devrilir': 'Elektrikli Devrilir Tavalar',
    'elektrikli-amerikan': 'Elektrikli Amerikan Izgaralar',
    'elektrikli-kapali': 'Elektrikli Kapalı Ocaklar',
    'gazli-kapali': 'Gazlı Kapalı Ocaklar',
    'gazli-wok': 'Gazlı Wok Ocaklar',
    'gazli-show': 'Gazlı Show Ocaklar',
    'gazli-yer': 'Gazlı Yer Ocakları',
    'elektrikli-makarna': 'Elektrikli Makarna Pişiriciler',
    'elektrikli-sulu': 'Elektrikli Sulu Izgaralar',
    'gazli-sulu': 'Gazlı Sulu Izgaralar',
    'elektrikli-patates': 'Elektrikli Patates Dinlendirme',
    'induksiyon': 'İndüksiyon Ocaklar',
    'indirekt': 'İndirekt Isıtmalı',
    'direkt': 'Direkt Isıtmalı',
    'banket': 'Banket Arabaları',
    'drop-in': 'Drop-in Serisi',
    'eko-seri': 'Eko Seri',
}


def upload_photo(file_path, product, sort_order=0, is_primary=False):
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    ct_map = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}
    content_type = ct_map.get(ext, 'image/png')

    with open(file_path, 'rb') as f:
        file_bytes = f.read()

    checksum = hashlib.sha256(file_bytes).hexdigest()
    existing = Media.objects.filter(checksum_sha256=checksum).first()
    if existing:
        media = existing
    else:
        media = Media.objects.create(
            kind='image', filename=filename,
            content_type=content_type, bytes=file_bytes,
            size_bytes=len(file_bytes),
            checksum_sha256=checksum,
        )

    if not ProductMedia.objects.filter(product=product, media=media).exists():
        max_sort = ProductMedia.objects.filter(product=product).count()
        ProductMedia.objects.create(
            product=product, media=media,
            sort_order=max_sort, is_primary=is_primary and max_sort == 0,
        )
        return True
    return False


def main():
    print("=" * 60)
    print("KALAN FOTO YUKLEME (2. ASUS)")
    print("=" * 60)

    with open('foto_eslestirme_raporu.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_codes = {v.model_code: v for v in Variant.objects.select_related('product').all()}
    all_lower = {k.lower(): v for k, v in all_codes.items()}

    uploaded = 0
    matched_count = 0
    unmatched_remaining = []

    from collections import defaultdict
    by_product = defaultdict(list)

    for u in data['unmatched']:
        code = u.get('extracted_code', '')
        file_path = u['file']

        # 1. Apply manual code fixes
        fixed = CODE_FIXES.get(code)
        if fixed and fixed in all_codes:
            by_product[all_codes[fixed].product_id].append((file_path, all_codes[fixed].product))
            matched_count += 1
            continue

        # Also try case-insensitive fix
        fixed_lower = CODE_FIXES.get(code.lower())
        if fixed_lower and fixed_lower in all_codes:
            by_product[all_codes[fixed_lower].product_id].append((file_path, all_codes[fixed_lower].product))
            matched_count += 1
            continue

        # 2. Strip prefix numbers for VBY
        m = re.match(r'^\d+-(.+)$', code)
        if m:
            stripped = m.group(1)
            fixed2 = CODE_FIXES.get(stripped)
            if fixed2 and fixed2 in all_codes:
                by_product[all_codes[fixed2].product_id].append((file_path, all_codes[fixed2].product))
                matched_count += 1
                continue
            if stripped in all_codes:
                # Already handled in first pass, skip
                continue

        # 3. Description-based: try to find a product in matching series
        for desc_key, series_name in DESCRIPTION_SERIES_MAP.items():
            if desc_key in code.lower():
                # Find series and assign to first product
                series_qs = Series.objects.filter(name__icontains=desc_key.split('-')[0])
                if series_qs.exists():
                    product = Product.objects.filter(series=series_qs.first()).first()
                    if product:
                        by_product[product.id].append((file_path, product))
                        matched_count += 1
                        break
        else:
            unmatched_remaining.append(u)

    print(f"\nManuel duzeltmelerle eslesen: {matched_count}")
    print(f"Hala eslesmeyen: {len(unmatched_remaining)}")
    print(f"Yuklenecek foto: {sum(len(v) for v in by_product.values())}")

    count = 0
    with transaction.atomic():
        for product_id, items in by_product.items():
            for i, (file_path, product) in enumerate(items):
                if not os.path.exists(file_path):
                    continue
                try:
                    result = upload_photo(file_path, product, sort_order=i, is_primary=(i == 0))
                    if result:
                        uploaded += 1
                    count += 1
                except Exception as e:
                    print(f"  [HATA] {file_path}: {e}")

    print(f"\n{'=' * 60}")
    print("SONUC")
    print(f"{'=' * 60}")
    print(f"Yuklenen foto: {uploaded}")

    products_with = Product.objects.filter(product_media__isnull=False).distinct().count()
    products_without = Product.objects.filter(product_media__isnull=True).distinct().count()
    print(f"Resimli urun: {products_with}")
    print(f"Resimsiz urun: {products_without}")
    print(f"Toplam media: {Media.objects.filter(kind='image').count()}")

    if unmatched_remaining:
        print(f"\nEslesemeyen dosyalar ({len(unmatched_remaining)}):")
        unique = sorted(set(u['extracted_code'] for u in unmatched_remaining if u.get('extracted_code')))
        for c in unique[:30]:
            print(f"  - {c}")


if __name__ == '__main__':
    main()
