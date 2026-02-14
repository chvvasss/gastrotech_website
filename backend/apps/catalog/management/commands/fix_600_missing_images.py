"""
Fix missing images for 600 series products.
Assigns available images to products that don't have images yet.
"""
import os
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Product, ProductMedia, Media


class Command(BaseCommand):
    help = 'Fix missing images for 600 series products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Paths
        base_path = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / '600SERISIFOTOLAR'
        images_path = base_path / '600series_images2'

        self.stdout.write(f"Images path: {images_path}")
        self.stdout.write(f"Dry run: {dry_run}")

        # Define manual mappings for products without images
        # These are based on analysis of available images
        manual_mappings = {
            # Alt Stantlar Kapaklı - "kapakli" ve "with-door" içeren görseller
            '600-serisi-alt-stantlar-kapakli': [
                '012_01_alt-stant-kapakli-cekmeceli-base-cupboard-with-door-with-drawer.png',
                '012_02_alt-stant-kapakli-cekmeceli-base-cupboard-with-door-with-drawer.png',
            ],
            # Alt Stantlar Çekmeceli - aynı görseller (kapaklı/çekmeceli birlikte)
            '600-serisi-alt-stantlar-cekmeceli': [
                '012_01_alt-stant-kapakli-cekmeceli-base-cupboard-with-door-with-drawer.png',
                '012_02_alt-stant-kapakli-cekmeceli-base-cupboard-with-door-with-drawer.png',
            ],
            # Elektrikli Pleyt Izgaralar - smooth/ribbed görselleri (zaten gazlı pleyt'e atanmış ama elektrikli için de uygun)
            '600-serisi-elektrikli-pleyt-izgaralar': [
                '005_02_duz-nervurlu-duz-nervurlu-smooth-ribbed-smooth-ribbed.png',
                '006_01_duz-nervurlu-duz-nervurlu-smooth-ribbed-smooth-ribbed.png',
            ],
        }

        # Products that have NO matching images in the folder
        no_images_available = [
            '600-serisi-elektrikli-benmariler',  # ESB kodları - görsel yok
            '600-serisi-gazli-fritozler',         # GFP kodları - görsel yok
            '600-serisi-induksiyon-ocaklar',      # IK0 kodları - görsel yok
        ]

        report = {
            'uploaded': [],
            'skipped': [],
            'no_image_available': [],
        }

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("PROCESSING MISSING IMAGES:")
        self.stdout.write("=" * 80)

        # Process manual mappings
        for slug, image_files in manual_mappings.items():
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(f"\n[SKIP] Product not found: {slug}")
                continue

            existing_count = product.product_media.count()

            self.stdout.write(f"\n{product.name} ({slug}):")
            self.stdout.write(f"  Existing images: {existing_count}")
            self.stdout.write(f"  Images to add: {len(image_files)}")

            if existing_count > 0:
                self.stdout.write(f"  -> SKIPPING (already has images)")
                report['skipped'].append({
                    'product': product.name,
                    'slug': slug,
                    'reason': f'Already has {existing_count} images'
                })
                continue

            if not dry_run:
                try:
                    with transaction.atomic():
                        for i, image_file in enumerate(image_files):
                            image_path = images_path / image_file

                            if not image_path.exists():
                                self.stdout.write(f"  [ERROR] Image not found: {image_file}")
                                continue

                            # Read image
                            with open(image_path, 'rb') as f:
                                content = f.read()

                            # Get content type
                            ext = image_path.suffix.lower()
                            content_type = 'image/png' if ext == '.png' else 'image/jpeg'

                            # Get dimensions
                            width, height = None, None
                            try:
                                from PIL import Image
                                import io
                                img = Image.open(io.BytesIO(content))
                                width, height = img.size
                            except Exception:
                                pass

                            # Create Media
                            media = Media.objects.create(
                                kind='image',
                                filename=image_path.name,
                                content_type=content_type,
                                bytes=content,
                                width=width,
                                height=height,
                            )

                            # Create ProductMedia
                            ProductMedia.objects.create(
                                product=product,
                                media=media,
                                sort_order=i,
                                is_primary=(i == 0)
                            )

                            self.stdout.write(f"  -> Uploaded: {image_file}")

                    report['uploaded'].append({
                        'product': product.name,
                        'slug': slug,
                        'images': image_files
                    })

                except Exception as e:
                    self.stdout.write(f"  [ERROR] {e}")
            else:
                for image_file in image_files:
                    self.stdout.write(f"  [DRY-RUN] Would upload: {image_file}")

        # Report products with no available images
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("PRODUCTS WITH NO AVAILABLE IMAGES:")
        self.stdout.write("=" * 80)

        for slug in no_images_available:
            try:
                product = Product.objects.get(slug=slug)
                self.stdout.write(f"\n{product.name} ({slug}):")
                self.stdout.write(f"  -> NO MATCHING IMAGES IN FOLDER")
                self.stdout.write(f"  -> Manual upload required")
                report['no_image_available'].append({
                    'product': product.name,
                    'slug': slug,
                })
            except Product.DoesNotExist:
                self.stdout.write(f"\n[SKIP] Product not found: {slug}")

        # Summary
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("SUMMARY:")
        self.stdout.write("=" * 80)
        self.stdout.write(f"  Uploaded: {len(report['uploaded'])}")
        self.stdout.write(f"  Skipped: {len(report['skipped'])}")
        self.stdout.write(f"  No images available: {len(report['no_image_available'])}")

        if dry_run:
            self.stdout.write("\n[DRY RUN] No changes were made.")

        # Save report
        report_path = base_path / 'fix_missing_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        self.stdout.write(f"\nReport saved to: {report_path}")
