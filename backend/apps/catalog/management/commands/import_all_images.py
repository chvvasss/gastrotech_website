"""
Import ALL missing product images from C:\\Users\\emir\\Desktop\\Fotolar

Strategy:
1. Match by exact variant model_code (e.g. EKO6010.png -> Variant 'EKO6010')
2. Match by normalized model_code (case-insensitive, strip spaces/hyphens)
3. Match by product name substring
4. Skip non-product files (lists, fiyat listesi, etc.)

Run:
    python manage.py import_all_images --dry-run
    python manage.py import_all_images
"""
import hashlib
import os
import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Media, ProductMedia, Product, Variant


SRC_DIR = Path(r"C:\Users\emir\Desktop\Fotolar")

# Files to skip (non-product images)
SKIP_NAMES = {
    'fiyat listesi', 'list', 'list 1', 'list 2', 'list1', 'list2', 'liste',
    'bicaklar',
}


def normalize(s):
    """Normalize a string for fuzzy matching."""
    return re.sub(r'[\s\-_./]', '', s).upper()


class Command(BaseCommand):
    help = "Import all missing product images"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Build lookup maps
        self.stdout.write("Building lookup maps...")

        # Map: model_code -> Variant
        variant_by_code = {}
        variant_by_normalized = {}
        for v in Variant.objects.select_related('product').all():
            variant_by_code[v.model_code] = v
            variant_by_normalized[normalize(v.model_code)] = v

        # Map: product name (normalized) -> Product
        product_by_name = {}
        for p in Product.objects.all():
            product_by_name[normalize(p.name)] = p

        # Get existing media filenames to avoid duplicates
        existing_filenames = set(Media.objects.filter(kind='image').values_list('filename', flat=True))

        # Get existing ProductMedia links to avoid duplicate links
        existing_links = set(
            ProductMedia.objects.values_list('product_id', 'media_id')
        )

        # Scan all image files
        self.stdout.write("Scanning image files...")
        image_files = []
        for root, dirs, files in os.walk(SRC_DIR):
            for f in sorted(files):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    image_files.append({
                        'path': os.path.join(root, f),
                        'filename': f,
                        'name_no_ext': os.path.splitext(f)[0],
                        'folder': os.path.basename(root),
                    })

        self.stdout.write(f"Found {len(image_files)} image files")

        imported = 0
        skipped_existing = 0
        skipped_no_match = 0
        skipped_files = 0
        linked = 0
        errors = 0
        match_methods = {'exact': 0, 'normalized': 0, 'name': 0}

        for img in image_files:
            name = img['name_no_ext']
            filename = img['filename']

            # Skip non-product files
            if name.lower() in SKIP_NAMES or name.isdigit():
                skipped_files += 1
                continue

            # Skip already imported
            if filename in existing_filenames:
                skipped_existing += 1
                continue

            # Try matching strategies
            product = None
            method = None

            # Strategy 1: Exact variant code match
            if name in variant_by_code:
                product = variant_by_code[name].product
                method = 'exact'

            # Strategy 2: Normalized variant code match
            if not product:
                norm = normalize(name)
                if norm in variant_by_normalized:
                    product = variant_by_normalized[norm].product
                    method = 'normalized'

            # Strategy 3: Check if it's a multi-variant image (e.g. "TNS-622D&TNS-634D&TNS-644D")
            if not product and ('&' in name or ',' in name):
                parts = re.split(r'[&,]', name)
                for part in parts:
                    part = part.strip()
                    if part in variant_by_code:
                        product = variant_by_code[part].product
                        method = 'exact'
                        break
                    norm_part = normalize(part)
                    if norm_part in variant_by_normalized:
                        product = variant_by_normalized[norm_part].product
                        method = 'normalized'
                        break

            if not product:
                skipped_no_match += 1
                self.stdout.write(self.style.WARNING(
                    f"  NO MATCH: {img['folder']}/{filename}"
                ))
                continue

            match_methods[method] += 1

            if dry_run:
                self.stdout.write(f"  [DRY-RUN] Would import {filename} -> '{product.name}' (via {method})")
                imported += 1
                continue

            # Import the image
            try:
                with open(img['path'], 'rb') as fh:
                    data = fh.read()

                content_type = 'image/png' if filename.lower().endswith('.png') else 'image/jpeg'
                checksum = hashlib.sha256(data).hexdigest()

                with transaction.atomic():
                    media = Media.objects.create(
                        kind='image',
                        filename=filename,
                        content_type=content_type,
                        bytes=data,
                        size_bytes=len(data),
                        checksum_sha256=checksum,
                    )

                    # Check if link already exists
                    existing_count = ProductMedia.objects.filter(product=product).count()
                    link, created = ProductMedia.objects.get_or_create(
                        product=product,
                        media=media,
                        defaults={'order': existing_count}
                    )
                    if created:
                        linked += 1

                imported += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  IMPORTED: {filename} -> '{product.name}' (via {method})"
                ))
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"  ERROR: {filename}: {e}"))

        # Summary
        self.stdout.write("\n=== SUMMARY ===")
        self.stdout.write(f"Total files scanned: {len(image_files)}")
        self.stdout.write(f"Already imported (skipped): {skipped_existing}")
        self.stdout.write(f"Non-product files (skipped): {skipped_files}")
        self.stdout.write(f"No match found: {skipped_no_match}")
        self.stdout.write(f"Successfully imported: {imported}")
        self.stdout.write(f"New ProductMedia links: {linked}")
        self.stdout.write(f"Errors: {errors}")
        self.stdout.write(f"Match methods: {match_methods}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes made"))
