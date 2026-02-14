"""
Upload 600 series images to products via Django ORM.
This script directly uploads images to the database without needing browser automation.
"""
import os
import re
import json
import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.db import transaction
from apps.catalog.models import Product, Variant, ProductMedia, Media


class Command(BaseCommand):
    help = 'Upload 600 series images to matching products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be uploaded without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Upload even if product already has images'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        # Paths
        base_path = Path('/app/600SERISIFOTOLAR')
        if not base_path.exists():
            base_path = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / '600SERISIFOTOLAR'
        excel_path = base_path / '600series_images2_summary.xlsx'
        images_path = base_path / '600series_images2'

        self.stdout.write(f"Excel path: {excel_path}")
        self.stdout.write(f"Images path: {images_path}")
        self.stdout.write(f"Dry run: {dry_run}")
        self.stdout.write(f"Force upload: {force}")

        # Read Excel
        df = pd.read_excel(excel_path)
        self.stdout.write(f"\nTotal rows in Excel: {len(df)}")

        # Get 600 series products with variants
        products = Product.objects.filter(
            series__name__icontains='600'
        ).prefetch_related('variants', 'product_media')

        # Build matching rules
        product_rules = {
            '600-serisi-gazli-ocaklar': ['gazli-ocak', 'gas-burner-top', 'gko'],
            '600-serisi-gazli-wok-ocaklar': ['wok', 'gkw'],
            '600-serisi-elektrikli-ocaklar-yuvarlak-pleytli': ['round-hot-plate', 'yuvarlak-pleyt', 'ek0', 'electric-round'],
            '600-serisi-induksiyon-ocaklar': ['induksiyon', 'induction', 'ik0'],
            '600-serisi-gazli-kuzineler': ['gazli-kuzine', 'gas-burner-range', 'gkf'],
            '600-serisi-elektrikli-fritozler': ['elektrikli-frit', 'electric-fryer', 'efp'],
            '600-serisi-gazli-fritozler': ['gazli-frit', 'gas-fryer', 'gfp'],
            '600-serisi-gazli-sulu-izgaralar': ['gazli-sulu', 'gas-vapor', 'gsi'],
            '600-serisi-elektrikli-sulu-izgaralar': ['elektrikli-sulu', 'electric-vapor', 'esi'],
            '600-serisi-gazli-lavatas-izgaralar': ['lavatas', 'lavastone', 'lava-grill', 'gli'],
            '600-serisi-elektrikli-pleyt-izgaralar': ['elektrikli-pleyt', 'electric-fry-top', 'epi'],
            '600-serisi-gazli-pleyt-izgaralar': ['gazli-pleyt', 'gas-fry-top', 'gp1', 'smooth-ribbed'],
            '600-serisi-elektrikli-benmariler': ['benmari', 'bain-marie', 'esb'],
            '600-serisi-elektrikli-makarna-pisiriciler': ['makarna', 'pasta-cook', 'emf'],
            '600-serisi-elektrikli-patates-dinlendirme': ['patates', 'chip-scuttle', 'epd'],
            '600-serisi-ara-tezgahlar': ['ara-tezgah', 'neutral', 'ntr'],
            '600-serisi-alt-stantlar-kapaksiz': ['alt-stant', 'open-front', 'base-cupboard'],
            '600-serisi-alt-stantlar-kapakli': ['kapakli', 'with-door'],
            '600-serisi-alt-stantlar-cekmeceli': ['cekmeceli', 'with-drawer'],
        }

        # Create variant code to product mapping
        variant_to_product = {}
        product_map = {}
        for p in products:
            product_map[p.slug] = p
            for v in p.variants.all():
                variant_to_product[v.model_code] = p

        # Group images by product
        product_images = {}

        for idx, row in df.iterrows():
            image_file = row['image_file']
            code = row['code'] if pd.notna(row['code']) else None

            # Try to find matching product
            matched_product = None

            # Method 1: Direct code match
            if code and code in variant_to_product:
                matched_product = variant_to_product[code]

            # Method 2: Code in image filename
            if not matched_product:
                image_lower = image_file.lower()
                for vcode, product in variant_to_product.items():
                    if vcode.lower() in image_lower:
                        matched_product = product
                        break

            # Method 3: Keyword matching
            if not matched_product:
                name = row['name'] if pd.notna(row['name']) else ''
                product_text = row['product_text'] if pd.notna(row['product_text']) else ''
                combined_text = f"{image_file} {name} {product_text}".lower()
                combined_text = combined_text.replace('_', '-').replace(' ', '-')

                for slug, keywords in product_rules.items():
                    for kw in keywords:
                        if kw.lower() in combined_text:
                            if slug in product_map:
                                matched_product = product_map[slug]
                                break
                    if matched_product:
                        break

            if matched_product:
                if matched_product.slug not in product_images:
                    product_images[matched_product.slug] = []
                product_images[matched_product.slug].append({
                    'image_file': image_file,
                    'image_path': images_path / image_file,
                    'product': matched_product,
                })

        # Upload report
        report = {
            'uploaded': [],
            'skipped': [],
            'errors': [],
            'no_match': []
        }

        self.stdout.write("\n" + "="*80)
        self.stdout.write("UPLOAD PLAN:")
        self.stdout.write("="*80)

        for slug, images in sorted(product_images.items()):
            product = images[0]['product']
            existing_count = product.product_media.count()

            self.stdout.write(f"\n{product.name} ({slug}):")
            self.stdout.write(f"  Existing images: {existing_count}")
            self.stdout.write(f"  New images: {len(images)}")

            if existing_count > 0 and not force:
                self.stdout.write(f"  -> SKIPPING (already has images, use --force to override)")
                report['skipped'].append({
                    'product': product.name,
                    'slug': slug,
                    'reason': f'Already has {existing_count} images'
                })
                continue

            for i, img_data in enumerate(images):
                self.stdout.write(f"  [{i+1}] {img_data['image_file']}")

            if not dry_run:
                try:
                    with transaction.atomic():
                        for i, img_data in enumerate(images):
                            image_path = img_data['image_path']

                            if not image_path.exists():
                                raise FileNotFoundError(f"Image not found: {image_path}")

                            # Read image file
                            with open(image_path, 'rb') as f:
                                content = f.read()

                            # Get file extension and content type
                            ext = image_path.suffix.lower()
                            if ext in ['.jpg', '.jpeg']:
                                content_type = 'image/jpeg'
                            elif ext == '.png':
                                content_type = 'image/png'
                            elif ext == '.webp':
                                content_type = 'image/webp'
                            else:
                                content_type = 'image/png'

                            # Get image dimensions
                            width, height = None, None
                            try:
                                from PIL import Image
                                import io
                                img = Image.open(io.BytesIO(content))
                                width, height = img.size
                            except Exception:
                                pass

                            # Create Media (stores bytes directly in DB)
                            media = Media.objects.create(
                                kind='image',
                                filename=image_path.name,
                                content_type=content_type,
                                bytes=content,
                                width=width,
                                height=height,
                            )

                            # Create ProductMedia association
                            ProductMedia.objects.create(
                                product=product,
                                media=media,
                                sort_order=existing_count + i,
                                is_primary=(i == 0 and existing_count == 0)
                            )

                            self.stdout.write(f"    -> Uploaded: {image_path.name}")

                    report['uploaded'].append({
                        'product': product.name,
                        'slug': slug,
                        'images': [img['image_file'] for img in images]
                    })

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"    -> ERROR: {e}"))
                    report['errors'].append({
                        'product': product.name,
                        'slug': slug,
                        'error': str(e)
                    })

        # Print summary
        self.stdout.write("\n" + "="*80)
        self.stdout.write("SUMMARY:")
        self.stdout.write("="*80)
        self.stdout.write(f"  Total products with matches: {len(product_images)}")
        self.stdout.write(f"  Uploaded: {len(report['uploaded'])}")
        self.stdout.write(f"  Skipped: {len(report['skipped'])}")
        self.stdout.write(f"  Errors: {len(report['errors'])}")

        if dry_run:
            self.stdout.write("\n[DRY RUN] No changes were made. Run without --dry-run to upload.")

        # Save report to file
        report_path = base_path / 'upload_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        self.stdout.write(f"\nReport saved to: {report_path}")
