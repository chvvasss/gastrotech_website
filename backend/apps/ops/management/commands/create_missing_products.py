"""
Django management command to create missing products/variants for unmatched images.
This populates the catalog with products that have image files but no DB entries.
"""
import os
import re
from pathlib import Path
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.models import Product, Variant, Brand, Category, Series


# Product definitions based on image file prefixes
# Categories: firinlar, pisirme-ekipmanlari, hazirlik-ekipmanlari, sogutma-uniteleri,
#            bulasikhane, camasirhane, kafeterya-ekipmanlari, tamamlayici-ekipmanlar
PRODUCT_DEFINITIONS = {
    # Format: prefix -> (product_name, category_slug, brand_slug, series_slug or None)
    
    # Chrome Coated Grills
    'cc': {
        'name': 'Chrome Coated Pleyt Izgaralar',
        'category': 'pisirme-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # Fritözler (Fryers)
    'gkf': {
        'name': 'Gazlı Kuzine Tip Fritözler',
        'category': 'pisirme-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # Show Ocaklar ECO
    'gso': {
        'name': 'Gazlı Show Ocaklar ECO Serisi',
        'category': 'pisirme-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # Konveksiyonel Ocaklar ECO
    'gko': {
        'name': 'Gazlı Konveksiyonel Ocaklar ECO Serisi',
        'category': 'pisirme-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # GO - Geniş Ocaklar
    'go': {
        'name': 'Endüstriyel Geniş Ocaklar',
        'category': 'pisirme-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # WO - Wok Ocaklar
    'wo': {
        'name': 'Wok Ocakları',
        'category': 'pisirme-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # EDT - Elektrikli Döner Tepsi
    'edt': {
        'name': 'Elektrikli Döner Tepsiler',
        'category': 'pisirme-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # GDT - Gazlı Döner Tepsi
    'gdt': {
        'name': 'Gazlı Döner Tepsiler',
        'category': 'pisirme-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # EKT - Elektrikli Kuzine Tip
    'ekt': {
        'name': 'Elektrikli Kuzine Tip Ekipmanlar',
        'category': 'pisirme-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # GKT - Gazlı Kuzine Tip
    'gkt': {
        'name': 'Gazlı Kuzine Tip Ekipmanlar',
        'category': 'pisirme-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # GKTD - Gazlı Kuzine Tip Derin
    'gktd': {
        'name': 'Gazlı Kuzine Tip Derin Fritözler',
        'category': 'pisirme-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # IKO - Indüksiyon Kuzine Ocakları
    'iko': {
        'name': 'İndüksiyon Kuzine Ocakları',
        'category': 'pisirme-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # VYO - Vakum Yoğurma
    'vyo': {
        'name': 'Vakumlu Yoğurma Makineleri',
        'category': 'hazirlik-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # GKFE - Gazlı Kuzine Fırın Elektrikli
    'gkfe': {
        'name': 'Gazlı Kuzine Elektrikli Fırınlar',
        'category': 'firinlar',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # VMD - Vakum Makinesi Dijital
    'vmd': {
        'name': 'Vakum Paketleme Makineleri Dijital',
        'category': 'hazirlik-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # EPD - Elektrikli Patates Dinlendirme
    'epd': {
        'name': 'Elektrikli Patates Dinlendirme Üniteleri',
        'category': 'pisirme-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # NTR - Nötr Tezgahlar
    'ntr': {
        'name': 'Nötr Tezgahlar',
        'category': 'tamamlayici-ekipmanlar',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # STD - Stand
    'std': {
        'name': 'Ekipman Standları',
        'category': 'tamamlayici-ekipmanlar',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # VBS - Vakum Blender Serisi
    'vbs': {
        'name': 'Vakum Blender Sistemleri',
        'category': 'hazirlik-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # SYM - Sıcak Yemek Modülü
    'sym': {
        'name': 'Sıcak Yemek Modülleri',
        'category': 'kafeterya-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # VSHDP - Vakum Servis Hızlı Dondurma
    'vshdp': {
        'name': 'Hızlı Dondurma Sistemleri',
        'category': 'sogutma-uniteleri',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # EYO - Elektrikli Yoğurma
    'eyo': {
        'name': 'Elektrikli Yoğurma Makineleri',
        'category': 'hazirlik-ekipmanlari',
        'brand': 'gastrotech',
        'series': None,
    },
    
    # NEVO - Nevo Fırınlar (belongs to PRIME brand)
    'nevo': {
        'name': 'NEVO Serisi Konveksiyonel Fırınlar',
        'category': 'firinlar',
        'brand': 'prime',
        'series': None,
    },
    
    # PRIME - Prime Fırınlar  
    'prime': {
        'name': 'PRIME Serisi Konveksiyonel Fırınlar',
        'category': 'firinlar',
        'brand': 'prime',
        'series': None,
    },
    
    # MAESTRO (already exists, just add variant)
    'maestro': {
        'name': 'Maestro Serisi Fırınlar',
        'category': 'firinlar',
        'brand': 'maestro',
        'series': None,
        'skip_product': True,  # Product likely exists
    },
    
    # VBY - Bulaşık Makineleri (to cover vby variants not covered by smart mapping)
    'vby': {
        'name': 'VBY Serisi Tezgah Altı Bulaşık Makineleri',
        'category': 'bulasikhane',
        'brand': 'gastrotech',
        'series': None,
    },
}


def get_model_code_from_filename(filename):
    """Extract model code from filename."""
    stem = Path(filename).stem
    parts = stem.split('_')
    base = parts[0]
    if '(' in base:
        base = base.split('(')[0]
    return base.strip()


def get_prefix(code):
    """Extract letter prefix from code."""
    prefix = ''
    for c in code.lower():
        if c.isalpha():
            prefix += c
        else:
            break
    return prefix


class Command(BaseCommand):
    help = 'Create missing products and variants for unmatched image files'

    def add_arguments(self, parser):
        parser.add_argument(
            'directory',
            type=str,
            help='Directory containing image files'
        )
        parser.add_argument(
            '--commit',
            action='store_true',
            help='Actually commit changes (default is dry-run)'
        )

    def handle(self, *args, **options):
        directory = options['directory']
        dry_run = not options['commit']
        
        if not os.path.isdir(directory):
            raise CommandError(f"Directory does not exist: {directory}")
        
        self.stdout.write(f"Scanning: {directory}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN mode"))
        
        # Collect all unmatched codes grouped by prefix
        unmatched_by_prefix = defaultdict(set)
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    code = get_model_code_from_filename(file)
                    
                    # Check if variant exists
                    variant = Variant.objects.filter(model_code__iexact=code).first()
                    if not variant:
                        prefix = get_prefix(code)
                        if prefix:
                            unmatched_by_prefix[prefix].add(code.upper())
        
        # Process each prefix
        products_created = 0
        variants_created = 0
        
        for prefix, codes in sorted(unmatched_by_prefix.items()):
            definition = PRODUCT_DEFINITIONS.get(prefix)
            
            if not definition:
                self.stdout.write(self.style.WARNING(
                    f"  {prefix}: {len(codes)} codes - NO DEFINITION (skipping)"
                ))
                continue
            
            self.stdout.write(f"\n{prefix.upper()}: {len(codes)} codes")
            
            # Get or create product
            product_name = definition['name']
            product = Product.objects.filter(name__iexact=product_name).first()
            
            if not product and not definition.get('skip_product'):
                category = Category.objects.filter(slug=definition['category']).first()
                brand = Brand.objects.filter(slug=definition['brand']).first()
                
                if not category:
                    self.stderr.write(f"  Category not found: {definition['category']}")
                    continue
                if not brand:
                    self.stderr.write(f"  Brand not found: {definition['brand']}")
                    continue
                
                if not dry_run:
                    product = Product.objects.create(
                        name=product_name,
                        slug=slugify(product_name),
                        category=category,
                        brand=brand,
                        status='active',
                    )
                    products_created += 1
                    self.stdout.write(self.style.SUCCESS(f"  Created Product: {product_name}"))
                else:
                    self.stdout.write(f"  [DRY] Would create Product: {product_name}")
            elif product:
                self.stdout.write(f"  Using existing Product: {product.name}")
            
            # Create variants
            for code in sorted(codes):
                existing = Variant.objects.filter(model_code__iexact=code).first()
                if existing:
                    continue
                
                if not dry_run and product:
                    Variant.objects.create(
                        product=product,
                        model_code=code,
                        sku=code,
                    )
                    variants_created += 1
                    self.stdout.write(f"    + Variant: {code}")
                else:
                    self.stdout.write(f"    [DRY] Would create Variant: {code}")
        
        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(f"Products created: {products_created}")
        self.stdout.write(f"Variants created: {variants_created}")
