import json
import os
import hashlib
import requests
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Any
from urllib.error import URLError
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.models import (
    Product, 
    Variant, 
    Category, 
    Series, 
    Brand, 
    TaxonomyNode, 
    Media, 
    ProductMedia
)

class Command(BaseCommand):
    help = "Import products, variants, and images from a JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Path to the JSON file.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run validation without saving changes.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Commit changes even if errors occur (skip failed items).",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        dry_run = options["dry_run"]
        force = options["force"]

        self.stdout.write("Starting JSON import...")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE: No changes will be saved."))

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"Invalid JSON: {e}"))
            return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error reading file: {e}"))
            return

        if not isinstance(data, list):
            self.stderr.write(self.style.ERROR("JSON root must be a list of products."))
            return

        stats = {
            "products_processed": 0,
            "products_created": 0,
            "products_updated": 0,
            "variants_created": 0,
            "variants_updated": 0,
            "images_processed": 0,
            "errors": [],
        }

        # Pre-cache lookups to avoid N+1 queries
        self.categories = {c.slug: c for c in Category.objects.all()}
        self.series_map = {s.slug: s for s in Series.objects.select_related('category').all()}
        self.brands = {b.slug: b for b in Brand.objects.all()}
        self.nodes = {n.slug: n for n in TaxonomyNode.objects.all()}

        try:
            with transaction.atomic():
                for index, item in enumerate(data):
                    try:
                        self.process_product(item, index, stats)
                    except Exception as e:
                        error_msg = f"Item {index} ({item.get('slug', 'unknown')}): {str(e)}"
                        stats["errors"].append(error_msg)
                        if not force:
                            raise Exception(error_msg) # Abort transaction
                        else:
                            self.stdout.write(self.style.ERROR(error_msg))

                if dry_run:
                    raise Exception("Dry run complete (rolling back transaction).")

        except Exception as e:
            if str(e) == "Dry run complete (rolling back transaction).":
                self.stdout.write(self.style.SUCCESS("Dry run successful. No changes made."))
            elif "Item" in str(e) and not force:
                 self.stderr.write(self.style.ERROR(f"Aborted due to error: {e}"))
            else:
                self.stderr.write(self.style.ERROR(f"An unexpected error occurred: {str(e)}"))
                if options.get('verbosity', 1) > 1:
                    raise e
            
            self.print_stats(stats)
            return

        self.stdout.write(self.style.SUCCESS("Import completed successfully."))
        self.print_stats(stats)

    def process_product(self, data: Dict[str, Any], index: int, stats: Dict[str, Any]):
        stats["products_processed"] += 1
        
        # 1. Validation & Relations
        slug = data.get("slug")
        if not slug:
            raise ValueError("Missing 'slug' field.")
        
        category_slug = data.get("category")
        series_slug = data.get("series")
        brand_slug = data.get("brand")
        
        if not category_slug or not brand_slug:
            raise ValueError("Missing required relation fields (category, brand).")

        category = self.categories.get(category_slug)
        if not category:
            raise ValueError(f"Category not found: {category_slug}")
            
        # Handle optional Series
        series = None
        if series_slug:
            series = self.series_map.get(series_slug)
            if not series:
                 # Auto-create series under product category
                 self.stdout.write(self.style.WARNING(f"Series not found: {series_slug}. Creating it under {category.slug}."))
                 series, _ = Series.objects.get_or_create(
                     slug=series_slug,
                     category=category,
                     defaults={'name': series_slug.replace('-', ' ').title(), 'order': 999}
                 )
                 # Add to map
                 self.series_map[series_slug] = series

            if series.category_id != category.id:
                 # Trust Series category
                 self.stdout.write(self.style.WARNING(f"Auto-correcting category to match series '{series_slug}': {category.slug} -> {series.category.slug}"))
                 category = series.category
        else:
            # Auto-assign to default series
            default_series_slug = f"{category_slug}-general"
            series = self.series_map.get(default_series_slug)
            if not series:
                # Create default series on the fly
                # We need to be careful with transaction here, but we are in one.
                # Update series_map to avoid re-querying
                series, _ = Series.objects.get_or_create(
                    slug=default_series_slug,
                    category=category,
                    defaults={
                        "name": "General",
                        "description_short": f"General products for {category.name}",
                        "order": 999,
                        "is_featured": False
                    }
                )
                self.series_map[default_series_slug] = series
                self.stdout.write(f"Created default series: {series.slug}")

        if brand_slug == 'gtech':
            brand_slug = 'gastrotech'

        brand = self.brands.get(brand_slug)
        if not brand:
             # Auto-create brand
             self.stdout.write(self.style.WARNING(f"Brand not found: {brand_slug}. Creating it."))
             brand = Brand.objects.create(
                 name=brand_slug.title(), 
                 slug=brand_slug, 
                 is_active=True
             )
             self.brands[brand_slug] = brand


        primary_node = None
        if data.get("primary_node"):
            primary_node = self.nodes.get(data.get("primary_node"))
            if not primary_node:
                 self.stdout.write(self.style.WARNING(f"Taxonomy Node not found: {data.get('primary_node')} (Skipping assignment)"))
                 primary_node = None

        # 2. Product Upsert
        defaults = {
            "name": data.get("name", slug),
            "title_tr": data.get("title_tr", data.get("name", slug)),
            "title_en": data.get("title_en", ""),
            "status": data.get("status", "draft"),
            "is_featured": data.get("is_featured", False),
            "series": series,
            "category": category,
            "brand": brand,
            "primary_node": primary_node,
            "general_features": data.get("general_features", []),
            "short_specs": data.get("short_specs", []),
            "notes": data.get("notes", []),
            "long_description": data.get("long_description", ""),
            "seo_title": data.get("seo_title", ""),
            "seo_description": data.get("seo_description", ""),
        }

        product, created = Product.objects.update_or_create(
            slug=slug,
            defaults=defaults
        )

        if created:
            stats["products_created"] += 1
        else:
            stats["products_updated"] += 1
            
        self.stdout.write(f"Product: {product.slug} ({'Created' if created else 'Updated'})")

        # 3. Variants
        variants_data = data.get("variants", [])
        if not variants_data:
            raise ValueError("Product must have at least one variant.")

        for v_data in variants_data:
            self.process_variant(product, v_data, stats)

        # 4. Images
        images_data = data.get("images", [])
        if images_data:
            self.process_images(product, images_data, stats)

    def process_variant(self, product: Product, data: Dict[str, Any], stats: Dict[str, Any]):
        model_code = data.get("model_code")
        if not model_code:
            raise ValueError("Variant missing 'model_code'.")

        defaults = {
            "product": product,
            "name_tr": data.get("name_tr", model_code),
            "name_en": data.get("name_en", ""),
            "sku": data.get("sku"),
            "dimensions": data.get("dimensions", ""),
            "weight_kg": self.parse_decimal(data.get("weight_kg")),
            "list_price": self.parse_decimal(data.get("list_price")),
            "price_override": self.parse_decimal(data.get("price_override")),
            "stock_qty": data.get("stock_qty"), # Can be None
            "specs": data.get("specs", {}),
        }

        variant, created = Variant.objects.update_or_create(
            model_code=model_code,
            defaults=defaults
        )
        
        if created:
            stats["variants_created"] += 1
        else:
            stats["variants_updated"] += 1

    def process_images(self, product: Product, images_data: List[Dict[str, Any]], stats: Dict[str, Any]):
        # Clear existing media links? 
        # Strategy: Keep existing, append new? Or Replace all? 
        # For idempotency, if we re-run, checking by filename/checksum would be ideal.
        # But for now, let's just attempt to add if not exists (by filename match on product).
        
        existing_links = {pm.media.filename: pm for pm in product.product_media.select_related('media').all()}
        
        for img_data in images_data:
            url_or_path = img_data.get("url")
            if not url_or_path:
                continue

            filename = os.path.basename(url_or_path)
            # If URL, might need better filename extraction
            if url_or_path.startswith("http"):
                 if "?" in filename:
                     filename = filename.split("?")[0]

            is_primary = img_data.get("is_primary", False)
            order = img_data.get("sort_order", 0)
            alt = img_data.get("alt", "")

            # Check if linked
            if filename in existing_links:
                # Update metadata if needed
                pm = existing_links[filename]
                pm.is_primary = is_primary
                pm.sort_order = order
                pm.alt = alt
                pm.save()
                continue
            
            # Use existing Media if hash matches? 
            # Simplified: Use existing Media by filename if needed, or create new.
            # Assuming uniqueness by filename for now.
            
            media_content = self.fetch_image_content(url_or_path)
            if not media_content:
                self.stdout.write(self.style.WARNING(f"Could not fetch image: {url_or_path}"))
                continue

            # Compute Hash
            file_hash = hashlib.sha256(media_content).hexdigest()
            
            # Try to find existing media by hash (Deduplication)
            media = Media.objects.filter(checksum_sha256=file_hash).first()
            
            if not media:
                # Create Media
                media = Media(
                    kind=Media.Kind.IMAGE,
                    filename=filename,
                    content_type="image/jpeg", # naive, should detect
                    bytes=media_content
                )
                media.save()
                stats["images_processed"] += 1

            # Link
            ProductMedia.objects.create(
                product=product,
                media=media,
                is_primary=is_primary,
                sort_order=order,
                alt=alt
            )

    def fetch_image_content(self, path: str) -> Optional[bytes]:
        try:
            if path.startswith("http"):
                response = requests.get(path, timeout=10)
                if response.status_code == 200:
                    return response.content
            else:
                # Local path
                # Remove file:// prefix if present
                if path.startswith("file:///"):
                     path = path[8:]
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        return f.read()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Image read error: {e}"))
            return None
        return None

    def parse_decimal(self, value: Any) -> Optional[Decimal]:
        if value is None:
            return None
        if isinstance(value, (float, int)):
            return Decimal(str(value))
        if isinstance(value, str) and value.strip():
             try:
                 return Decimal(value.strip())
             except:
                 return None
        return None

    def print_stats(self, stats: Dict[str, Any]):
        self.stdout.write("\nSummary:")
        self.stdout.write(f"Products Processed: {stats['products_processed']}")
        self.stdout.write(f"Products Created:   {stats['products_created']}")
        self.stdout.write(f"Products Updated:   {stats['products_updated']}")
        self.stdout.write(f"Variants Created:   {stats['variants_created']}")
        self.stdout.write(f"Variants Updated:   {stats['variants_updated']}")
        self.stdout.write(f"Images Processed:   {stats['images_processed']}")
        
        if stats["errors"]:
            self.stdout.write(self.style.ERROR(f"\nTotal Errors: {len(stats['errors'])}"))
            for err in stats["errors"][:10]:
                self.stdout.write(f"- {err}")
            if len(stats["errors"]) > 10:
                 self.stdout.write(f"... and {len(stats['errors']) - 10} more.")
