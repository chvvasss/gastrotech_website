"""
Seed command for Hazırlık Ekipmanları category structure with logo groups.

This command creates:
1. 6 new brands (Gtech, ESSEDUE, LERICA, CGF, vitella, Dalle)
2. 5 subcategories under Hazırlık Ekipmanları
3. 15 series within those subcategories
4. Logo group mappings (Brand -> Series within Category)

Usage:
    python manage.py seed_hazirlik_categories
    python manage.py seed_hazirlik_categories --dry-run

Idempotent: Safe to run multiple times without creating duplicates.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import (
    Category, Series, Brand, BrandCategory,
    CategoryLogoGroup, LogoGroupSeries
)
from apps.common.slugify_tr import slugify_tr


class Command(BaseCommand):
    help = 'Seed Hazirlik Ekipmanlari category structure with logo groups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN] No changes will be made'))
        
        # Counters
        stats = {
            'brands_created': 0,
            'brands_existing': 0,
            'categories_created': 0,
            'categories_existing': 0,
            'series_created': 0,
            'series_existing': 0,
            'logo_groups_created': 0,
            'logo_groups_existing': 0,
            'logo_series_created': 0,
            'logo_series_existing': 0,
        }
        
        with transaction.atomic():
            # Step 1: Create/Get Brands
            # Note: Gtech is actually Gastrotech. We use the existing gastrotech brand.
            brands_data = [
                {'name': 'Gastrotech', 'slug': 'gastrotech'},  # Ensure correct casing
                {'name': 'ESSEDUE', 'slug': 'essedue'},
                {'name': 'LERICA', 'slug': 'lerica'},
                {'name': 'CGF', 'slug': 'cgf'},
                {'name': 'vitella', 'slug': 'vitella'},
                {'name': 'Dalle', 'slug': 'dalle'},
            ]
            
            brands = {}
            self.stdout.write('\n=== BRANDS ===')
            for bd in brands_data:
                brand, created = Brand.objects.get_or_create(
                    slug=bd['slug'],
                    defaults={'name': bd['name'], 'is_active': True}
                )
                # Ensure name correction if it exists but with different case
                if not created and brand.name != bd['name']:
                    old_name = brand.name
                    brand.name = bd['name']
                    brand.save(update_fields=['name'])
                    self.stdout.write(self.style.WARNING(f"  [!] Updated brand name: {old_name} -> {brand.name}"))

                brands[bd['slug']] = brand
                if created:
                    stats['brands_created'] += 1
                    self.stdout.write(self.style.SUCCESS(f"  [+] Created brand: {bd['name']}"))
                else:
                    stats['brands_existing'] += 1
                    self.stdout.write(f"  [=] Brand exists: {bd['name']}")
            
            # Step 2: Get parent category
            try:
                parent = Category.objects.get(slug='hazirlik-ekipmanlari')
                self.stdout.write(f'\nFound parent: {parent.name} (id={parent.id})')
            except Category.DoesNotExist:
                self.stdout.write(self.style.ERROR('Parent category "hazirlik-ekipmanlari" not found!'))
                return
            
            # Step 3: Define structure
            # Format: {category: {brand_slug: [series_list]}}
            structure = {
                'Sebze Yıkama Makineleri': {
                    'slug': 'sebze-yikama-makineleri',
                    'logos': {
                        'gastrotech': [
                            {'name': 'Sebze Yıkama Makineleri', 'is_heading': False},
                            {'name': 'Devrilir Sebze Yıkama Makineleri', 'is_heading': False},
                        ],
                    },
                },
                'Et İşleme Makineleri': {
                    'slug': 'et-isleme-makineleri',
                    'logos': {
                        'essedue': [
                            {'name': 'Gıda Dilimleme Makineleri', 'is_heading': False},
                            {'name': 'Diket Gıda Dilimleme Makineleri', 'is_heading': False},
                            {'name': 'Otomatik Gıda Dilimleme Makineleri', 'is_heading': False},
                        ],
                    },
                },
                'Vakum Makineleri': {
                    'slug': 'vakum-makineleri',
                    'logos': {
                        'lerica': [
                            {'name': 'Vakum Makineleri', 'is_heading': False},
                        ],
                    },
                },
                'Hamur İşleme Makineleri': {
                    'slug': 'hamur-isleme-makineleri',
                    'logos': {
                        'cgf': [
                            {'name': 'Kanatlı Hamur Açma Makineleri', 'is_heading': False},
                            {'name': 'Kruvasan Kesme Cihazları', 'is_heading': False},
                            {'name': 'Set Üstü Hamur Açma Makineleri', 'is_heading': False},
                            {'name': 'Standlı Hamur Açma Makineleri', 'is_heading': False},
                        ],
                        'vitella': [
                            {'name': 'Hamur Bölme ve Yuvarlama Makineleri', 'is_heading': False},
                            {'name': 'Manuel Hamur Bölme ve Yuvarlama Makineleri', 'is_heading': False},
                            {'name': 'Otomatik Hamur Bölme ve Yuvarlama Makineleri', 'is_heading': False},
                        ],
                    },
                },
                'Sebze ve Meyve Kurutucular': {
                    'slug': 'sebze-ve-meyve-kurutucular',
                    'logos': {
                        'gastrotech': [
                            {'name': 'Dehidratörler', 'is_heading': False},
                        ],
                        'dalle': [
                            {'name': 'Dondurarak Sebze ve Meyve Kurutucular', 'is_heading': False},
                        ],
                    },
                },
            }
            
            self.stdout.write('\n=== CATEGORIES, SERIES & LOGO GROUPS ===')
            
            for cat_name, cat_data in structure.items():
                cat_slug = cat_data['slug']
                
                # Create/Get Category
                category, created = Category.objects.get_or_create(
                    parent=parent,
                    slug=cat_slug,
                    defaults={'name': cat_name}
                )
                if created:
                    stats['categories_created'] += 1
                    self.stdout.write(self.style.SUCCESS(f"\n  [+] Created category: {cat_name}"))
                else:
                    stats['categories_existing'] += 1
                    self.stdout.write(f"\n  [=] Category exists: {cat_name}")
                
                # Process each logo group
                logo_order = 0
                for brand_slug, series_list in cat_data['logos'].items():
                    brand = brands.get(brand_slug)
                    if not brand:
                        # Try to get existing brand
                        brand = Brand.objects.filter(slug=brand_slug).first()
                    
                    if not brand:
                        self.stdout.write(self.style.ERROR(f"      Brand not found: {brand_slug}"))
                        continue
                    
                    # Create/Get LogoGroup
                    logo_group, lg_created = CategoryLogoGroup.objects.get_or_create(
                        category=category,
                        brand=brand,
                        defaults={'order': logo_order, 'is_active': True}
                    )
                    logo_order += 1
                    
                    if lg_created:
                        stats['logo_groups_created'] += 1
                        self.stdout.write(self.style.SUCCESS(f"      [+] Created logo group: {brand.name}"))
                    else:
                        stats['logo_groups_existing'] += 1
                        self.stdout.write(f"      [=] Logo group exists: {brand.name}")
                    
                    # Create/Get BrandCategory association
                    BrandCategory.objects.get_or_create(
                        brand=brand,
                        category=category,
                        defaults={'is_active': True, 'order': 0}
                    )
                    
                    # Create series and link to logo group
                    series_order = 0
                    for series_info in series_list:
                        series_name = series_info['name']
                        series_slug = slugify_tr(series_name)
                        is_heading = series_info.get('is_heading', False)
                        
                        # Create/Get Series
                        series, s_created = Series.objects.get_or_create(
                            category=category,
                            slug=series_slug,
                            defaults={'name': series_name, 'order': series_order}
                        )
                        series_order += 1
                        
                        if s_created:
                            stats['series_created'] += 1
                            self.stdout.write(self.style.SUCCESS(f"          [+] Created series: {series_name}"))
                        else:
                            stats['series_existing'] += 1
                            self.stdout.write(f"          [=] Series exists: {series_name}")
                        
                        # Link series to logo group - use update_or_create to ensure is_heading is corrected
                        lgs, lgs_created = LogoGroupSeries.objects.update_or_create(
                            logo_group=logo_group,
                            series=series,
                            defaults={'order': series_order, 'is_heading': is_heading}
                        )
                        
                        if lgs_created:
                            stats['logo_series_created'] += 1
                        else:
                            stats['logo_series_existing'] += 1
            
            if dry_run:
                self.stdout.write(self.style.WARNING('\n[DRY RUN] Rolling back all changes...'))
                transaction.set_rollback(True)
        
        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('SUMMARY')
        self.stdout.write('=' * 50)
        self.stdout.write(f"Brands created:      {stats['brands_created']}")
        self.stdout.write(f"Brands existing:     {stats['brands_existing']}")
        self.stdout.write(f"Categories created:  {stats['categories_created']}")
        self.stdout.write(f"Categories existing: {stats['categories_existing']}")
        self.stdout.write(f"Series created:      {stats['series_created']}")
        self.stdout.write(f"Series existing:     {stats['series_existing']}")
        self.stdout.write(f"Logo groups created: {stats['logo_groups_created']}")
        self.stdout.write(f"Logo groups existing:{stats['logo_groups_existing']}")
        self.stdout.write(f"Logo-series links:   {stats['logo_series_created']} new, {stats['logo_series_existing']} existing")
        
        self.stdout.write(self.style.SUCCESS('\n[OK] Seed completed successfully!'))
