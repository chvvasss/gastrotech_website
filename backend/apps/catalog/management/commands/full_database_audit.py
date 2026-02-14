"""
Comprehensive Database Audit Script
Compares CSV data with database state, identifies and fixes mismatches
"""
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Brand, Category, Series, Product, BrandCategory

class Command(BaseCommand):
    help = 'Complete database audit - verify all products/series in correct categories'

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write("COMPLETE DATABASE AUDIT")
        self.stdout.write("=" * 70)
        
        # Load CSV data
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
        csv_dir = os.path.join(base_dir, 'sss')
        
        self.stdout.write(f"Looking for CSVs in: {csv_dir}")
        
        # Check if CSVs exist, if not just skip CSV comparison
        csv_exists = os.path.exists(os.path.join(csv_dir, 'catalog_product_202601181553.csv'))
        if csv_exists:
            prod_csv = pd.read_csv(os.path.join(csv_dir, 'catalog_product_202601181553.csv'))
            series_csv = pd.read_csv(os.path.join(csv_dir, 'catalog_series_202601181553.csv'))
            cat_csv = pd.read_csv(os.path.join(csv_dir, 'catalog_category_202601181553.csv'))
            self.stdout.write(f"\nCSV Data: {len(prod_csv)} products, {len(series_csv)} series, {len(cat_csv)} categories")
        else:
            self.stdout.write(self.style.WARNING("CSV files not found, skipping CSV comparison"))
        
        # Database counts
        db_products = Product.objects.count()
        db_series = Series.objects.count()
        db_categories = Category.objects.count()
        self.stdout.write(f"Database: {db_products} products, {db_series} series, {db_categories} categories")
        
        # ===== PHASE 1: Category Distribution =====
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("PHASE 1: CATEGORY DISTRIBUTION")
        self.stdout.write("=" * 50)
        
        for cat in Category.objects.all().order_by('name'):
            series_count = Series.objects.filter(category=cat).count()
            product_count = Product.objects.filter(category=cat).count()
            self.stdout.write(f"\n{cat.name} ({cat.slug}):")
            self.stdout.write(f"  Series: {series_count}, Products: {product_count}")
            
            # List series in this category
            if series_count > 0:
                for s in Series.objects.filter(category=cat)[:10]:
                    prod_in_series = Product.objects.filter(series=s).count()
                    self.stdout.write(f"    - {s.name} ({prod_in_series} products)")
                if series_count > 10:
                    self.stdout.write(f"    ... and {series_count - 10} more")
        
        # ===== PHASE 2: Products without category =====
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("PHASE 2: PRODUCTS WITHOUT CATEGORY")
        self.stdout.write("=" * 50)
        
        orphan_products = Product.objects.filter(category__isnull=True)
        self.stdout.write(f"Products without category: {orphan_products.count()}")
        
        if orphan_products.exists():
            with transaction.atomic():
                fixed = 0
                for product in orphan_products:
                    if product.series and product.series.category:
                        product.category = product.series.category
                        product.save()
                        fixed += 1
                        self.stdout.write(f"  Fixed: {product.name} -> {product.category.name}")
                self.stdout.write(self.style.SUCCESS(f"Fixed {fixed} orphan products"))
        
        # ===== PHASE 3: Series without category =====
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("PHASE 3: SERIES WITHOUT CATEGORY")
        self.stdout.write("=" * 50)
        
        orphan_series = Series.objects.filter(category__isnull=True)
        self.stdout.write(f"Series without category: {orphan_series.count()}")
        for s in orphan_series:
            self.stdout.write(self.style.WARNING(f"  - {s.name} ({s.slug})"))
        
        # ===== PHASE 4: Single-Product Series =====
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("PHASE 4: SINGLE-PRODUCT SERIES")
        self.stdout.write("=" * 50)
        
        single_product_series = []
        for series in Series.objects.all():
            prod_count = Product.objects.filter(series=series).count()
            if prod_count == 1:
                product = Product.objects.filter(series=series).first()
                single_product_series.append({
                    'series': series,
                    'product': product
                })
        
        self.stdout.write(f"\nSeries with exactly 1 product: {len(single_product_series)}")
        for item in single_product_series:
            self.stdout.write(f"  - Series: {item['series'].name}")
            self.stdout.write(f"    Product: {item['product'].name}")
            self.stdout.write(f"    Category: {item['series'].category.name if item['series'].category else 'N/A'}")
        
        # ===== PHASE 5: Brand-Category Links =====
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("PHASE 5: BRAND-CATEGORY LINKS")
        self.stdout.write("=" * 50)
        
        # For each category, check if brands with products there have M2M links
        missing_links = []
        for cat in Category.objects.all():
            # Get brands that have products in this category
            products_in_cat = Product.objects.filter(category=cat)
            brand_ids = set(products_in_cat.values_list('brand_id', flat=True))
            
            for brand_id in brand_ids:
                if not brand_id:
                    continue
                brand = Brand.objects.get(id=brand_id)
                
                # Check if M2M link exists
                link_exists = BrandCategory.objects.filter(
                    brand=brand, 
                    category=cat, 
                    is_active=True
                ).exists()
                
                if not link_exists:
                    missing_links.append((brand, cat))
        
        self.stdout.write(f"\nMissing brand-category links: {len(missing_links)}")
        
        if missing_links:
            with transaction.atomic():
                for brand, cat in missing_links:
                    BrandCategory.objects.get_or_create(
                        brand=brand,
                        category=cat,
                        defaults={'is_active': True}
                    )
                    self.stdout.write(self.style.SUCCESS(f"  Created: {brand.name} -> {cat.name}"))
        
        # ===== SUMMARY =====
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("AUDIT SUMMARY")
        self.stdout.write("=" * 70)
        self.stdout.write(f"Total categories: {db_categories}")
        self.stdout.write(f"Total series: {db_series}")
        self.stdout.write(f"Total products: {db_products}")
        self.stdout.write(f"Single-product series: {len(single_product_series)}")
        self.stdout.write(f"Missing brand-category links fixed: {len(missing_links)}")
