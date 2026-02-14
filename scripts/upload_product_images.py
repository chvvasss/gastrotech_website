#!/usr/bin/env python
"""
Product Image Upload Script

This script reads an Excel file containing product image mappings and uploads
images to the Gastrotech admin panel via the API. It handles:
- Matching products by code (model_code/variant) or name
- Checking for Vital brand products (skip image upload)
- Checking for existing product images (skip if already has images)
- Uploading new images via the admin API
- Generating a detailed report

Usage:
    python scripts/upload_product_images.py

Requirements:
    - pandas
    - openpyxl
    - requests
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

import pandas as pd


# Add backend to path for Django access
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django
django.setup()

from apps.catalog.models import Product, Variant, Brand, ProductMedia


# Configuration
EXCEL_FILE = PROJECT_ROOT / "700serisifotolar" / "020_061_images_summary.xlsx"
IMAGES_DIR = PROJECT_ROOT / "700serisifotolar" / "020_061_images"
OUTPUT_REPORT = PROJECT_ROOT / "700serisifotolar" / "upload_report.xlsx"
VITAL_BRAND_NAME = "vital"  # Case-insensitive check


class ProductImageUploader:
    """Handles matching products and uploading images."""
    
    def __init__(self):
        self.results = []
        self.stats = {
            "total_rows": 0,
            "products_found": 0,
            "products_not_found": 0,
            "vital_brand_skipped": 0,
            "existing_image_skipped": 0,
            "images_uploaded": 0,
            "upload_errors": 0,
            "no_image_file": 0,
        }
    
    def load_excel(self):
        """Load and parse the Excel file."""
        print(f"Loading Excel file: {EXCEL_FILE}")
        self.df = pd.read_excel(EXCEL_FILE)
        self.stats["total_rows"] = len(self.df)
        print(f"Loaded {len(self.df)} rows")
        return self.df
    
    def find_product_by_code(self, code):
        """
        Find a product by code. Tries multiple matching strategies:
        1. Match against Variant.model_code
        2. Match against Product.slug containing the code
        3. Match against Product.title_tr containing the code
        """
        if not code or pd.isna(code):
            return None
        
        code = str(code).strip().upper()
        
        # Skip generic codes like "700", "900" which don't map to specific products
        if code in ("700", "900", "300", "150", "120", "102"):
            return None
        
        # Strategy 1: Find variant by model_code
        variant = Variant.objects.filter(model_code__iexact=code).select_related("product", "product__brand").first()
        if variant:
            return variant.product
        
        # Strategy 2: Find product by slug containing code
        product = Product.objects.filter(slug__icontains=code.lower()).select_related("brand").first()
        if product:
            return product
        
        # Strategy 3: Find product by title containing code
        product = Product.objects.filter(title_tr__icontains=code).select_related("brand").first()
        if product:
            return product
        
        return None
    
    def find_product_by_name(self, name):
        """Find a product by name using fuzzy matching."""
        if not name or pd.isna(name):
            return None
        
        name = str(name).strip()
        
        # Try exact match first
        product = Product.objects.filter(title_tr__iexact=name).select_related("brand").first()
        if product:
            return product
        
        # Try contains match
        product = Product.objects.filter(title_tr__icontains=name).select_related("brand").first()
        if product:
            return product
        
        return None
    
    def is_vital_brand(self, product):
        """Check if product is a Vital brand product."""
        if not product or not product.brand:
            return False
        return VITAL_BRAND_NAME in product.brand.name.lower()
    
    def has_existing_images(self, product):
        """Check if product already has images."""
        if not product:
            return False
        return ProductMedia.objects.filter(product=product).exists()
    
    def upload_image_django(self, product, image_path):
        """Upload image directly via Django ORM."""
        from apps.catalog.models import Media
        
        if not image_path.exists():
            return False, "Image file not found"
        
        try:
            # Read image file
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Determine content type
            suffix = image_path.suffix.lower()
            content_type_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            content_type = content_type_map.get(suffix, "image/png")
            
            # Create Media object
            media = Media.objects.create(
                kind=Media.Kind.IMAGE,
                filename=image_path.name,
                content_type=content_type,
                data=image_data,
            )
            
            # Create ProductMedia association
            existing_count = ProductMedia.objects.filter(product=product).count()
            ProductMedia.objects.create(
                product=product,
                media=media,
                sort_order=existing_count,
                is_primary=existing_count == 0,  # First image is primary
            )
            
            return True, f"Uploaded {image_path.name}"
            
        except Exception as e:
            return False, str(e)
    
    def process_row(self, row):
        """Process a single row from the Excel file."""
        image_file = row.get("image_file")
        code = row.get("code")
        name = row.get("name")
        
        result = {
            "image_file": image_file,
            "code": code if not pd.isna(code) else "",
            "name": name if not pd.isna(name) else "",
            "product_found": "",
            "product_slug": "",
            "brand": "",
            "status": "",
            "remarks": "",
        }
        
        # Find product by code first, then by name
        product = None
        if code and not pd.isna(code):
            product = self.find_product_by_code(code)
        
        if not product and name and not pd.isna(name):
            product = self.find_product_by_name(name)
        
        if not product:
            result["status"] = "ürün bulunamadı"
            result["remarks"] = f"Code: {code}, Name: {name}"
            self.stats["products_not_found"] += 1
            return result
        
        self.stats["products_found"] += 1
        result["product_found"] = product.title_tr
        result["product_slug"] = product.slug
        result["brand"] = product.brand.name if product.brand else ""
        
        # Check if Vital brand
        if self.is_vital_brand(product):
            result["status"] = "Vital markalı – görsel yüklenmedi"
            result["remarks"] = "Vital markası tespit edildi, görsel güncellenmedi"
            self.stats["vital_brand_skipped"] += 1
            return result
        
        # Check if already has images
        if self.has_existing_images(product):
            result["status"] = "mevcut görsel var – atlandı"
            result["remarks"] = "Ürün zaten görsele sahip"
            self.stats["existing_image_skipped"] += 1
            return result
        
        # Check if image file exists
        if not image_file or pd.isna(image_file):
            result["status"] = "görsel dosyası yok"
            self.stats["no_image_file"] += 1
            return result
        
        image_path = IMAGES_DIR / image_file
        if not image_path.exists():
            result["status"] = "görsel dosyası bulunamadı"
            result["remarks"] = f"Dosya: {image_file}"
            self.stats["no_image_file"] += 1
            return result
        
        # Upload image
        success, message = self.upload_image_django(product, image_path)
        
        if success:
            result["status"] = "görsel yüklendi"
            result["remarks"] = message
            self.stats["images_uploaded"] += 1
        else:
            result["status"] = "yükleme hatası"
            result["remarks"] = message
            self.stats["upload_errors"] += 1
        
        return result
    
    def run(self):
        """Run the full upload process."""
        print("=" * 60)
        print("Product Image Upload Script")
        print("=" * 60)
        
        # Load Excel
        self.load_excel()
        
        # Process each row
        print("\nProcessing rows...")
        for idx, row in self.df.iterrows():
            result = self.process_row(row)
            self.results.append(result)
            
            # Progress indicator
            if (idx + 1) % 20 == 0:
                print(f"  Processed {idx + 1}/{len(self.df)} rows...")
        
        print(f"  Processed all {len(self.df)} rows")
        
        # Generate report
        self.generate_report()
        
        # Print summary
        self.print_summary()
    
    def generate_report(self):
        """Generate Excel report of results."""
        print(f"\nGenerating report: {OUTPUT_REPORT}")
        
        report_df = pd.DataFrame(self.results)
        
        # Reorder columns for better readability
        columns = [
            "code", "name", "image_file", "product_found", 
            "product_slug", "brand", "status", "remarks"
        ]
        report_df = report_df[[c for c in columns if c in report_df.columns]]
        
        report_df.to_excel(OUTPUT_REPORT, index=False, engine="openpyxl")
        print(f"Report saved to: {OUTPUT_REPORT}")
    
    def print_summary(self):
        """Print summary statistics."""
        print("\n" + "=" * 60)
        print("UPLOAD SUMMARY")
        print("=" * 60)
        print(f"Total rows processed:     {self.stats['total_rows']}")
        print(f"Products found:           {self.stats['products_found']}")
        print(f"Products not found:       {self.stats['products_not_found']}")
        print(f"Vital brand (skipped):    {self.stats['vital_brand_skipped']}")
        print(f"Existing images (skipped): {self.stats['existing_image_skipped']}")
        print(f"Images uploaded:          {self.stats['images_uploaded']}")
        print(f"Upload errors:            {self.stats['upload_errors']}")
        print(f"No image file:            {self.stats['no_image_file']}")
        print("=" * 60)


def main():
    """Main entry point."""
    uploader = ProductImageUploader()
    uploader.run()


if __name__ == "__main__":
    main()
