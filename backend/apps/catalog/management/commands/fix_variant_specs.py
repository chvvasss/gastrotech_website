from django.core.management.base import BaseCommand
from django.db import transaction
import pandas as pd
import os
import json
from apps.catalog.models import Variant
from apps.common.slugify_tr import slugify_tr

class Command(BaseCommand):
    help = 'Fix variants with empty specs from Excel'

    def handle(self, *args, **options):
        AAA_DIR = r"c:\gastrotech.com.tr.0101\gastrotech.com_cursor\AAA"
        files = [
            "bulk_upload_urunler5_varyant5_FINAL_fixed_series.xlsx",
            "bulk_upload_urunlerson_varyantson_FIXED.xlsx",
            "bulk_upload_URUN_VARYANT_FIXED_REF.xlsx"
        ]
        
        self.stdout.write("=" * 70)
        self.stdout.write("FIXING MISSING SPECS")
        self.stdout.write("=" * 70)
        
        # 1. Provide a map of (product_slug, model_code) -> specs_dict from Excel
        excel_specs = {}
        
        self.stdout.write("Loading Excel Data...")
        for fname in files:
            fpath = os.path.join(AAA_DIR, fname)
            if not os.path.exists(fpath): continue
            
            try:
                df = pd.read_excel(fpath, sheet_name='Variants').fillna("")
                
                # Identify Spec columns
                spec_cols = [c for c in df.columns if str(c).startswith('Spec:')]
                
                for _, row in df.iterrows():
                    p_slug = slugify_tr(str(row.get('Product Slug')))
                    model = str(row.get('Model Code')).strip()
                    
                    if not p_slug or not model: continue
                    
                    # Logically duplicate rows in different files might overwrite, specifically "FINAL" files should win
                    # But here we just want ANY data if we have none.
                    
                    specs = {}
                    for col in spec_cols:
                        val = row.get(col)
                        if val:
                            key = col.replace("Spec:", "")
                            # Lowercase key for consistency with our schema (capacity, power, etc)
                            # Actually our schema seems to use lowercase keys like 'capacity', 'power'
                            specs[key.lower()] = str(val).strip()
                            
                    if specs:
                        excel_specs[(p_slug, model)] = specs
            except Exception as e:
                self.stdout.write(f"Error reading {fname}: {e}")
                pass
        
        self.stdout.write(f"Loaded spec data for {len(excel_specs)} unique variants.")
        
        # 2. Find DB Variants with empty specs
        with transaction.atomic():
            variants = Variant.objects.filter(specs__exact={})
            self.stdout.write(f"Found {variants.count()} variants with empty specs in DB.")
            
            fixed_count = 0
            for v in variants:
                key = (v.product.slug, v.model_code)
                
                if key in excel_specs:
                    new_specs = excel_specs[key]
                    v.specs = new_specs
                    v.save()
                    self.stdout.write(f"  [FIXED] {v.product.slug} - {v.model_code}")
                    self.stdout.write(f"          Specs: {new_specs}")
                    fixed_count += 1
                else:
                    self.stdout.write(f"  [MISSING] {v.product.slug} - {v.model_code} (Not found in Excel)")
            
            self.stdout.write(self.style.SUCCESS(f"\nFixed {fixed_count} variants."))
