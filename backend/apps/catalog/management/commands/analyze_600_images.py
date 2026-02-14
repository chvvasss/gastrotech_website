"""
Analyze 600 series images and match them with products.
"""
import os
import re
import pandas as pd
from django.core.management.base import BaseCommand
from apps.catalog.models import Product, Variant


class Command(BaseCommand):
    help = 'Analyze 600 series images and create matching report'

    def handle(self, *args, **options):
        # Paths
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))),
            '600SERISIFOTOLAR')
        excel_path = os.path.join(base_path, '600series_images2_summary.xlsx')
        images_path = os.path.join(base_path, '600series_images2')

        self.stdout.write(f"Excel path: {excel_path}")
        self.stdout.write(f"Images path: {images_path}")

        # Read Excel
        df = pd.read_excel(excel_path)
        self.stdout.write(f"\nTotal rows in Excel: {len(df)}")

        # Get 600 series products with variants
        products = Product.objects.filter(
            series__name__icontains='600'
        ).prefetch_related('variants')

        # Build product matching rules
        product_rules = {
            # Product slug -> keywords to match in image name/text
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
        for p in products:
            for v in p.variants.all():
                variant_to_product[v.model_code] = {
                    'product_id': str(p.id),
                    'product_slug': p.slug,
                    'product_name': p.name,
                }

        # Analyze each row
        matches = []
        unmatched = []

        for idx, row in df.iterrows():
            image_file = row['image_file']
            code = row['code'] if pd.notna(row['code']) else None
            name = row['name'] if pd.notna(row['name']) else ''
            product_text = row['product_text'] if pd.notna(row['product_text']) else ''

            # Try to find matching product
            matched_product = None
            match_method = None

            # Method 1: Direct code match
            if code and code in variant_to_product:
                matched_product = variant_to_product[code]
                match_method = f'variant_code:{code}'

            # Method 2: Code in image filename
            if not matched_product:
                image_lower = image_file.lower()
                for vcode, vproduct in variant_to_product.items():
                    if vcode.lower() in image_lower:
                        matched_product = vproduct
                        match_method = f'filename_code:{vcode}'
                        break

            # Method 3: Keyword matching
            if not matched_product:
                combined_text = f"{image_file} {name} {product_text}".lower()
                combined_text = combined_text.replace('_', '-').replace(' ', '-')

                for slug, keywords in product_rules.items():
                    for kw in keywords:
                        if kw.lower() in combined_text:
                            # Find the product by slug
                            product = products.filter(slug=slug).first()
                            if product:
                                matched_product = {
                                    'product_id': str(product.id),
                                    'product_slug': product.slug,
                                    'product_name': product.name,
                                }
                                match_method = f'keyword:{kw}'
                                break
                    if matched_product:
                        break

            # Record result
            result = {
                'image_file': image_file,
                'code': code,
                'name': name[:50] if name else '',
                'product_text': product_text[:50] if product_text else '',
            }

            if matched_product:
                result['matched'] = True
                result['product_slug'] = matched_product['product_slug']
                result['product_name'] = matched_product['product_name']
                result['product_id'] = matched_product['product_id']
                result['match_method'] = match_method
                matches.append(result)
            else:
                result['matched'] = False
                result['match_method'] = 'no_match'
                unmatched.append(result)

        # Print report
        self.stdout.write("\n" + "="*80)
        self.stdout.write("MATCHED IMAGES:")
        self.stdout.write("="*80)

        # Group by product
        by_product = {}
        for m in matches:
            slug = m['product_slug']
            if slug not in by_product:
                by_product[slug] = []
            by_product[slug].append(m)

        for slug, items in sorted(by_product.items()):
            self.stdout.write(f"\n{items[0]['product_name']} ({slug}):")
            for item in items:
                self.stdout.write(f"  - {item['image_file']}")
                self.stdout.write(f"    Match: {item['match_method']}")

        self.stdout.write("\n" + "="*80)
        self.stdout.write("UNMATCHED IMAGES:")
        self.stdout.write("="*80)

        for item in unmatched:
            self.stdout.write(f"\n  - {item['image_file']}")
            self.stdout.write(f"    Code: {item['code']}, Name: {item['name']}")

        self.stdout.write("\n" + "="*80)
        self.stdout.write("SUMMARY:")
        self.stdout.write(f"  Total images: {len(df)}")
        self.stdout.write(f"  Matched: {len(matches)}")
        self.stdout.write(f"  Unmatched: {len(unmatched)}")
        self.stdout.write(f"  Products with images: {len(by_product)}")
