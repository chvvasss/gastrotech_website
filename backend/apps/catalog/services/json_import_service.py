
import json
import logging
import hashlib
import requests
import uuid
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple

from django.core.cache import cache
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

logger = logging.getLogger(__name__)

class JsonImportService:
    """
    Service to handle JSON product data import via API.
    Supports Preview (validation) and Commit (save).
    """

    CACHE_TIMEOUT = 3600  # 1 hour for preview cache

    @classmethod
    def preview(cls, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate the JSON data and return a summary of what would happen.
        """
        service = cls(data, dry_run=True)
        return service.process()

    @classmethod
    def commit(cls, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute the import and save changes to DB.
        """
        service = cls(data, dry_run=False)
        return service.process()

    def __init__(self, data: List[Dict[str, Any]], dry_run: bool = False):
        self.data = data
        self.dry_run = dry_run
        self.stats = {
            "products_processed": 0,
            "products_created": 0,
            "products_updated": 0,
            "variants_created": 0,
            "variants_updated": 0,
            "images_processed": 0,
            "errors": [],
            "created_product_ids": [], # Track for undo
        }
        # Pre-cache lookups
        self.categories = {c.slug: c for c in Category.objects.all()}
        # self.series_map = {s.slug: s for s in Series.objects.all()} # Removed: Series are scoped provided by (category, slug)
        self.brands = {b.slug: b for b in Brand.objects.all()}
        # self.nodes = {n.slug: n for n in TaxonomyNode.objects.all()} # Removed: Nodes are scoped to series

    def process(self) -> Dict[str, Any]:
        try:
            with transaction.atomic():
                for index, item in enumerate(self.data):
                    try:
                        self._process_product(item, index)
                    except Exception as e:
                        error_msg = f"Item {index} ({item.get('slug', 'unknown')}): {str(e)}"
                        self.stats["errors"].append(error_msg)
                        # We continue processing to find all errors in preview, 
                        # but in commit mode we might want to stop? 
                        # For now, let's collect all errors.

                if self.stats["errors"] and not self.dry_run:
                    # If we have errors during commit, we should probably rollback?
                    # Or allow partial success?
                    # Let's enforce all-or-nothing for commit to be safe.
                    raise Exception(f"Import failed with {len(self.stats['errors'])} errors.")

                if self.dry_run:
                    # Always rollback in dry run
                    transaction.set_rollback(True)
        
        except Exception as e:
            if self.dry_run and "Import failed" not in str(e):
                 # Verify manual rollback didn't cause this
                 pass
            elif not self.dry_run:
                import traceback
                logger.error(f"Import transaction failed: {e}")
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "stats": self.stats,
                    "error": str(e)
                }

        return {
            "success": True if not self.stats["errors"] or self.dry_run else False,
            "stats": self.stats,
            "dry_run": self.dry_run,
            "dry_run_id": self._cache_data() if self.dry_run else None
        }

    def _cache_data(self) -> str:
        """Cache the data for subsequent commit."""
        key = str(uuid.uuid4())
        cache.set(f"json_import_{key}", self.data, self.CACHE_TIMEOUT)
        return key

    def _process_product(self, data: Dict[str, Any], index: int):
        self.stats["products_processed"] += 1
        
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
        if series_slug:
            # Series are unique per category, so we must filter by category AND slug
            series = Series.objects.filter(category=category, slug=series_slug).first()
            
            if not series:
                # User expects missing series to be created ("olmayanı oluşturmuyor mu")
                series_name = series_slug.replace("-", " ").title()
                # Try to get a better name from data if available, but usually it's not in the product JSON
                # unless we change the JSON structure. Using slug-derived name for now.
                
                series = Series.objects.create(
                    category=category,
                    slug=series_slug,
                    name=series_name,
                    description_short=f"{series_name} for {category.name}",
                    order=999, # Put at end by default
                    is_featured=False
                )
                self.stats["variants_created"] = self.stats.get("variants_created", 0) # Just to ensure key exists, though irrelevant here
                # We should probably track series_created in stats, but let's stick to existing keys or add logging
                logger.info(f"Auto-created missing series: {series_slug} in {category.name}")

        else:
            default_series_slug = f"{category_slug}-general"
            series = Series.objects.filter(category=category, slug=default_series_slug).first()
            
            if not series:
                # Create default series
                series = Series.objects.create(
                    category=category,
                    slug=default_series_slug,
                    name="General",
                    description_short=f"General products for {category.name}",
                    order=999,
                    is_featured=False
                )

        brand = self.brands.get(brand_slug)
        if not brand:
             raise ValueError(f"Brand not found: {brand_slug}")

        primary_node = None
        node_slug = data.get("primary_node")
        if node_slug:
            # Taxonomy nodes are scoped to the Series
            # We look for a node with this slug inside the current series
            primary_node = TaxonomyNode.objects.filter(series=series, slug=node_slug).first()
            
            if not primary_node:
                # Auto-create if missing ("olmayanı oluşturmuyor mu import mantığı")
                node_name = node_slug.replace("-", " ").title()
                primary_node = TaxonomyNode.objects.create(
                    series=series,
                    slug=node_slug,
                    name=node_name,
                    order=0
                )
                logger.info(f"Auto-created missing taxonomy node: {node_slug} in series {series.name}")

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
            self.stats["products_created"] += 1
            self.stats["created_product_ids"].append(str(product.id))
        else:
            self.stats["products_updated"] += 1

        # Variants
        variants_data = data.get("variants", [])
        if not variants_data:
            raise ValueError("Product must have at least one variant.")

        for v_data in variants_data:
            self._process_variant(product, v_data)

        # Images
        images_data = data.get("images", [])
        if images_data:
            self._process_images(product, images_data)

    def _process_variant(self, product: Product, data: Dict[str, Any]):
        model_code = data.get("model_code")
        if not model_code:
            raise ValueError("Variant missing 'model_code'.")

        defaults = {
            "product": product,
            "name_tr": data.get("name_tr", model_code),
            "name_en": data.get("name_en", ""),
            "sku": data.get("sku"),
            "dimensions": data.get("dimensions", ""),
            "weight_kg": self._parse_decimal(data.get("weight_kg")),
            "list_price": self._parse_decimal(data.get("list_price")),
            "price_override": self._parse_decimal(data.get("price_override")),
            "stock_qty": data.get("stock_qty"), 
            "specs": data.get("specs", {}),
        }

        variant, created = Variant.objects.update_or_create(
            model_code=model_code,
            defaults=defaults
        )
        
        if created:
            self.stats["variants_created"] += 1
        else:
            self.stats["variants_updated"] += 1

    def _process_images(self, product: Product, images_data: List[Dict[str, Any]]):
        logger.info(f"Processing images for product {product.slug}")
        # Only process images in commit mode (expensive/slow in dry run?)
        # Or maybe check existence in dry run but don't download?
        # Let's skip download in dry-run for speed.
        if self.dry_run:
            return

        existing_links = {pm.media.filename: pm for pm in product.product_media.select_related('media').all()}
        
        for img_data in images_data:
            if isinstance(img_data, str):
                 url_or_path = img_data
                 is_primary = False
                 order = 0
                 alt = ""
            else:
                url_or_path = img_data.get("url")
                is_primary = img_data.get("is_primary", False)
                order = img_data.get("sort_order", 0)
                alt = img_data.get("alt", "")

            if not url_or_path:
                continue
            
            filename = self._get_filename(url_or_path)

            if filename in existing_links:
                pm = existing_links[filename]
                pm.is_primary = is_primary
                pm.sort_order = order
                pm.alt = alt
                pm.save()
                continue
            
            media_content = self._fetch_image_content(url_or_path)
            if not media_content:
                continue

            file_hash = hashlib.sha256(media_content).hexdigest()
            media = Media.objects.filter(checksum_sha256=file_hash).first()
            
            if not media:
                media = Media(
                    kind=Media.Kind.IMAGE,
                    filename=filename,
                    content_type="image/jpeg", 
                    bytes=media_content
                )
                media.save()
                self.stats["images_processed"] += 1

            ProductMedia.objects.create(
                product=product,
                media=media,
                is_primary=is_primary,
                sort_order=order,
                alt=alt
            )

    def _get_filename(self, path: str) -> str:
        import os
        filename = os.path.basename(path)
        if path.startswith("http"):
             if "?" in filename:
                 filename = filename.split("?")[0]
        return filename

    def _fetch_image_content(self, path: str) -> Optional[bytes]:
        import os
        try:
            if path.startswith("http"):
                response = requests.get(path, timeout=10)
                if response.status_code == 200:
                    return response.content
            else:
                if path.startswith("file:///"):
                     path = path[8:]
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        return f.read()
        except Exception as e:
            logger.error(f"Failed to fetch image from {path}: {e}")
            pass
        return None

    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
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
