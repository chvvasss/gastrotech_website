import logging
import pandas as pd
from django.db import transaction
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from apps.catalog.models import (
    Brand,
    Category,
    Series,
    TaxonomyNode,
    Product,
    Variant,
    SpecKey,
)
from apps.common.slugify_tr import slugify_tr

logger = logging.getLogger(__name__)


class BulkUploadService:
    """
    Service to handle bulk product uploads via Excel.
    
    Process:
    1. Parse and validate Excel structure
    2. Validate data integrity (required fields, types)
    3. Dry run: Check what would be created/updated
    4. Execute: Perform actual database operations
    """

    REQUIRED_COLUMNS = [
        "Brand",
        "Category",
        "Series",
        "Product Name",
        "Model Code",
        "Title TR",
    ]

    def __init__(self, file, product_status="active"):
        self.file = file
        self.errors = []
        self.df = None
        self.product_status = product_status
        logger.info(f"BulkUploadService initialized with product_status={product_status}")

    def validate_and_parse(self):
        """Parse Excel and validate structure."""
        logger.info("Starting Excel validation and parsing")
        try:
            self.df = pd.read_excel(self.file)
            logger.info(f"Successfully parsed Excel file with {len(self.df)} rows")
        except Exception as e:
            logger.error(f"Failed to parse Excel file: {e}")
            raise ValidationError(f"Invalid Excel file: {str(e)}")

        # Check required columns
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in self.df.columns]
        if missing_columns:
            error_msg = f"Missing required columns: {', '.join(missing_columns)}"
            logger.error(error_msg)
            raise ValidationError(error_msg)

        # Basic data validation
        if self.df.empty:
            logger.error("Excel file is empty")
            raise ValidationError("Excel file is empty")

        logger.info(f"Found columns: {list(self.df.columns)}")
        return self.df

    def process_data(self, dry_run=True):
        """
        Process the dataframe and create/update catalog entries.
        
        Returns:
            dict: Summary of operations (created, updated, errors)
        """
        if self.df is None:
            self.validate_and_parse()

        logger.info(f"Processing data (dry_run={dry_run})")
        
        results = {
            "categories_created": 0,
            "series_created": 0,
            "brands_created": 0,
            "products_created": 0,
            "products_updated": 0,
            "variants_created": 0,
            "variants_updated": 0,
            "errors": [],
            "rows_processed": 0,
        }

        try:
            with transaction.atomic():
                self._execute_process(results)
                
                if dry_run:
                    logger.info("Dry run mode - rolling back transaction")
                    # Rollback transaction in dry_run to simulate but not save
                    transaction.set_rollback(True)
                else:
                    logger.info("Real mode - committing transaction")
                    
        except Exception as e:
            error_msg = f"Global Error during processing: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results["errors"].append(error_msg)

        logger.info(f"Processing complete: {results['rows_processed']} rows processed, {len(results['errors'])} errors")
        return results

    def _execute_process(self, results):
        """Iterate rows and process them."""
        logger.info(f"Executing process for {len(self.df)} rows")
        
        for index, row in self.df.iterrows():
            row_num = index + 2  # Excel row number (1-based header + 1)
            logger.debug(f"Processing row {row_num}")
            
            try:
                # 1. Brand - Try name first, then slug
                brand_name = self._get_clean_value(row, "Brand")
                if not brand_name:
                    error_msg = f"Row {row_num}: Missing Brand"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
                    continue
                
                # First try to find by case-insensitive name
                try:
                    brand = Brand.objects.get(name__iexact=brand_name)
                    logger.debug(f"Row {row_num}: Found existing brand '{brand_name}'")
                except Brand.DoesNotExist:
                    # Create new with slug
                    brand_slug = slugify_tr(brand_name)
                    brand, created = Brand.objects.get_or_create(
                        slug=brand_slug,
                        defaults={"name": brand_name}
                    )
                    if created:
                        results["brands_created"] += 1
                        logger.debug(f"Row {row_num}: Created brand '{brand_name}'")

                # 2. Category - Try name first, then slug
                category_name = self._get_clean_value(row, "Category")
                if not category_name:
                    error_msg = f"Row {row_num}: Missing Category"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
                    continue

                # First try to find by case-insensitive name
                try:
                    category = Category.objects.get(name__iexact=category_name)
                    logger.debug(f"Row {row_num}: Found existing category '{category_name}'")
                except Category.DoesNotExist:
                    # Create new with slug
                    category_slug = slugify_tr(category_name)
                    category, created = Category.objects.get_or_create(
                        slug=category_slug,
                        defaults={"name": category_name}
                    )
                    if created:
                        results["categories_created"] += 1
                        logger.debug(f"Row {row_num}: Created category '{category_name}'")

                # 3. Series - Try name first, then slug
                series_name = self._get_clean_value(row, "Series")
                if not series_name:
                    error_msg = f"Row {row_num}: Missing Series"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
                    continue

                # First try to find by case-insensitive name
                try:
                    series = Series.objects.get(name__iexact=series_name)
                    logger.debug(f"Row {row_num}: Found existing series '{series_name}'")
                    # Update category if different
                    if series.category != category:
                        logger.info(f"Row {row_num}: Updating series '{series_name}' category to '{category_name}'")
                        series.category = category
                        series.save()
                except Series.DoesNotExist:
                    # Create new with slug
                    series_slug = slugify_tr(series_name)
                    series, created = Series.objects.get_or_create(
                        slug=series_slug,
                        defaults={
                            "name": series_name,
                            "category": category
                        }
                    )
                    if created:
                        results["series_created"] += 1
                        logger.debug(f"Row {row_num}: Created series '{series_name}'")

                # 4. Taxonomy (Optional)
                taxonomy_path = self._get_clean_value(row, "Taxonomy")
                primary_node = None
                if taxonomy_path:
                    try:
                        primary_node = self._get_or_create_taxonomy(series, taxonomy_path)
                        logger.debug(f"Row {row_num}: Set taxonomy to '{taxonomy_path}'")
                    except Exception as e:
                        logger.warning(f"Row {row_num}: Failed to create taxonomy '{taxonomy_path}': {e}")

                # 5. Product
                product_name = self._get_clean_value(row, "Product Name")
                if not product_name:
                    error_msg = f"Row {row_num}: Missing Product Name"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
                    continue
                
                product_slug = slugify_tr(product_name)
                title_tr = self._get_clean_value(row, "Title TR") or product_name
                title_en = self._get_clean_value(row, "Title EN") or ""
                
                # Determine product status
                status = getattr(Product.Status, self.product_status.upper(), Product.Status.ACTIVE)
                
                product, created = Product.objects.update_or_create(
                    slug=product_slug,
                    defaults={
                        "name": product_name,
                        "series": series,
                        "brand": brand,
                        "primary_node": primary_node,
                        "title_tr": title_tr,
                        "title_en": title_en,
                        "status": status,
                    }
                )
                if created:
                    results["products_created"] += 1
                    logger.debug(f"Row {row_num}: Created product '{product_name}'")
                else:
                    results["products_updated"] += 1
                    logger.debug(f"Row {row_num}: Updated product '{product_name}'")

                # 6. Variant
                model_code = self._get_clean_value(row, "Model Code")
                if not model_code:
                    error_msg = f"Row {row_num}: Missing Model Code"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
                    continue

                variant_defaults = {
                    "product": product,
                    "name_tr": title_tr,
                    "name_en": title_en,
                    "dimensions": self._get_clean_value(row, "Dimensions") or "",
                    "weight_kg": self._parse_decimal(row.get("Weight")),
                    "list_price": self._parse_decimal(row.get("Price")),
                }

                # Handle dynamic specs
                specs = {}
                for col in self.df.columns:
                    if col.startswith("Spec:"):
                        key = col.replace("Spec:", "").strip()
                        key_slug = slugify_tr(key)
                        value = self._get_clean_value(row, col)
                        if value:
                            specs[key_slug] = value
                
                variant_defaults["specs"] = specs

                variant, created = Variant.objects.update_or_create(
                    model_code=model_code,
                    defaults=variant_defaults
                )
                
                if created:
                    results["variants_created"] += 1
                    logger.debug(f"Row {row_num}: Created variant '{model_code}'")
                else:
                    results["variants_updated"] += 1
                    logger.debug(f"Row {row_num}: Updated variant '{model_code}'")
                
                results["rows_processed"] += 1

            except Exception as e:
                error_msg = f"Row {row_num}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                results["errors"].append(error_msg)

    def _get_or_create_taxonomy(self, series, path_str):
        """
        Create hierarchy: 'Ocaklar > Gazlı'
        """
        parts = [p.strip() for p in path_str.split(">") if p.strip()]
        parent = None
        current_node = None
        
        for part in parts:
            node_slug = slugify_tr(part)
            current_node, _ = TaxonomyNode.objects.get_or_create(
                series=series,
                slug=node_slug,
                defaults={
                    "name": part,
                    "parent": parent
                }
            )
            parent = current_node
            
        return current_node

    def _get_clean_value(self, row, column_name):
        """Get a clean string value from a row, handling NaN and empty strings."""
        value = row.get(column_name, "")
        
        # Handle pandas NaN
        if pd.isna(value):
            return None
            
        # Convert to string and strip
        value_str = str(value).strip()
        
        # Handle empty strings and string "nan"
        if not value_str or value_str.lower() == "nan":
            return None
            
        return value_str

    def _parse_decimal(self, value):
        """Parse decimal value safely."""
        if pd.isna(value) or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
