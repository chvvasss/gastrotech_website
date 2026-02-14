
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.db.models import Count, F, Q
from apps.catalog.models import Product, Series, Variant, Brand, Category, Media
from apps.common.slugify_tr import slugify_tr
import unicodedata
import re

class Command(BaseCommand):
    help = 'Fixes catalog data inconsistencies based on Audit Report'

    def handle(self, *args, **options):
        self.stdout.write("Starting Catalog Repair...")
        
        with transaction.atomic():
            self.fix_product_categories()
            self.fix_brand_duplicates()
            self.fix_variant_skus()
            
            
            self.fix_brand_categories()
            
        self.stdout.write(self.style.SUCCESS("All Repair Phases Completed Successfully"))

    def fix_brand_categories(self):
        """Phase 6: Populate BrandCategory from Products"""
        self.stdout.write("--- Phase 6: Populating BrandCategory ---")
        
        # distinct brand-category pairs from products
        pairs = Product.objects.filter(
            brand__isnull=False, 
            category__isnull=False
        ).values('brand', 'category').distinct()
        
        count = 0
        from apps.catalog.models import BrandCategory
        
        for p in pairs:
            _, created = BrandCategory.objects.get_or_create(
                brand_id=p['brand'],
                category_id=p['category'],
                defaults={'is_active': True}
            )
            if created:
                count += 1
                
        self.stdout.write(f"Created {count} new BrandCategory relationships")

    def fix_product_categories(self):
        """Phase 3 Prerequisite: Populate product.category_id from series"""
        self.stdout.write("--- Phase 3: Populating Product Categories ---")
        
        products = Product.objects.filter(category__isnull=True, series__isnull=False)
        count = products.count()
        self.stdout.write(f"Found {count} products with missing category")
        
        if count > 0:
            # Efficient update using subquery join logic equivalent
            # Django update with F() from related object is tricky in bulk update for joins,
            # but we can iterate or use raw SQL. For 252 items, iteration is fine and safe.
            updated = 0
            for p in products:
                if p.series.category:
                    p.category = p.series.category
                    p.save(update_fields=['category', 'updated_at'])
                    updated += 1
            self.stdout.write(f"Updated {updated} products with series category")

    def fix_brand_duplicates(self):
        """Phase 1: Deduplicate Brands"""
        self.stdout.write("--- Phase 1: Deduplicating Brands ---")
        
        # Helper to canonize
        def canon(name):
            if not name: return ""
            s = str(name)
            s = unicodedata.normalize("NFKD", s)
            s = "".join(ch for ch in s if not unicodedata.combining(ch))
            s = s.casefold().strip()
            return s

        brands = list(Brand.objects.all())
        groups = {}
        
        for b in brands:
            k = canon(b.name)
            if k not in groups: groups[k] = []
            groups[k].append(b)
            
        for key, group in groups.items():
            if len(group) > 1:
                self.stdout.write(f"Duplicate Group for '{key}': {[b.name for b in group]}")
                
                # Sort: Prefer one with most products, then ID
                group.sort(key=lambda b: (b.products.count(), b.created_at), reverse=True)
                winner = group[0]
                losers = group[1:]
                
                self.stdout.write(f"  Winner: {winner.name} (Products: {winner.products.count()})")
                
                for loser in losers:
                    self.stdout.write(f"  Merging loser: {loser.name} -> {winner.name}")
                    # Move products
                    Product.objects.filter(brand=loser).update(brand=winner)
                    # Delete or deactivate loser? Report says "no delete" initially but implies merge.
                    # We will append (MERGED) to name and slug to avoid constraints, and set inactive
                    loser.is_active = False
                    loser.name = f"{loser.name} (MERGED)"
                    loser.slug = f"{loser.slug}-merged-{loser.id}"[:150]
                    loser.save()

    def fix_variant_skus(self):
        """Phase 5: Populate Variant SKUs"""
        self.stdout.write("--- Phase 5: Fix Variant SKUs ---")
        
        variants = Variant.objects.filter(sku__isnull=True)
        count = variants.count()
        self.stdout.write(f"Found {count} variants with missing SKU")
        
        for v in variants:
            # Strategy: model_code if exists, else product slug + part of ID
            new_sku = None
            if v.model_code:
                # Clean model code
                code = re.sub(r'[^a-zA-Z0-9]', '', v.model_code).upper()
                new_sku = code
            
            if not new_sku:
                new_sku = f"{v.product.slug[:20]}-{str(v.id)[:8]}"
                
            # Check uniqueness
            original_sku = new_sku
            counter = 1
            while Variant.objects.filter(sku=new_sku).exists():
                new_sku = f"{original_sku}-{counter}"
                counter += 1
                
            v.sku = new_sku
            v.save(update_fields=['sku', 'updated_at'])
            
        self.stdout.write(f"Fixed {count} variant SKUs")
