from django.core.management.base import BaseCommand
import pandas as pd
import os
from apps.catalog.models import Product, Variant, Series, Category, Brand
from apps.common.slugify_tr import slugify_tr

class Command(BaseCommand):
    help = 'Audit Project AAA Data against Database'

    def handle(self, *args, **options):
        AAA_DIR = r"c:\gastrotech.com.tr.0101\gastrotech.com_cursor\AAA"
        
        # Files to check (priority order doesn't matter for "missing" check, we want the union)
        files = [
            "bulk_upload_urunler5_varyant5_FINAL_fixed_series.xlsx",
            "bulk_upload_urunlerson_varyantson_FIXED.xlsx",
            "bulk_upload_URUN_VARYANT_FIXED_REF.xlsx"
        ]
        
        # 1. Cache DB Data
        self.stdout.write("Fetching DB data...")
        db_products = {p.slug: p for p in Product.objects.all()}
        db_variants = {(v.product.slug, v.model_code): v for v in Variant.objects.select_related('product').all()}
        
        missing_prods = [] # List of {slug, file}
        missing_vars = []  # List of {product, model, file}
        
        for fname in files:
            fpath = os.path.join(AAA_DIR, fname)
            if not os.path.exists(fpath):
                self.stdout.write(self.style.WARNING(f"File not found: {fname}"))
                continue
                
            self.stdout.write(f"\nScanning: {fname}")
            try:
                df_prods = pd.read_excel(fpath, sheet_name='Products').fillna("")
                df_vars = pd.read_excel(fpath, sheet_name='Variants').fillna("")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error: {e}"))
                continue
            
            # Check Products
            for _, row in df_prods.iterrows():
                slug_raw = row.get('Product Slug') or row.get('Product Name')
                if not slug_raw: continue
                slug = slugify_tr(str(slug_raw))
                
                if slug not in db_products:
                    # Check if we already noted it
                    if not any(m['slug'] == slug for m in missing_prods):
                        missing_prods.append({'slug': slug, 'name': row.get('Product Name'), 'file': fname})
            
            # Check Variants
            for _, row in df_vars.iterrows():
                p_slug_raw = row.get('Product Slug')
                model_raw = row.get('Model Code')
                if not p_slug_raw or not model_raw: continue
                p_slug = slugify_tr(str(p_slug_raw))
                model = str(model_raw).strip()
                
                if (p_slug, model) not in db_variants:
                     if not any(m['product'] == p_slug and m['model'] == model for m in missing_vars):
                        missing_vars.append({'product': p_slug, 'model': model, 'file': fname})

        self.stdout.write("\n" + "="*50)
        self.stdout.write("DEEP DATA INTEGRITY CHECK")
        self.stdout.write("="*50)

        # check for empty layouts
        empty_layouts = Product.objects.filter(spec_layout__exact=[]).count()
        self.stdout.write(f"Products with Empty Spec Layout: {empty_layouts}")
        if empty_layouts > 0:
            for p in Product.objects.filter(spec_layout__exact=[])[:5]:
                self.stdout.write(f"  - {p.slug}")

        # check for variants with empty specs
        empty_specs = Variant.objects.filter(specs__exact={}).count()
        self.stdout.write(f"Variants with Empty Specs: {empty_specs}")
        
        # Check for Series Visibility issues (Single Product Series)
        # This was Phase 2, but good to verify
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("AGGREGATE REPORT (MISSING ITEMS)")
        self.stdout.write("="*50)
        
        self.stdout.write(f"Total Missing Products: {len(missing_prods)}")
        for p in missing_prods:
            self.stdout.write(f"  - {p['slug']} (found in {p['file']})")
            
        self.stdout.write(f"\nTotal Missing Variants: {len(missing_vars)}")
        for v in missing_vars:
            self.stdout.write(f"  - {v['product']} -> {v['model']} (found in {v['file']})")

        
        # Save results to file for next steps if needed
        # For now just output to stdout is fine for the agent to read.
