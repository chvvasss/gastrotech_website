"""
Unified Import Service for Gastrotech Catalog.

Two-phase import system:
1. validate() - Dry-run with comprehensive report generation
2. commit() - Execute import with transaction safety

Supports:
- Multi-sheet Excel (Products + Variants sheets)
- Flexible column mapping (exact + alias support)
- Smart mode: missing entity candidate creation with dedup
- Strict mode: blocking errors on missing refs
- Idempotent upsert by slug/model_code
- XLSX report generation with multiple sheets
"""

import hashlib
import json
import logging
import uuid
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.catalog.models import (
    Category, Series, Brand, BrandCategory, Product, Variant, SpecKey, Media
)
from apps.ops.models import ImportJob, AuditLog
from apps.common.canonical import canonical_slug, normalize_empty_value

# Backward compatibility alias
slugify_tr = canonical_slug

logger = logging.getLogger(__name__)


# V5 TEMPLATE CONTRACT - Column mappings
# Canonical V5 column names come FIRST, legacy aliases follow for backward compatibility
PRODUCTS_COLUMN_MAP = {
    'brand_slug': ['Brand', 'brand', 'Brand Slug', 'brand_slug', 'Marka'],
    'category_slug': ['Category', 'category', 'Category Slug', 'category_slug', 'Kategori'],
    'series_slug': ['Series', 'series', 'Series Slug', 'series_slug', 'Seri'],
    'name': ['Product Name', 'product_name', 'name', 'Ürün Adı'],
    'slug': ['Product Slug', 'product_slug', 'slug', 'Slug'],
    'title_tr': ['Title TR', 'title_tr'],
    'title_en': ['Title EN', 'title_en'],
    'status': ['Status', 'status', 'Durum'],
    'is_featured': ['Is Featured', 'is_featured', 'Öne Çıkan'],
    'long_description': ['Long Description', 'long_description', 'Uzun Açıklama'],
    'general_features': ['General Features', 'general_features', 'Genel Özellikler'],
    'short_specs': ['Short Specs', 'short_specs', 'Kısa Özellikler'],
    'taxonomy': ['Taxonomy', 'taxonomy', 'Taksonomi'],
}

VARIANTS_COLUMN_MAP = {
    'product_slug': ['Product Slug', 'product_slug', 'Ürün Slug'],
    'model_code': ['Model Code', 'model_code', 'Model Kodu'],
    'name_tr': ['Variant Name TR', 'Variant Name', 'name_tr', 'Varyant Adı'],
    'name_en': ['Variant Name EN', 'Variant Name (EN)', 'name_en'],
    'sku': ['SKU', 'sku'],
    'dimensions': ['Dimensions', 'dimensions', 'Boyutlar'],
    'weight_kg': ['Weight', 'weight_kg', 'Weight (kg)', 'Ağırlık'],
    'list_price': ['List Price', 'list_price', 'Price', 'Fiyat'],
    'stock_qty': ['Stock Qty', 'stock_qty', 'Stock', 'Stok'],
}

# V5 REQUIRED FIELDS (per template contract)
PRODUCTS_REQUIRED = [
    'brand_slug',     # Brand
    'category_slug',  # Category
    'series_slug',    # Series
    'name',           # Product Name
    'slug',           # Product Slug
    'title_tr',       # Title TR
]

VARIANTS_REQUIRED = [
    'product_slug',   # Product Slug
    'model_code',     # Model Code
    # NOTE: name_tr/name_en are NOT required - they default to Product.title_tr/title_en
]


class UnifiedImportService:
    """
    Production-grade import service for catalog data.

    Features:
    - Two-phase: validate (dry-run) → commit (execute)
    - Multi-sheet Excel support (Products + Variants)
    - Flexible column mapping with aliases
    - Comprehensive validation with row/column error tracking
    - Smart mode: missing entity candidate detection with dedup
    - Idempotent: same input → same result
    - Transaction-safe: all-or-nothing commits
    """

    EMPTY_VALUES = {'', '-', '—', 'nan', 'NaN', 'null', 'NULL', 'None', '#N/A'}

    def __init__(self, mode: str = 'strict'):
        self.mode = mode
        self.report = self._init_report()
        self._seen_candidates: Dict[str, Set[str]] = {
            'categories': set(),
            'series': set(),
            'brands': set(),
            'products': set(),
        }

        # V5: Load entity caches for validation (lazy-load on first use)
        self._category_cache = None
        self._series_cache = None
        self._brand_cache = None

    def _load_caches(self):
        """Lazy-load entity caches for validation."""
        if self._category_cache is None:
            self._category_cache = {c.slug: c for c in Category.objects.all()}
            logger.info(f"[CACHE] Loaded {len(self._category_cache)} categories")

        if self._series_cache is None:
            self._series_cache = {s.slug: s for s in Series.objects.select_related('category').all()}
            logger.info(f"[CACHE] Loaded {len(self._series_cache)} series")

        if self._brand_cache is None:
            self._brand_cache = {b.slug: b for b in Brand.objects.all()}
            logger.info(f"[CACHE] Loaded {len(self._brand_cache)} brands")

    def _init_report(self) -> Dict[str, Any]:
        return {
            'status': 'pending',
            'issues': [],
            'candidates': {
                'categories': [],
                'series': [],
                'brands': [],
                'products': [],
            },
            'normalization': {
                'merged_continuation_rows': [],
                'disambiguated_model_codes': [],
                'empty_value_normalizations': 0,
            },
            'counts': {
                'total_product_rows': 0,
                'total_variant_rows': 0,
                'valid_product_rows': 0,
                'valid_variant_rows': 0,
                'error_rows': 0,
                'warning_rows': 0,
                'products_to_create': 0,
                'products_to_update': 0,
                'variants_to_create': 0,
                'variants_to_update': 0,
            },
            'products_data': [],
            'variants_data': [],
            'valid_rows': [],
        }

    def validate(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Phase 1: Validate import file with dry-run.

        Returns comprehensive report with:
        - Issues (errors/warnings with row/col/value)
        - Candidates (missing entities to create in smart mode)
        - valid_rows for commit phase
        """
        logger.info(f"[VALIDATE] Starting validation for {filename} ({len(file_bytes)} bytes)")

        try:
            products_df, variants_df = self._load_dataframes(file_bytes, filename)
            
            self.report['counts']['total_product_rows'] = len(products_df) if products_df is not None else 0
            self.report['counts']['total_variant_rows'] = len(variants_df) if variants_df is not None else 0

            if products_df is not None:
                products_df = self._normalize_empty_values(products_df, 'products')
                self._validate_products_sheet(products_df)

            if variants_df is not None:
                variants_df = self._normalize_empty_values(variants_df, 'variants')
                variants_df = self._disambiguate_duplicate_model_codes(variants_df)
                self._validate_variants_sheet(variants_df)

            self._analyze_upsert_operations()

            error_count = sum(1 for i in self.report['issues'] if i.get('severity') == 'error')
            warning_count = sum(1 for i in self.report['issues'] if i.get('severity') == 'warning')
            
            self.report['counts']['error_rows'] = error_count
            self.report['counts']['warning_rows'] = warning_count

            if error_count > 0:
                self.report['status'] = 'failed_validation'
            elif warning_count > 0:
                self.report['status'] = 'validation_warnings'
            else:
                self.report['status'] = 'validation_passed'

            logger.info(
                f"[VALIDATE] Complete: {len(self.report['valid_rows'])} valid rows, "
                f"{error_count} errors, {warning_count} warnings"
            )

            # CRITICAL: Create immutable snapshot for deterministic commit
            self._create_snapshot()

            return self.report

        except Exception as e:
            logger.exception(f"[VALIDATE] Fatal error during validation")
            self.report['status'] = 'validation_fatal_error'
            self.report['issues'].append({
                'row': None,
                'column': None,
                'value': None,
                'severity': 'error',
                'code': 'fatal_error',
                'message': f"Fatal error during validation: {str(e)}",
                'expected': None,
            })
            return self.report

    def _create_snapshot(self):
        """
        Create immutable snapshot for deterministic commit.

        CRITICAL: This ensures validate() preview = commit() result guarantee.
        Snapshot is stored in Media with SHA-256 hash for integrity verification.
        """
        # Build canonical snapshot data
        snapshot_data = {
            'products_data': self.report['products_data'],
            'variants_data': self.report['variants_data'],
            'candidates': self.report['candidates'],
            'normalization': self.report['normalization'],
            'metadata': {
                'validated_at': timezone.now().isoformat(),
                'mode': self.mode,
                'version': '1.0',
            },
        }

        # Custom encoder for Decimal and other non-standard types
        class DecimalEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Decimal):
                    return str(obj)
                return super().default(obj)

        # Serialize to canonical JSON (deterministic formatting)
        snapshot_json = json.dumps(
            snapshot_data,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,  # Deterministic key ordering
            cls=DecimalEncoder
        )

        # Compute SHA-256 hash
        snapshot_hash = hashlib.sha256(snapshot_json.encode('utf-8')).hexdigest()
        snapshot_bytes = snapshot_json.encode('utf-8')

        # Store in Media
        snapshot_media = Media.objects.create(
            kind='file',
            filename=f'import_snapshot_{uuid.uuid4()}.json',
            content_type='application/json',
            bytes=snapshot_bytes,
            size_bytes=len(snapshot_bytes),
            checksum_sha256=snapshot_hash,
        )

        # Add snapshot info to report (for API response)
        self.report['snapshot'] = {
            'media_id': str(snapshot_media.id),
            'hash': snapshot_hash,
            'size_bytes': len(snapshot_bytes),
            'created_at': snapshot_media.created_at.isoformat(),
        }

        logger.info(
            f"[SNAPSHOT] Created snapshot {snapshot_media.id} "
            f"(hash={snapshot_hash[:16]}..., size={len(snapshot_bytes)} bytes)"
        )

    def commit(self, job_id: str, allow_partial: bool = False) -> Dict[str, Any]:
        """
        Phase 2: Execute import with transaction safety.

        CRITICAL: Loads from snapshot_file (immutable) NOT report_json (mutable).
        This ensures deterministic behavior: validate() preview = commit() result.
        """
        logger.info(f"[COMMIT] Starting commit for job {job_id}, allow_partial={allow_partial}")

        job = ImportJob.objects.get(id=job_id)

        if job.status not in ['pending', 'partial', 'validating']:
            raise ValueError(f"Job {job_id} is in invalid state for commit: {job.status}")

        # CRITICAL: Load from snapshot (immutable), NOT report_json
        if not job.snapshot_file:
            raise ValueError(
                f"Job {job_id} has no snapshot. Must run validate() first."
            )

        # Verify snapshot integrity
        snapshot_content = job.snapshot_file.bytes.decode('utf-8')
        actual_hash = hashlib.sha256(snapshot_content.encode('utf-8')).hexdigest()

        if actual_hash != job.snapshot_hash:
            raise ValueError(
                f"Snapshot integrity check FAILED for job {job_id}. "
                f"Expected hash {job.snapshot_hash}, got {actual_hash}. "
                f"Snapshot may have been tampered with."
            )

        logger.info(f"[COMMIT] Snapshot integrity verified: {actual_hash[:16]}...")

        # Load snapshot data (canonical source of truth)
        snapshot = json.loads(snapshot_content)
        products_data = snapshot.get('products_data', [])
        variants_data = snapshot.get('variants_data', [])
        candidates = snapshot.get('candidates', {})

        # Check validation status from report_json (for compatibility)
        report = job.report_json
        if report.get('status') == 'failed_validation' and not allow_partial:
            raise ValidationError(
                f"Job {job_id} has validation errors. Set allow_partial=True to commit valid rows only."
            )

        if not products_data and not variants_data:
            raise ValueError(f"Job {job_id} has no valid data to import")

        try:
            with transaction.atomic():
                job.status = 'running'
                job.started_at = timezone.now()
                job.save(update_fields=['status', 'started_at'])

                # V5: Track created entities for db_verify
                created_categories = []
                created_brands = []
                created_series = []
                created_products = []
                updated_products = []
                created_variants = []
                updated_variants = []

                # Create missing entities in smart mode (from snapshot, not report_json)
                if job.mode == 'smart':
                    created_categories, created_brands, created_series = self._create_candidates(candidates)

                for p_data in products_data:
                    try:
                        product, created = self._upsert_product_from_data(p_data)
                        if created:
                            created_products.append(product.slug)
                        else:
                            updated_products.append(product.slug)
                    except Exception as e:
                        logger.error(f"[COMMIT] Error upserting product {p_data.get('slug')}: {e}")
                        if not allow_partial:
                            raise

                for v_data in variants_data:
                    try:
                        variant, created = self._upsert_variant_from_data(v_data)
                        if created:
                            created_variants.append(variant.model_code)
                        else:
                            updated_variants.append(variant.model_code)
                    except Exception as e:
                        logger.error(f"[COMMIT] Error upserting variant {v_data.get('model_code')}: {e}")
                        if not allow_partial:
                            raise

                job.created_count = len(created_variants) + len(created_products)
                job.updated_count = len(updated_variants) + len(updated_products)
                job.skipped_count = 0
                job.error_count = report.get('counts', {}).get('error_rows', 0)
                job.status = 'success' if job.error_count == 0 else 'partial'
                job.completed_at = timezone.now()
                job.is_preview = False
                job.save()

                AuditLog.log(
                    action='import_apply',
                    entity_type='import_job',
                    entity_id=str(job.id),
                    entity_label=f"Import {job.get_kind_display()}",
                    actor=job.created_by,
                    metadata={
                        'mode': job.mode,
                        'created_products': len(created_products),
                        'updated_products': len(updated_products),
                        'created_variants': len(created_variants),
                        'updated_variants': len(updated_variants),
                    },
                )

                # V5: Comprehensive DB verification (all created entities)
                db_verify = self._verify_db_write(
                    created_categories,
                    created_brands,
                    created_series,
                    created_products,
                    created_variants,
                )

                logger.info(
                    f"[COMMIT] Complete for job {job_id}: "
                    f"{len(created_categories)} categories, {len(created_brands)} brands, {len(created_series)} series, "
                    f"{len(created_products)} products created ({len(updated_products)} updated), "
                    f"{len(created_variants)} variants created ({len(updated_variants)} updated)"
                )

                if not db_verify['created_entities_found_in_db']:
                    logger.error(
                        f"[COMMIT] DB VERIFY FAILED for job {job_id}! "
                        f"Some created entities not found in DB. Details: {db_verify['verification_details']}"
                    )

                return {
                    'status': 'success',
                    'job_id': str(job.id),
                    'counts': {
                        'categories_created': len(created_categories),
                        'brands_created': len(created_brands),
                        'series_created': len(created_series),
                        'products_created': len(created_products),
                        'products_updated': len(updated_products),
                        'variants_created': len(created_variants),
                        'variants_updated': len(updated_variants),
                    },
                    'db_verify': db_verify,
                }

        except Exception as e:
            logger.exception(f"[COMMIT] Error during commit for job {job_id}")
            job.status = 'failed'
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'completed_at'])
            raise

    def _load_dataframes(self, file_bytes: bytes, filename: str) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Load Excel/CSV file into DataFrames. Supports multi-sheet Excel."""
        import io
        
        products_df = None
        variants_df = None

        if filename.endswith('.csv'):
            # Try UTF-8 first, then CP1254 (Turkish), then Latin-1
            encodings = ['utf-8', 'cp1254', 'latin1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), delimiter=';', dtype=str, encoding=encoding)
                    logger.info(f"[LOAD] Loaded CSV with {len(df)} rows using {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"[LOAD] Failed to read CSV with {encoding}: {e}")
                    continue
            
            if df is None:
                # Fallback to loose UTF-8 decoding if all else fails
                 try:
                    df = pd.read_csv(io.BytesIO(file_bytes), delimiter=';', dtype=str, encoding='utf-8', encoding_errors='replace')
                    logger.warning(f"[LOAD] Loaded CSV with {len(df)} rows using utf-8-replace (some characters may be corrupted)")
                 except Exception as e:
                    raise ValueError(f"Could not read CSV file. Please ensure it is encoded in UTF-8 or CP1254. Error: {str(e)}")

            df.columns = df.columns.str.strip()
            variants_df = df
        elif filename.endswith(('.xlsx', '.xls')):
            sheets = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, dtype=str)
            
            for sheet_name, df in sheets.items():
                df.columns = df.columns.str.strip()
                sheet_lower = sheet_name.lower()
                
                if 'product' in sheet_lower and 'variant' not in sheet_lower:
                    products_df = df
                    logger.info(f"[LOAD] Found Products sheet '{sheet_name}' with {len(df)} rows")
                elif 'variant' in sheet_lower:
                    variants_df = df
                    logger.info(f"[LOAD] Found Variants sheet '{sheet_name}' with {len(df)} rows")
            
            if products_df is None and variants_df is None:
                first_sheet_name = list(sheets.keys())[0]
                variants_df = sheets[first_sheet_name]
                logger.info(f"[LOAD] No Products/Variants sheets found, using first sheet '{first_sheet_name}'")
        else:
            raise ValueError(f"Unsupported file format: {filename}")

        return products_df, variants_df

    def _normalize_empty_values(self, df: pd.DataFrame, sheet_type: str) -> pd.DataFrame:
        """Normalize empty values (-, nan, null) to None."""
        original_nulls = df.isnull().sum().sum()
        df = df.replace(self.EMPTY_VALUES, np.nan)
        new_nulls = df.isnull().sum().sum()
        self.report['normalization']['empty_value_normalizations'] += int(new_nulls - original_nulls)
        return df

    def _map_column(self, df: pd.DataFrame, target: str, mapping: Dict) -> Optional[str]:
        """Find matching column in DataFrame using mapping."""
        aliases = mapping.get(target, [target])
        for alias in aliases:
            if alias in df.columns:
                return alias
        return None

    def _get_mapped_value(self, row: pd.Series, target: str, mapping: Dict, df: pd.DataFrame) -> Any:
        """Get value from row using column mapping."""
        col = self._map_column(df, target, mapping)
        if col and col in row.index:
            val = row.get(col)
            if pd.isna(val):
                return None
            return str(val).strip()
        return None

    def _validate_products_sheet(self, df: pd.DataFrame):
        """Validate Products sheet and populate products_data."""
        # Load caches for validation
        self._load_caches()

        # V5 CONTRACT: Check for required columns (using PRODUCTS_REQUIRED constant)
        missing_required_cols = []
        for field in PRODUCTS_REQUIRED:
            # Map internal field name to possible column names in Excel
            if field == 'brand_slug':
                col_key = 'brand_slug'
            elif field == 'category_slug':
                col_key = 'category_slug'
            elif field == 'series_slug':
                col_key = 'series_slug'
            elif field == 'name':
                col_key = 'name'
            elif field == 'slug':
                col_key = 'slug'
            elif field == 'title_tr':
                col_key = 'title_tr'
            else:
                col_key = field

            if not self._map_column(df, col_key, PRODUCTS_COLUMN_MAP):
                # Allow 'name' fallback for 'slug' generation
                if field == 'slug' and self._map_column(df, 'name', PRODUCTS_COLUMN_MAP):
                    continue
                missing_required_cols.append(field)

        if missing_required_cols:
            expected_cols = []
            for field in missing_required_cols:
                if field == 'brand_slug':
                    expected_cols.append('Brand')
                elif field == 'category_slug':
                    expected_cols.append('Category')
                elif field == 'series_slug':
                    expected_cols.append('Series')
                elif field == 'name':
                    expected_cols.append('Product Name')
                elif field == 'slug':
                    expected_cols.append('Product Slug')
                elif field == 'title_tr':
                    expected_cols.append('Title TR')
                else:
                    expected_cols.append(field)

            self.report['issues'].append({
                'row': 0,
                'column': ', '.join(expected_cols),
                'value': None,
                'severity': 'error',
                'code': 'missing_required_columns',
                'message': f"Products sheet missing required columns: {', '.join(expected_cols)}",
                'expected': f"Required columns: {', '.join(expected_cols)}",
            })
            return

        # Row-level validation
        for idx, row in df.iterrows():
            row_num = idx + 2
            row_data = {}
            row_issues = []

            # V5: Extract slug and name (with backward compatibility)
            slug_val = self._get_mapped_value(row, 'slug', PRODUCTS_COLUMN_MAP, df)
            name_val = self._get_mapped_value(row, 'name', PRODUCTS_COLUMN_MAP, df)

            # Generate slug from name if not provided
            if not slug_val and name_val:
                slug_val = slugify_tr(name_val)

            if not slug_val:
                row_issues.append({
                    'row': row_num,
                    'column': 'Product Slug',
                    'value': None,
                    'severity': 'error',
                    'code': 'required_field_missing',
                    'message': 'Product Slug is required (can be auto-generated from Product Name)',
                    'expected': 'Non-empty slug value or Product Name to generate from',
                })
                self.report['issues'].extend(row_issues)
                continue

            row_data['slug'] = slug_val
            row_data['name'] = name_val or slug_val

            # V5: Title TR is REQUIRED
            title_tr_val = self._get_mapped_value(row, 'title_tr', PRODUCTS_COLUMN_MAP, df)
            if not title_tr_val:
                # Fallback to name if title_tr missing (for backward compatibility)
                title_tr_val = name_val or slug_val
            row_data['title_tr'] = title_tr_val

            # V5: Title EN is optional
            row_data['title_en'] = self._get_mapped_value(row, 'title_en', PRODUCTS_COLUMN_MAP, df) or ''

            # V5: Brand is OPTIONAL (can be blank/NULL)
            brand_val = self._get_mapped_value(row, 'brand_slug', PRODUCTS_COLUMN_MAP, df)
            if brand_val:
                row_data['brand_slug'] = brand_val
                row_data['brand_name'] = brand_val  # Store for display

                # Check if brand exists in DB (use cache)
                brand_obj = self._brand_cache.get(brand_val)
                if not brand_obj:
                    self._add_brand_candidate(brand_val, brand_val, row_num)
            else:
                # Brand is blank - this is OK, product will have brand=NULL
                row_data['brand_slug'] = None
                row_data['brand_name'] = None

            # V5: Category is REQUIRED
            # Check for taxonomy path first (hierarchical), then category_slug (flat)
            taxonomy_val = self._get_mapped_value(row, 'taxonomy', PRODUCTS_COLUMN_MAP, df)
            category_val = self._get_mapped_value(row, 'category_slug', PRODUCTS_COLUMN_MAP, df)

            # Determine if we're using hierarchical path
            raw_category_path = taxonomy_val or category_val
            is_hierarchical = bool(taxonomy_val) or (category_val and ('/' in category_val or '>' in category_val))

            if not raw_category_path:
                row_issues.append({
                    'row': row_num,
                    'column': 'Category/Taxonomy',
                    'value': None,
                    'severity': 'error',
                    'code': 'required_field_missing',
                    'message': 'Category or Taxonomy is required',
                    'expected': 'Category slug or taxonomy path (e.g., "electronics" or "Fırınlar > Pizza Fırını")',
                })
            else:
                # Check if series is provided (affects series_mode for new categories)
                series_val = self._get_mapped_value(row, 'series_slug', PRODUCTS_COLUMN_MAP, df)
                has_series = bool(series_val)

                if is_hierarchical:
                    # Handle hierarchical category path
                    leaf_category = self._add_hierarchical_category_candidate(
                        raw_category_path,
                        row_num,
                        has_series=has_series,
                        treat_slash_as_hierarchy=True,  # TODO: Make this configurable
                    )
                    if leaf_category:
                        row_data['category_slug'] = leaf_category.slug
                        row_data['category_name'] = leaf_category.name
                        row_data['category_id'] = str(leaf_category.id)
                    else:
                        # Will be created during commit - use leaf segment slug for now
                        from apps.ops.services.taxonomy_parser import parse_category_path
                        segments = parse_category_path(raw_category_path, treat_slash_as_hierarchy=True)
                        if segments:
                            leaf_segment = segments[-1]
                            row_data['category_slug'] = leaf_segment.slug
                            row_data['category_name'] = leaf_segment.name
                        else:
                            row_data['category_slug'] = slugify_tr(raw_category_path)
                            row_data['category_name'] = raw_category_path
                    row_data['taxonomy_path'] = raw_category_path
                else:
                    # Handle flat category slug
                    row_data['category_slug'] = category_val
                    row_data['category_name'] = category_val

                    # Check if category exists in DB (use cache)
                    category_obj = self._category_cache.get(category_val)
                    if not category_obj:
                        self._add_category_candidate(category_val, category_val, row_num)

            # V5: Series is REQUIRED
            series_val = self._get_mapped_value(row, 'series_slug', PRODUCTS_COLUMN_MAP, df)
            if not series_val:
                row_issues.append({
                    'row': row_num,
                    'column': 'Series',
                    'value': None,
                    'severity': 'error',
                    'code': 'required_field_missing',
                    'message': 'Series is required',
                    'expected': 'Series slug (e.g., premium-series, eco-line)',
                })
            else:
                row_data['series_slug'] = series_val
                row_data['series_name'] = series_val

                # Check if series exists in DB (use cache)
                series_obj = self._series_cache.get(series_val)
                if not series_obj:
                    # Series doesn't exist - add candidate
                    self._add_series_candidate(series_val, series_val, row_num, df, row)
                else:
                    # V5.1: Series-Category mismatch validation (with hierarchical support)
                    # Series category can be an ANCESTOR of the product's category
                    if category_val:
                        if series_obj.category.slug == category_val:
                            # Exact match
                            row_data['series_category_match_type'] = 'exact'
                        else:
                            # Check if series category is ancestor of product category
                            is_valid, match_type = self._is_category_ancestor_of(
                                series_obj.category.slug,
                                category_val
                            )
                            row_data['series_category_match_type'] = match_type
                            
                            if not is_valid:
                                row_issues.append({
                                    'row': row_num,
                                    'column': 'Series / Category',
                                    'value': f"Series={series_val}, Category={category_val}",
                                    'severity': 'error',
                                    'code': 'series_category_mismatch',
                                    'message': f"Series '{series_val}' belongs to category '{series_obj.category.slug}' which is not an ancestor of '{category_val}'",
                                    'expected': f"Category '{series_obj.category.slug}' or one of its descendants",
                                })
                    else:
                        row_data['series_category_match_type'] = 'exact'

            # V5: Status defaults to 'active'
            status_val = self._get_mapped_value(row, 'status', PRODUCTS_COLUMN_MAP, df)
            row_data['status'] = self._parse_status(status_val) or 'active'

            # V5: Is Featured is optional
            is_featured_val = self._get_mapped_value(row, 'is_featured', PRODUCTS_COLUMN_MAP, df)
            row_data['is_featured'] = self._parse_bool(is_featured_val)

            # V5: Optional fields
            row_data['long_description'] = self._get_mapped_value(row, 'long_description', PRODUCTS_COLUMN_MAP, df) or ''

            general_features = self._get_mapped_value(row, 'general_features', PRODUCTS_COLUMN_MAP, df)
            row_data['general_features'] = self._parse_list_field(general_features)

            short_specs = self._get_mapped_value(row, 'short_specs', PRODUCTS_COLUMN_MAP, df)
            row_data['short_specs'] = self._parse_list_field(short_specs)

            row_data['taxonomy'] = self._get_mapped_value(row, 'taxonomy', PRODUCTS_COLUMN_MAP, df)
            row_data['row_num'] = row_num

            self.report['issues'].extend(row_issues)

            if not any(i['severity'] == 'error' for i in row_issues):
                self.report['products_data'].append(row_data)
                self.report['counts']['valid_product_rows'] += 1

    def _validate_variants_sheet(self, df: pd.DataFrame):
        """Validate Variants sheet and populate variants_data (V5 contract)."""
        # V5: Use VARIANTS_REQUIRED constant
        missing_required_cols = []
        for field in VARIANTS_REQUIRED:
            if not self._map_column(df, field, VARIANTS_COLUMN_MAP):
                missing_required_cols.append(field)

        if missing_required_cols:
            self.report['issues'].append({
                'row': 0,
                'column': ', '.join(missing_required_cols),
                'value': None,
                'severity': 'error',
                'code': 'missing_required_columns',
                'message': f"Variants sheet missing required columns: {', '.join(missing_required_cols)}",
                'expected': 'Model Code, Product Slug',
            })
            return

        for idx, row in df.iterrows():
            row_num = idx + 2
            row_data = {}
            row_issues = []

            model_code = self._get_mapped_value(row, 'model_code', VARIANTS_COLUMN_MAP, df)
            if not model_code:
                row_issues.append({
                    'row': row_num,
                    'column': 'Model Code',
                    'value': None,
                    'severity': 'error',
                    'code': 'required_field_missing',
                    'message': 'Model Code is required',
                    'expected': 'Non-empty value like GKO9010',
                })
            elif len(str(model_code)) > 64:
                row_issues.append({
                    'row': row_num,
                    'column': 'Model Code',
                    'value': str(model_code)[:50] + '...',
                    'severity': 'error',
                    'code': 'value_too_long',
                    'message': f'Model Code is too long ({len(str(model_code))} characters). Maximum 64 characters allowed.',
                    'expected': 'Maximum 64 characters',
                })
            else:
                row_data['model_code'] = model_code

            product_slug = self._get_mapped_value(row, 'product_slug', VARIANTS_COLUMN_MAP, df)
            if not product_slug:
                row_issues.append({
                    'row': row_num,
                    'column': 'Product Slug',
                    'value': None,
                    'severity': 'error',
                    'code': 'required_field_missing',
                    'message': 'Product Slug is required',
                    'expected': 'Non-empty value like endustriyel-gazli-ocak',
                })
            else:
                row_data['product_slug'] = product_slug
                
                try:
                    Product.objects.get(slug=product_slug)
                except Product.DoesNotExist:
                    products_data = self.report.get('products_data', [])
                    product_in_products_sheet = any(p.get('slug') == product_slug for p in products_data)
                    
                    if not product_in_products_sheet:
                        if self.mode == 'smart':
                            self._add_product_candidate(product_slug, row_num)
                        else:
                            existing_slugs = list(Product.objects.values_list('slug', flat=True)[:5])
                            row_issues.append({
                                'row': row_num,
                                'column': 'Product Slug',
                                'value': product_slug,
                                'severity': 'error',
                                'code': 'invalid_foreign_key',
                                'message': f"Product '{product_slug}' not found",
                                'expected': f"Existing slugs: {', '.join(existing_slugs) or 'No products exist'}",
                            })

            # V5: Variant Name TR/EN default to Product title_tr/title_en when blank
            name_tr_raw = self._get_mapped_value(row, 'name_tr', VARIANTS_COLUMN_MAP, df)
            name_en_raw = self._get_mapped_value(row, 'name_en', VARIANTS_COLUMN_MAP, df)

            # Find matching product to get default names
            matching_product = None
            if product_slug:
                # First check in current Products sheet (products_data)
                for p in self.report.get('products_data', []):
                    if p.get('slug') == product_slug:
                        matching_product = p
                        break

                # If not found, try DB (for variants-only imports)
                if not matching_product:
                    try:
                        prod_obj = Product.objects.get(slug=product_slug)
                        matching_product = {'title_tr': prod_obj.title_tr, 'title_en': prod_obj.title_en}
                    except Product.DoesNotExist:
                        pass

            # Apply V5 defaults
            if not name_tr_raw and matching_product:
                row_data['name_tr'] = matching_product.get('title_tr', '')
            else:
                row_data['name_tr'] = name_tr_raw or ''

            if not name_en_raw and matching_product:
                row_data['name_en'] = matching_product.get('title_en', '')
            else:
                row_data['name_en'] = name_en_raw or ''
            row_data['sku'] = self._get_mapped_value(row, 'sku', VARIANTS_COLUMN_MAP, df)
            row_data['dimensions'] = self._get_mapped_value(row, 'dimensions', VARIANTS_COLUMN_MAP, df) or ''
            
            weight = self._get_mapped_value(row, 'weight_kg', VARIANTS_COLUMN_MAP, df)
            row_data['weight_kg'], weight_issue = self._parse_decimal(weight, 'Weight', row_num)
            if weight_issue:
                row_issues.append(weight_issue)
            
            price = self._get_mapped_value(row, 'list_price', VARIANTS_COLUMN_MAP, df)
            row_data['list_price'], price_issue = self._parse_decimal(price, 'List Price', row_num)
            if price_issue:
                row_issues.append(price_issue)
            
            stock = self._get_mapped_value(row, 'stock_qty', VARIANTS_COLUMN_MAP, df)
            row_data['stock_qty'], stock_issue = self._parse_integer(stock, 'Stock Qty', row_num)
            if stock_issue:
                row_issues.append(stock_issue)

            specs = {}
            for col in df.columns:
                if col.startswith('Spec:') or col.startswith('spec:'):
                    spec_key = col.split(':', 1)[1].strip()
                    spec_slug = slugify_tr(spec_key) if spec_key else spec_key.lower().replace(' ', '_')
                    val = row.get(col)
                    if pd.notna(val) and str(val).strip():
                        specs[spec_slug] = str(val).strip()
            row_data['specs'] = specs
            row_data['row_num'] = row_num

            self.report['issues'].extend(row_issues)
            
            if not any(i['severity'] == 'error' for i in row_issues):
                self.report['variants_data'].append(row_data)
                self.report['valid_rows'].append({
                    'row_num': row_num,
                    'data': row_data,
                    'type': 'variant',
                })
                self.report['counts']['valid_variant_rows'] += 1

    def _disambiguate_duplicate_model_codes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle duplicate model_code in data."""
        model_code_col = self._map_column(df, 'model_code', VARIANTS_COLUMN_MAP)
        if not model_code_col:
            return df

        model_code_counts = df[model_code_col].value_counts()
        duplicates = model_code_counts[model_code_counts > 1]

        if duplicates.empty:
            return df

        seen = {}
        for idx, row in df.iterrows():
            model_code = row.get(model_code_col)
            if pd.isna(model_code):
                continue

            if model_code in duplicates.index:
                if model_code not in seen:
                    seen[model_code] = 1
                else:
                    seen[model_code] += 1
                    new_code = f"{model_code}-{seen[model_code]}"
                    df.at[idx, model_code_col] = new_code
                    self.report['normalization']['disambiguated_model_codes'].append({
                        'row': idx + 2,
                        'original': model_code,
                        'new': new_code,
                    })

        return df

    def _add_category_candidate(self, slug: str, name: str, row_num: int, parent_slug: str = None):
        """Add category to candidates list with dedup."""
        # Create a unique key that includes parent for hierarchy support
        candidate_key = f"{parent_slug or 'ROOT'}:{slug}"

        if candidate_key not in self._seen_candidates['categories']:
            self._seen_candidates['categories'].add(candidate_key)
            self.report['candidates']['categories'].append({
                'slug': slug,
                'name': name or slug.replace('-', ' ').title(),
                'parent_slug': parent_slug,
                'series_mode': 'disabled',  # Safe default
                'rows': [row_num],
            })
            if self.mode == 'smart':
                parent_info = f" under '{parent_slug}'" if parent_slug else " (root)"
                self.report['issues'].append({
                    'row': row_num,
                    'column': 'Category',
                    'value': slug,
                    'severity': 'info',
                    'code': 'missing_category_candidate',
                    'message': f"Category '{name or slug}'{parent_info} will be created",
                    'expected': None,
                })
            elif self.mode == 'strict':
                existing_slugs = list(Category.objects.values_list('slug', flat=True)[:5])
                self.report['issues'].append({
                    'row': row_num,
                    'column': 'Category',
                    'value': slug,
                    'severity': 'error',
                    'code': 'invalid_foreign_key',
                    'message': f"Category '{slug}' not found",
                    'expected': f"Existing: {', '.join(existing_slugs) or 'No categories exist'}",
                })
        else:
            for c in self.report['candidates']['categories']:
                if c['slug'] == slug and c.get('parent_slug') == parent_slug:
                    if row_num not in c['rows']:
                        c['rows'].append(row_num)
                    break

    def _add_hierarchical_category_candidate(
        self,
        raw_path: str,
        row_num: int,
        has_series: bool = False,
        treat_slash_as_hierarchy: bool = True,
    ):
        """
        Add hierarchical category path to candidates list.

        Parses paths like "Root / Sub / Leaf" and adds missing segments.
        """
        from apps.ops.services.taxonomy_parser import (
            parse_category_path,
            resolve_category_chain,
        )

        segments = parse_category_path(raw_path, treat_slash_as_hierarchy)
        if not segments:
            return None

        # Resolve what exists and what's missing
        resolution = resolve_category_chain(
            segments,
            mode=self.mode,
            allow_create_missing=(self.mode == 'smart'),
        )

        # Store resolution info for reporting
        if 'category_resolutions' not in self.report:
            self.report['category_resolutions'] = []

        self.report['category_resolutions'].append({
            'row': row_num,
            'raw_path': raw_path,
            'segments': [{'name': s.name, 'slug': s.slug, 'level': s.level} for s in segments],
            'matched': resolution.matched_categories,
            'missing': resolution.missing_categories,
            'leaf_category_id': str(resolution.leaf_category.id) if resolution.leaf_category else None,
        })

        # Initialize category_hierarchies in candidates if not present
        if 'category_hierarchies' not in self.report['candidates']:
            self.report['candidates']['category_hierarchies'] = []

        # Add missing categories as candidates
        if resolution.missing_categories:
            # Store the full path as a hierarchy candidate
            path_key = raw_path.lower().strip()
            existing_paths = [h['path'].lower().strip() for h in self.report['candidates']['category_hierarchies']]

            if path_key not in existing_paths:
                self.report['candidates']['category_hierarchies'].append({
                    'path': raw_path,
                    'segments': [{'name': s.name, 'slug': s.slug, 'level': s.level} for s in segments],
                    'missing': resolution.missing_categories,
                    'has_series': has_series,
                    'rows': [row_num],
                })

                if self.mode == 'smart':
                    missing_names = [m['name'] for m in resolution.missing_categories]
                    self.report['issues'].append({
                        'row': row_num,
                        'column': 'Category/Taxonomy',
                        'value': raw_path,
                        'severity': 'info',
                        'code': 'missing_category_hierarchy',
                        'message': f"Category hierarchy will be created: {' > '.join(missing_names)}",
                        'expected': None,
                    })
                elif self.mode == 'strict':
                    self.report['issues'].append({
                        'row': row_num,
                        'column': 'Category/Taxonomy',
                        'value': raw_path,
                        'severity': 'error',
                        'code': 'missing_category_hierarchy',
                        'message': f"Category path not found: {raw_path}",
                        'expected': "Create categories first or use smart mode",
                    })
            else:
                # Add row to existing hierarchy candidate
                for h in self.report['candidates']['category_hierarchies']:
                    if h['path'].lower().strip() == path_key:
                        if row_num not in h['rows']:
                            h['rows'].append(row_num)
                        break

        # Return the leaf category if resolved
        return resolution.leaf_category

    def _add_series_candidate(self, slug: str, name: str, row_num: int, df: pd.DataFrame, row: pd.Series):
        """Add series to candidates list with dedup."""
        category_name = self._get_mapped_value(row, 'category', PRODUCTS_COLUMN_MAP, df)
        category_slug = self._get_mapped_value(row, 'category_slug', PRODUCTS_COLUMN_MAP, df)
        if not category_slug and category_name:
            category_slug = slugify_tr(category_name)
        
        if slug not in self._seen_candidates['series']:
            self._seen_candidates['series'].add(slug)
            self.report['candidates']['series'].append({
                'slug': slug,
                'name': name or slug.replace('-', ' ').title(),
                'category_slug': category_slug,
                'rows': [row_num],
            })
            if self.mode == 'smart':
                self.report['issues'].append({
                    'row': row_num,
                    'column': 'Series',
                    'value': slug,
                    'severity': 'info',
                    'code': 'missing_series_candidate',
                    'message': f"Series '{slug}' will be created",
                    'expected': None,
                })
            elif self.mode == 'strict':
                existing_slugs = list(Series.objects.values_list('slug', flat=True)[:5])
                self.report['issues'].append({
                    'row': row_num,
                    'column': 'Series',
                    'value': slug,
                    'severity': 'error',
                    'code': 'invalid_foreign_key',
                    'message': f"Series '{slug}' not found",
                    'expected': f"Existing: {', '.join(existing_slugs) or 'No series exist'}",
                })
        else:
            for s in self.report['candidates']['series']:
                if s['slug'] == slug:
                    if row_num not in s['rows']:
                        s['rows'].append(row_num)
                    break

    def _add_brand_candidate(self, slug: str, name: str, row_num: int):
        """Add brand to candidates list with dedup."""
        if slug not in self._seen_candidates['brands']:
            self._seen_candidates['brands'].add(slug)
            self.report['candidates']['brands'].append({
                'slug': slug,
                'name': name or slug.replace('-', ' ').title(),
                'rows': [row_num],
            })
            if self.mode == 'smart':
                self.report['issues'].append({
                    'row': row_num,
                    'column': 'Brand',
                    'value': slug,
                    'severity': 'info',
                    'code': 'missing_brand_candidate',
                    'message': f"Brand '{slug}' will be created",
                    'expected': None,
                })
            elif self.mode == 'strict':
                existing_slugs = list(Brand.objects.values_list('slug', flat=True)[:5])
                self.report['issues'].append({
                    'row': row_num,
                    'column': 'Brand',
                    'value': slug,
                    'severity': 'error',
                    'code': 'invalid_foreign_key',
                    'message': f"Brand '{slug}' not found",
                    'expected': f"Existing: {', '.join(existing_slugs) or 'No brands exist'}",
                })
        else:
            for b in self.report['candidates']['brands']:
                if b['slug'] == slug:
                    if row_num not in b['rows']:
                        b['rows'].append(row_num)
                    break

    def _add_product_candidate(self, slug: str, row_num: int):
        """Add product to candidates list with dedup."""
        if slug not in self._seen_candidates['products']:
            self._seen_candidates['products'].add(slug)
            self.report['candidates']['products'].append({
                'slug': slug,
                'rows': [row_num],
            })
            self.report['issues'].append({
                'row': row_num,
                'column': 'Product Slug',
                'value': slug,
                'severity': 'warning',
                'code': 'missing_product_candidate',
                'message': f"Product '{slug}' not found (will need to be created from Products sheet or manually)",
                'expected': None,
            })
        else:
            for p in self.report['candidates']['products']:
                if p['slug'] == slug:
                    if row_num not in p['rows']:
                        p['rows'].append(row_num)
                    break

    def _is_category_ancestor_of(self, ancestor_slug: str, descendant_slug: str) -> Tuple[bool, str]:
        """
        Check if ancestor_slug is an ancestor of descendant_slug in the category hierarchy.

        This supports hierarchical categories where a series can belong to a parent
        category while products belong to child categories.

        Args:
            ancestor_slug: The slug of the potential ancestor category (series category)
            descendant_slug: The slug of the potential descendant category (product category)

        Returns:
            Tuple of (is_match, match_type) where:
            - is_match: True if ancestor_slug is an ancestor of descendant_slug
            - match_type: 'exact', 'ancestor', or 'mismatch'
        """
        # Exact match check
        if ancestor_slug == descendant_slug:
            return True, 'exact'

        # Load caches for DB lookup
        self._load_caches()

        # First try DB hierarchy (preferred - accurate parent chain)
        descendant_cat = self._category_cache.get(descendant_slug)
        if descendant_cat:
            # Walk up the parent chain
            current = descendant_cat.parent
            while current:
                if current.slug == ancestor_slug:
                    return True, 'ancestor'
                current = current.parent

        # Fallback: String prefix check for slug paths like "firinlar/kombi-..."
        # This handles cases where category hierarchy is encoded in the slug path
        if '/' in descendant_slug:
            if descendant_slug.startswith(ancestor_slug + '/'):
                return True, 'ancestor'

        return False, 'mismatch'

    def _parse_status(self, value: Optional[str]) -> str:
        """Parse status value. Defaults to 'active' per V5 contract."""
        if not value:
            return 'active'
        value_lower = value.lower()
        if value_lower in ('active', 'aktif', 'yayinda'):
            return 'active'
        elif value_lower in ('draft', 'taslak'):
            return 'draft'
        elif value_lower in ('archived', 'arsivlenmis', 'pasif'):
            return 'archived'
        # V5: Default to 'active' for invalid values
        return 'active'

    def _parse_bool(self, value: Optional[str]) -> bool:
        """Parse boolean value."""
        if not value:
            return False
        value_lower = value.lower()
        return value_lower in ('true', 'yes', 'evet', '1', 'x')

    def _parse_list_field(self, value: Optional[str]) -> List[str]:
        """Parse pipe or newline separated list."""
        if not value:
            return []
        if '|' in value:
            return [v.strip() for v in value.split('|') if v.strip()]
        elif '\n' in value:
            return [v.strip() for v in value.split('\n') if v.strip()]
        return [value.strip()] if value.strip() else []

    def _parse_decimal(self, value: Optional[str], field_name: str, row_num: int) -> Tuple[Optional[Decimal], Optional[Dict]]:
        """Parse decimal value with locale support."""
        if not value:
            return None, None
        try:
            cleaned = str(value).strip()
            cleaned = cleaned.replace(' ', '').replace('\xa0', '')
            if ',' in cleaned and '.' in cleaned:
                cleaned = cleaned.replace('.', '').replace(',', '.')
            elif ',' in cleaned:
                cleaned = cleaned.replace(',', '.')
            return Decimal(cleaned), None
        except (InvalidOperation, ValueError):
            return None, {
                'row': row_num,
                'column': field_name,
                'value': value,
                'severity': 'error',
                'code': 'invalid_decimal',
                'message': f"Invalid decimal value for {field_name}: '{value}'",
                'expected': 'Number like 15000.50 or 15000,50 or 15.000,50',
            }

    def _parse_integer(self, value: Optional[str], field_name: str, row_num: int) -> Tuple[Optional[int], Optional[Dict]]:
        """Parse integer value."""
        if not value:
            return None, None
        try:
            cleaned = str(value).strip().replace('.0', '').replace(',0', '')
            return int(float(cleaned)), None
        except (ValueError, TypeError):
            return None, {
                'row': row_num,
                'column': field_name,
                'value': value,
                'severity': 'error',
                'code': 'invalid_integer',
                'message': f"Invalid integer value for {field_name}: '{value}'",
                'expected': 'Whole number like 50 or 100',
            }

    def _analyze_upsert_operations(self):
        """Analyze which products/variants will be created vs updated."""
        product_slugs = {p['slug'] for p in self.report.get('products_data', [])}
        model_codes = {v['model_code'] for v in self.report.get('variants_data', [])}

        existing_products = set(
            Product.objects.filter(slug__in=product_slugs).values_list('slug', flat=True)
        )
        existing_variants = set(
            Variant.objects.filter(model_code__in=model_codes).values_list('model_code', flat=True)
        )

        self.report['counts']['products_to_create'] = len(product_slugs - existing_products)
        self.report['counts']['products_to_update'] = len(product_slugs & existing_products)
        self.report['counts']['variants_to_create'] = len(model_codes - existing_variants)
        self.report['counts']['variants_to_update'] = len(model_codes & existing_variants)

    def _create_candidates(self, candidates: Dict) -> Tuple[List[str], List[str], List[str]]:
        """
        Create missing entities in smart mode (V5 contract).

        Creation order (respects FK constraints):
        1. Categories (with hierarchical support)
        2. Brands (no dependencies)
        3. Series (FK: category_id)
        4. Products (FK: series_id, brand_id) - created in _upsert_product_from_data
        5. Variants (FK: product_id) - created in _upsert_variant_from_data

        Returns:
            Tuple of (created_categories, created_brands, created_series) slug lists
        """
        from apps.ops.services.taxonomy_parser import (
            parse_category_path,
            get_or_create_category_chain,
        )

        created_categories = []
        created_brands = []
        created_series = []

        # Step 1: Create Categories (with hierarchical support)
        # First, process hierarchical category paths (from taxonomy field)
        for cat_data in candidates.get('category_hierarchies', []):
            # cat_data contains: {'path': 'Root / Sub / Leaf', 'rows': [...]}
            raw_path = cat_data.get('path', '')
            if raw_path:
                segments = parse_category_path(raw_path, treat_slash_as_hierarchy=True)
                if segments:
                    # Determine series_mode based on whether products in this category have series
                    series_mode = 'optional' if cat_data.get('has_series') else 'disabled'
                    result = get_or_create_category_chain(segments, series_mode=series_mode)
                    if result.created_categories:
                        for created in result.created_categories:
                            created_categories.append(created['slug'])
                            logger.info(f"[COMMIT] Created hierarchical category: {created['slug']} (level={created['level']})")

        # Then, process flat categories (legacy support)
        for cat_data in candidates.get('categories', []):
            # CRITICAL: Always set series_mode to avoid NULL violation
            series_mode = cat_data.get('series_mode', 'disabled')
            if series_mode not in ['disabled', 'optional', 'required']:
                series_mode = 'disabled'

            # For flat categories, parent is None (root level)
            parent_slug = cat_data.get('parent_slug')
            parent = None
            if parent_slug:
                parent = Category.objects.filter(slug=parent_slug).first()

            # Use get_or_create with parent scope
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                parent=parent,
                defaults={
                    'name': cat_data['name'],
                    'series_mode': series_mode,
                },
            )
            if created:
                created_categories.append(cat_data['slug'])
                logger.info(f"[COMMIT] Created category: {cat_data['slug']} (series_mode={series_mode})")
            else:
                logger.debug(f"[COMMIT] Category already exists: {cat_data['slug']}")

        # Step 2: Create Brands (no FK dependencies)
        for brand_data in candidates.get('brands', []):
            brand, created = Brand.objects.get_or_create(
                slug=brand_data['slug'],
                defaults={'name': brand_data['name']},
            )
            if created:
                created_brands.append(brand_data['slug'])
                logger.info(f"[COMMIT] Created brand: {brand_data['slug']}")
            else:
                logger.debug(f"[COMMIT] Brand already exists: {brand_data['slug']}")

        # Step 3: Create Series (FK: category_id)
        # CRITICAL: Series slug is unique per category, not globally
        for series_data in candidates.get('series', []):
            category_slug = series_data.get('category_slug')
            category = None

            # V5: Category is REQUIRED for Series - no fallback
            if category_slug:
                category = Category.objects.filter(slug=category_slug).first()

            if not category:
                # NO FALLBACK: Report error instead of silently using first category
                logger.error(
                    f"[COMMIT] SKIPPED series '{series_data['slug']}': "
                    f"category '{category_slug}' not found. "
                    f"This is a validation error that should have been caught earlier."
                )
                continue

            # FIXED: Series slug is unique per category, not globally
            # Look up by (category, slug) pair to support same slug in different categories
            series, created = Series.objects.get_or_create(
                category=category,
                slug=series_data['slug'],
                defaults={
                    'name': series_data['name'],
                },
            )
            if created:
                created_series.append(series_data['slug'])
                logger.info(f"[COMMIT] Created series: {series_data['slug']} (category={category.slug})")
            else:
                logger.debug(f"[COMMIT] Series already exists: {series_data['slug']} in category {category.slug}")

        return created_categories, created_brands, created_series

    def _upsert_product_from_data(self, data: Dict) -> Tuple[Product, bool]:
        """Upsert product from validated data."""
        slug = data['slug']

        # FIXED: No silent fallback - series must be found or error
        series = None
        series_slug = data.get('series_slug')
        category_slug = data.get('category_slug')

        if series_slug:
            # FIXED: Series lookup by (category, slug) for per-category uniqueness
            if category_slug:
                # First try exact match by category
                series = Series.objects.filter(
                    category__slug=category_slug,
                    slug=series_slug
                ).first()

            # If not found, try global lookup (backward compat for globally unique slugs)
            if not series:
                series = Series.objects.filter(slug=series_slug).first()

        # NO FALLBACK: Raise error instead of silently using first series
        if not series:
            raise ValueError(
                f"Series '{series_slug}' not found for product '{slug}'. "
                f"Category: {category_slug}. "
                f"Import must be re-validated with correct series reference."
            )

        brand = None
        brand_slug = data.get('brand_slug')
        if brand_slug:
            brand = Brand.objects.filter(slug=brand_slug).first()

        defaults = {
            'name': data.get('name', slug),
            'title_tr': data.get('title_tr', slug),
            'title_en': data.get('title_en', ''),
            'series': series,
            'status': data.get('status', 'active'),
            'is_featured': data.get('is_featured', False),
            'long_description': data.get('long_description', ''),
            'general_features': data.get('general_features', []),
            'short_specs': data.get('short_specs', []),
        }

        # Keep product.category consistent with series.category
        if series and series.category:
            defaults['category'] = series.category
        
        if brand:
            defaults['brand'] = brand

        product, created = Product.objects.update_or_create(
            slug=slug,
            defaults=defaults,
        )

        # V5: Auto-create brand-category relationship if both exist
        if brand and series and series.category:
            # Use get_or_create to avoid duplicate errors
            BrandCategory.objects.get_or_create(
                brand=brand,
                category=series.category,
                defaults={'is_active': True, 'order': 0}
            )
            logger.debug(
                f"[COMMIT] Ensured brand-category relationship: "
                f"{brand.slug} <-> {series.category.slug}"
            )

        return product, created

    def _upsert_variant_from_data(self, data: Dict) -> Tuple[Variant, bool]:
        """Upsert variant from validated data."""
        model_code = data['model_code']
        product_slug = data['product_slug']
        
        product = Product.objects.filter(slug=product_slug).first()
        if not product:
            raise ValueError(f"Product '{product_slug}' not found for variant {model_code}")

        defaults = {
            'product': product,
            'name_tr': data.get('name_tr', model_code),
            'name_en': data.get('name_en', ''),
            'dimensions': data.get('dimensions', ''),
            'specs': data.get('specs', {}),
        }
        
        if data.get('sku'):
            defaults['sku'] = data['sku']
        if data.get('weight_kg') is not None:
            defaults['weight_kg'] = data['weight_kg']
        if data.get('list_price') is not None:
            defaults['list_price'] = data['list_price']
        if data.get('stock_qty') is not None:
            defaults['stock_qty'] = data['stock_qty']

        variant, created = Variant.objects.update_or_create(
            model_code=model_code,
            defaults=defaults,
        )

        return variant, created

    def _verify_db_write(
        self,
        created_categories: List[str],
        created_brands: List[str],
        created_series: List[str],
        created_products: List[str],
        created_variants: List[str],
    ) -> Dict[str, Any]:
        """
        Verify that created entities were actually written to DB (V5 contract).

        This is CRITICAL to prevent "shows created but not in DB" bugs.
        Frontend MUST NOT show "success" unless db_verify.created_entities_found_in_db == true.
        """
        # Verify each entity type
        category_verified = all(
            Category.objects.filter(slug=slug).exists() for slug in created_categories
        )
        brand_verified = all(
            Brand.objects.filter(slug=slug).exists() for slug in created_brands
        )
        series_verified = all(
            Series.objects.filter(slug=slug).exists() for slug in created_series
        )
        product_verified = all(
            Product.objects.filter(slug=slug).exists() for slug in created_products
        )
        variant_verified = all(
            Variant.objects.filter(model_code=code).exists() for code in created_variants
        )

        # Overall verification (ALL entities must be found)
        all_verified = (
            category_verified
            and brand_verified
            and series_verified
            and product_verified
            and variant_verified
        )

        return {
            'enabled': True,
            'verified_at': timezone.now().isoformat(),
            'created_entities_found_in_db': all_verified,
            'created_category_slugs': created_categories,
            'created_brand_slugs': created_brands,
            'created_series_slugs': created_series,
            'created_product_slugs': created_products,
            'created_variant_model_codes': created_variants,
            'verification_details': {
                'categories_verified': category_verified,
                'brands_verified': brand_verified,
                'series_verified': series_verified,
                'products_verified': product_verified,
                'variants_verified': variant_verified,
            },
        }

    @staticmethod
    def compute_file_hash(file_bytes: bytes) -> str:
        """Compute SHA-256 hash of file for idempotency."""
        return hashlib.sha256(file_bytes).hexdigest()
