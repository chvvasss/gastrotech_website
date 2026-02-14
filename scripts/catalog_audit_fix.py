#!/usr/bin/env python3
"""
Catalog Data Audit & Remediation Script
Analyzes CSV exports, detects duplicates/mismatches, generates fix plan & SQL
"""

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

import pandas as pd


# ============================================================================
# CANONICAL FORM & UTILITIES
# ============================================================================

def canonical_form(text: str) -> str:
    """
    Unicode normalize + casefold + TR transliteration + trim + collapse whitespace
    """
    if not text:
        return ''
    
    # NFD normalize
    text = unicodedata.normalize('NFD', text)
    
    # Turkish transliteration
    tr_map = str.maketrans({
        'ç': 'c', 'Ç': 'c',
        'ğ': 'g', 'Ğ': 'g',
        'ı': 'i', 'İ': 'i', 'I': 'i',
        'ö': 'o', 'Ö': 'o',
        'ş': 's', 'Ş': 's',
        'ü': 'u', 'Ü': 'u',
    })
    text = text.translate(tr_map)
    
    # Remove diacritics
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    
    # Casefold + trim + collapse whitespace
    return ' '.join(text.casefold().split())


def slugify(text: str) -> str:
    """Basic slugification"""
    text = canonical_form(text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Brand:
    id: int
    name: str
    slug: str
    is_active: bool
    logo_media_id: Optional[int]
    created_at: Optional[str]
    product_count: int = 0
    canonical_name: str = ''
    
    def __post_init__(self):
        self.canonical_name = canonical_form(self.name)


@dataclass
class Category:
    id: int
    name: str
    slug: str
    parent_id: Optional[int]
    series_mode: Optional[str]
    created_at: Optional[str]
    product_count: int = 0
    series_count: int = 0
    canonical_name: str = ''
    
    def __post_init__(self):
        self.canonical_name = canonical_form(self.name)


@dataclass
class Series:
    id: int
    name: str
    slug: str
    category_id: Optional[int]
    is_featured: bool
    created_at: Optional[str]
    product_count: int = 0


@dataclass
class Product:
    id: int
    name: str
    slug: str
    status: str
    series_id: Optional[int]
    brand_id: Optional[int]
    category_id: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    variant_count: int = 0


@dataclass
class Variant:
    id: int
    sku: Optional[str]
    product_id: int
    model_code: Optional[str]
    name_tr: Optional[str]
    name_en: Optional[str]


@dataclass
class MergeAction:
    entity_type: str
    winner_id: int
    loser_ids: List[int]
    reason: str
    confidence: float


@dataclass
class MoveAction:
    entity_type: str
    entity_id: int
    from_value: Any
    to_value: Any
    reason: str


# ============================================================================
# CATALOG DATABASE (In-Memory)
# ============================================================================

class CatalogDB:
    def __init__(self, input_dir: Path):
        self.input_dir = input_dir
        self.brands: Dict[int, Brand] = {}
        self.categories: Dict[int, Category] = {}
        self.series: Dict[int, Series] = {}
        self.products: Dict[int, Product] = {}
        self.variants: Dict[int, Variant] = {}
        
        # Audit findings
        self.brand_merges: List[MergeAction] = []
        self.category_merges: List[MergeAction] = []
        self.category_moves: List[MoveAction] = []
        self.series_moves: List[MoveAction] = []
        self.product_merges: List[MergeAction] = []
        
    def load_csvs(self):
        """Load all CSV files"""
        print("Loading CSV files...")
        
        # Find CSV files (strip timestamp suffix)
        brand_csv = self._find_csv('catalog_brand')
        category_csv = self._find_csv('catalog_category')
        series_csv = self._find_csv('catalog_series')
        product_csv = self._find_csv('catalog_product')
        variant_csv = self._find_csv('catalog_variant')
        
        # Load brands
        if brand_csv:
            df = pd.read_csv(brand_csv)
            for _, row in df.iterrows():
                self.brands[row['id']] = Brand(
                    id=row['id'],
                    name=row['name'],
                    slug=row['slug'],
                    is_active=row.get('is_active', True),
                    logo_media_id=row.get('logo_media_id'),
                    created_at=row.get('created_at'),
                )
        
        # Load categories
        if category_csv:
            df = pd.read_csv(category_csv)
            for _, row in df.iterrows():
                self.categories[row['id']] = Category(
                    id=row['id'],
                    name=row['name'],
                    slug=row['slug'],
                    parent_id=row.get('parent_id') if pd.notna(row.get('parent_id')) else None,
                    series_mode=row.get('series_mode'),
                    created_at=row.get('created_at'),
                )
        
        # Load series
        if series_csv:
            df = pd.read_csv(series_csv)
            for _, row in df.iterrows():
                self.series[row['id']] = Series(
                    id=row['id'],
                    name=row['name'],
                    slug=row['slug'],
                    category_id=row.get('category_id') if pd.notna(row.get('category_id')) else None,
                    is_featured=row.get('is_featured', False),
                    created_at=row.get('created_at'),
                )
        
        # Load products
        if product_csv:
            df = pd.read_csv(product_csv)
            for _, row in df.iterrows():
                self.products[row['id']] = Product(
                    id=row['id'],
                    name=row['name'],
                    slug=row['slug'],
                    status=row.get('status', 'draft'),
                    series_id=row.get('series_id') if pd.notna(row.get('series_id')) else None,
                    brand_id=row.get('brand_id') if pd.notna(row.get('brand_id')) else None,
                    category_id=row.get('category_id') if pd.notna(row.get('category_id')) else None,
                    created_at=row.get('created_at'),
                    updated_at=row.get('updated_at'),
                )
        
        # Load variants
        if variant_csv:
            df = pd.read_csv(variant_csv)
            for _, row in df.iterrows():
                self.variants[row['id']] = Variant(
                    id=row['id'],
                    sku=row.get('sku') if pd.notna(row.get('sku')) else None,
                    product_id=row['product_id'],
                    model_code=row.get('model_code'),
                    name_tr=row.get('name_tr'),
                    name_en=row.get('name_en'),
                )
        
        # Compute reference counts
        self._compute_reference_counts()
        
        print(f"Loaded: {len(self.brands)} brands, {len(self.categories)} categories, "
              f"{len(self.series)} series, {len(self.products)} products, {len(self.variants)} variants")
    
    def _find_csv(self, table_name: str) -> Optional[Path]:
        """Find CSV file for table (handles timestamp suffix)"""
        pattern = f"{table_name}_*.csv"
        files = list(self.input_dir.glob(pattern))
        if not files:
            # Try exact name
            exact = self.input_dir / f"{table_name}.csv"
            return exact if exact.exists() else None
        return files[0]
    
    def _compute_reference_counts(self):
        """Compute how many times each entity is referenced"""
        # Brand product counts
        for product in self.products.values():
            if product.brand_id and product.brand_id in self.brands:
                self.brands[product.brand_id].product_count += 1
        
        # Category counts
        for product in self.products.values():
            if product.category_id and product.category_id in self.categories:
                self.categories[product.category_id].product_count += 1
        for series in self.series.values():
            if series.category_id and series.category_id in self.categories:
                self.categories[series.category_id].series_count += 1
        
        # Series product counts
        for product in self.products.values():
            if product.series_id and product.series_id in self.series:
                self.series[product.series_id].product_count += 1
        
        # Product variant counts
        for variant in self.variants.values():
            if variant.product_id in self.products:
                self.products[variant.product_id].variant_count += 1
    
    # ========================================================================
    # AUDIT METHODS
    # ========================================================================
    
    def audit_brand_duplicates(self):
        """Detect and plan brand merges"""
        print("\n=== Auditing Brand Duplicates ===")
        
        # Group by canonical name
        groups = defaultdict(list)
        for brand in self.brands.values():
            groups[brand.canonical_name].append(brand)
        
        # Find duplicates
        for canonical, brands_list in groups.items():
            if len(brands_list) > 1:
                # Select winner: highest product_count, else earliest created_at, else lowest id
                # Use datetime objects directly (Windows-safe)
                def brand_sort_key(b):
                    created = self._parse_datetime(b.created_at)
                    return (
                        -b.product_count,  # Negative for descending
                        created,  # Ascending (earlier is better)
                        b.id  # Ascending (lower is better)
                    )
                
                winner = min(brands_list, key=brand_sort_key)
                losers = [b for b in brands_list if b.id != winner.id]
                
                self.brand_merges.append(MergeAction(
                    entity_type='brand',
                    winner_id=winner.id,
                    loser_ids=[b.id for b in losers],
                    reason=f"Canonical name match: '{canonical}'",
                    confidence=1.0
                ))
                
                print(f"  MERGE: {[b.name for b in losers]} -> {winner.name} (id={winner.id})")
    
    def audit_category_duplicates(self):
        """Detect and plan category merges"""
        print("\n=== Auditing Category Duplicates ===")
        
        # Group by (canonical_name, parent_id)
        groups = defaultdict(list)
        for cat in self.categories.values():
            key = (cat.canonical_name, cat.parent_id)
            groups[key].append(cat)
        
        # Find duplicates
        for (canonical, parent_id), cats in groups.items():
            if len(cats) > 1:
                # Winner: most referenced, earliest created, lowest id
                def category_sort_key(c):
                    created = self._parse_datetime(c.created_at)
                    return (
                        -(c.product_count + c.series_count),  # Negative for descending
                        created,  # Ascending (earlier is better)
                        c.id  # Ascending (lower is better)
                    )
                
                winner = min(cats, key=category_sort_key)
                losers = [c for c in cats if c.id != winner.id]
                
                self.category_merges.append(MergeAction(
                    entity_type='category',
                    winner_id=winner.id,
                    loser_ids=[c.id for c in losers],
                    reason=f"Canonical name match: '{canonical}' under parent={parent_id}",
                    confidence=1.0
                ))
                
                print(f"  MERGE: {[c.name for c in losers]} -> {winner.name} (id={winner.id})")
    
    def audit_series_category_mismatches(self):
        """Detect series→category ancestry violations"""
        print("\n=== Auditing Series Category Mismatches ===")
        
        # Build category tree
        category_tree = self._build_category_tree()
        
        for series in self.series.values():
            if not series.category_id:
                continue
            
            # Get all products in this series
            series_products = [p for p in self.products.values() if p.series_id == series.id]
            if not series_products:
                continue
            
            # Check if series.category is ancestor of all product.category
            invalid_products = []
            for product in series_products:
                if not product.category_id:
                    continue
                if not self._is_ancestor(series.category_id, product.category_id, category_tree):
                    invalid_products.append(product)
            
            if invalid_products:
                # Find common ancestor
                all_categories = [p.category_id for p in series_products if p.category_id]
                common_ancestor = self._find_common_ancestor(all_categories, category_tree)
                
                if common_ancestor:
                    self.series_moves.append(MoveAction(
                        entity_type='series',
                        entity_id=series.id,
                        from_value=series.category_id,
                        to_value=common_ancestor,
                        reason=f"Move to common ancestor (products span multiple categories)"
                    ))
                    print(f"  MOVE series '{series.name}': category {series.category_id} -> {common_ancestor}")
                else:
                    print(f"  SPLIT needed for series '{series.name}' (no common ancestor)")
    
    def _build_category_tree(self) -> Dict[int, Set[int]]:
        """Build ancestor map: {category_id: {ancestor_ids}}"""
        tree = {cat.id: set() for cat in self.categories.values()}
        
        for cat in self.categories.values():
            current_id = cat.id
            parent_id = cat.parent_id
            while parent_id:
                tree[current_id].add(parent_id)
                parent_cat = self.categories.get(parent_id)
                if not parent_cat:
                    break
                parent_id = parent_cat.parent_id
        
        return tree
    
    def _is_ancestor(self, ancestor_id: int, descendant_id: int, tree: Dict[int, Set[int]]) -> bool:
        """Check if ancestor_id is in the ancestry of descendant_id"""
        if ancestor_id == descendant_id:
            return True
        return ancestor_id in tree.get(descendant_id, set())
    
    def _find_common_ancestor(self, category_ids: List[int], tree: Dict[int, Set[int]]) -> Optional[int]:
        """Find lowest common ancestor of categories"""
        if not category_ids:
            return None
        
        # Get all ancestors for each category (including self)
        ancestor_sets = []
        for cat_id in category_ids:
            ancestors = tree.get(cat_id, set()).copy()
            ancestors.add(cat_id)
            ancestor_sets.append(ancestors)
        
        # Find intersection
        common = set.intersection(*ancestor_sets)
        if not common:
            return None
        
        # Return the deepest (highest id, most specific)
        return max(common)
    
    def _parse_datetime(self, dt_str: Optional[str]) -> datetime:
        """Parse datetime string or return epoch (Windows-safe)"""
        if not dt_str:
            return datetime(1970, 1, 1)
        try:
            # Try ISO format first
            parsed = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            # Windows doesn't support negative timestamps, clamp to 1970
            if parsed.year < 1970:
                return datetime(1970, 1, 1)
            return parsed
        except:
            return datetime(1970, 1, 1)
    
    # ========================================================================
    # REPORT GENERATION
    # ========================================================================
    
    def generate_report(self, output_dir: Path):
        """Generate audit reports"""
        print("\n=== Generating Reports ===")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'brands': len(self.brands),
                'categories': len(self.categories),
                'series': len(self.series),
                'products': len(self.products),
                'variants': len(self.variants),
            },
            'issues': {
                'brand_duplicates': len(self.brand_merges),
                'category_duplicates': len(self.category_merges),
                'series_mismatches': len(self.series_moves),
            },
            'brand_merges': [asdict(m) for m in self.brand_merges],
            'category_merges': [asdict(m) for m in self.category_merges],
            'series_moves': [asdict(m) for m in self.series_moves],
        }
        
        # Write JSON
        json_path = output_dir / 'audit_report.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"  Wrote {json_path}")
        
        # Write Markdown
        md_path = output_dir / 'audit_report.md'
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# Catalog Audit Report\n\n")
            f.write(f"**Generated:** {report['timestamp']}\n\n")
            f.write("## Summary\n\n")
            f.write(f"- Brands: {report['summary']['brands']}\n")
            f.write(f"- Categories: {report['summary']['categories']}\n")
            f.write(f"- Series: {report['summary']['series']}\n")
            f.write(f"- Products: {report['summary']['products']}\n")
            f.write(f"- Variants: {report['summary']['variants']}\n\n")
            
            f.write("## Issues Found\n\n")
            f.write(f"- Brand duplicates: {report['issues']['brand_duplicates']}\n")
            f.write(f"- Category duplicates: {report['issues']['category_duplicates']}\n")
            f.write(f"- Series category mismatches: {report['issues']['series_mismatches']}\n\n")
            
            if self.brand_merges:
                f.write("### Brand Merges\n\n")
                for merge in self.brand_merges:
                    winner = self.brands[merge.winner_id]
                    losers = [self.brands[lid] for lid in merge.loser_ids]
                    f.write(f"- **{winner.name}** <- {', '.join(l.name for l in losers)}\n")
                    f.write(f"  - Reason: {merge.reason}\n")
        
        print(f"  Wrote {md_path}")
    
    def generate_sql(self, output_dir: Path, apply: bool = False):
        """Generate SQL migration scripts"""
        print("\n=== Generating SQL Scripts ===")
        
        # Check idempotency: if already applied, skip
        if apply:
            print("  APPLY mode: generating executable SQL")
        else:
            print("  DRY-RUN mode: generating preview SQL")
        
        # Generate each phase
        self._generate_sql_mapping_tables(output_dir)
        self._generate_sql_brand_merges(output_dir, apply)
        self._generate_sql_category_merges(output_dir, apply)
        self._generate_sql_series_moves(output_dir, apply)
    
    def _generate_sql_mapping_tables(self, output_dir: Path):
        """001_create_mapping_tables.sql"""
        sql_path = output_dir / '001_create_mapping_tables.sql'
        with open(sql_path, 'w', encoding='utf-8') as f:
            f.write("""-- Mapping & Audit Tables
-- Idempotent: IF NOT EXISTS

CREATE TABLE IF NOT EXISTS slug_redirects (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    old_slug VARCHAR(255) NOT NULL,
    new_slug VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_type, old_slug)
);

CREATE TABLE IF NOT EXISTS entity_aliases (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    alias_text VARCHAR(255) NOT NULL,
    alias_slug VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS merge_audit_log (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    winner_id INTEGER NOT NULL,
    loser_id INTEGER NOT NULL,
    reason TEXT,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS category_reclass_log (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    from_value INTEGER,
    to_value INTEGER,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add merged_into_id to brands (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='catalog_brand' AND column_name='merged_into_id'
    ) THEN
        ALTER TABLE catalog_brand ADD COLUMN merged_into_id INTEGER REFERENCES catalog_brand(id);
    END IF;
END $$;
""")
        print(f"  Wrote {sql_path}")
    
    def _generate_sql_brand_merges(self, output_dir: Path, apply: bool):
        """010_brands_merge.sql"""
        sql_path = output_dir / '010_brands_merge.sql'
        with open(sql_path, 'w', encoding='utf-8') as f:
            f.write("-- Brand Merges\n")
            f.write("-- Idempotent: check merge_audit_log before apply\n\n")
            
            if not self.brand_merges:
                f.write("-- No brand merges needed\n")
                return
            
            for merge in self.brand_merges:
                winner = self.brands[merge.winner_id]
                losers = [self.brands[lid] for lid in merge.loser_ids]
                
                f.write(f"-- Merge: {', '.join(l.name for l in losers)} → {winner.name}\n")
                f.write("DO $$\nBEGIN\n")
                
                for loser in losers:
                    # Idempotency check
                    f.write(f"    -- Check if already merged\n")
                    f.write(f"    IF NOT EXISTS (SELECT 1 FROM merge_audit_log WHERE entity_type='brand' "
                            f"AND winner_id='{winner.id}' AND loser_id='{loser.id}') THEN\n")
                    
                    # Repoint products
                    f.write(f"        UPDATE catalog_product SET brand_id='{winner.id}' WHERE brand_id='{loser.id}';\n")
                    
                    # Create alias
                    f.write(f"        INSERT INTO entity_aliases (entity_type, entity_id, alias_text, alias_slug) "
                            f"VALUES ('brand', '{winner.id}', '{loser.name.replace("'", "''")}', '{loser.slug}');\n")
                    
                    # Create redirect
                    f.write(f"        INSERT INTO slug_redirects (entity_type, old_slug, new_slug) "
                            f"VALUES ('brand', '{loser.slug}', '{winner.slug}') "
                            f"ON CONFLICT (entity_type, old_slug) DO NOTHING;\n")
                    
                    # Log merge
                    f.write(f"        INSERT INTO merge_audit_log (entity_type, winner_id, loser_id, reason, confidence) "
                            f"VALUES ('brand', '{winner.id}', '{loser.id}', '{merge.reason.replace("'", "''")}', {merge.confidence});\n")
                    
                    # Mark loser
                    f.write(f"        UPDATE catalog_brand SET merged_into_id='{winner.id}' WHERE id='{loser.id}';\n")
                    
                    f.write(f"    END IF;\n")
                
                f.write("END $$;\n\n")
        
        print(f"  Wrote {sql_path}")
    
    def _generate_sql_category_merges(self, output_dir: Path, apply: bool):
        """020_categories_merge_hierarchy.sql"""
        sql_path = output_dir / '020_categories_merge_hierarchy.sql'
        with open(sql_path, 'w', encoding='utf-8') as f:
            f.write("-- Category Merges & Hierarchy Fixes\n\n")
            
            if not self.category_merges:
                f.write("-- No category merges needed\n")
                return
            
            for merge in self.category_merges:
                winner = self.categories[merge.winner_id]
                losers = [self.categories[lid] for lid in merge.loser_ids]
                
                f.write(f"-- Merge: {', '.join(l.name for l in losers)} → {winner.name}\n")
                f.write("DO $$\nBEGIN\n")
                
                for loser in losers:
                    f.write(f"    IF NOT EXISTS (SELECT 1 FROM merge_audit_log WHERE entity_type='category' "
                            f"AND winner_id='{winner.id}' AND loser_id='{loser.id}') THEN\n")
                    
                    # Repoint products
                    f.write(f"        UPDATE catalog_product SET category_id='{winner.id}' WHERE category_id='{loser.id}';\n")
                    
                    # Repoint series
                    f.write(f"        UPDATE catalog_series SET category_id='{winner.id}' WHERE category_id='{loser.id}';\n")
                    
                    # Repoint child categories
                    f.write(f"        UPDATE catalog_category SET parent_id='{winner.id}' WHERE parent_id='{loser.id}';\n")
                    
                    # Create alias + redirect + log
                    f.write(f"        INSERT INTO entity_aliases (entity_type, entity_id, alias_text, alias_slug) "
                            f"VALUES ('category', '{winner.id}', '{loser.name.replace("'", "''")}', '{loser.slug}');\n")
                    f.write(f"        INSERT INTO slug_redirects (entity_type, old_slug, new_slug) "
                            f"VALUES ('category', '{loser.slug}', '{winner.slug}') "
                            f"ON CONFLICT (entity_type, old_slug) DO NOTHING;\n")
                    f.write(f"        INSERT INTO merge_audit_log (entity_type, winner_id, loser_id, reason, confidence) "
                            f"VALUES ('category', '{winner.id}', '{loser.id}', '{merge.reason.replace("'", "''")}', {merge.confidence});\n")
                    
                    f.write(f"    END IF;\n")
                
                f.write("END $$;\n\n")
        
        print(f"  Wrote {sql_path}")
    
    def _generate_sql_series_moves(self, output_dir: Path, apply: bool):
        """030_series_fix.sql"""
        sql_path = output_dir / '030_series_fix.sql'
        with open(sql_path, 'w', encoding='utf-8') as f:
            f.write("-- Series Category Corrections\n\n")
            
            if not self.series_moves:
                f.write("-- No series moves needed\n")
                return
            
            for move in self.series_moves:
                series = self.series[move.entity_id]
                f.write(f"-- Move series '{series.name}': category {move.from_value} -> {move.to_value}\n")
                f.write(f"UPDATE catalog_series SET category_id='{move.to_value}' WHERE id='{move.entity_id}';\n")
                f.write(f"INSERT INTO category_reclass_log (entity_type, entity_id, from_value, to_value, reason) "
                        f"VALUES ('series', '{move.entity_id}', '{move.from_value}', '{move.to_value}', "
                        f"'{move.reason.replace("'", "''")}');\n\n")
        
        print(f"  Wrote {sql_path}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Catalog Audit & Fix Script')
    parser.add_argument('--input_dir', type=str, default='sss', help='CSV input directory')
    parser.add_argument('--output_dir', type=str, default='audit_output', help='Output directory')
    parser.add_argument('--dry_run', action='store_true', help='Dry-run mode (default)')
    parser.add_argument('--apply', action='store_true', help='Apply mode (generate executables)')
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    if not args.apply:
        args.dry_run = True
    
    print("=" * 60)
    print("CATALOG DATA AUDIT & REMEDIATION")
    print("=" * 60)
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print("=" * 60)
    
    # Load data
    db = CatalogDB(input_dir)
    db.load_csvs()
    
    # Run audits
    db.audit_brand_duplicates()
    db.audit_category_duplicates()
    db.audit_series_category_mismatches()
    
    # Generate reports
    db.generate_report(output_dir)
    db.generate_sql(output_dir, apply=args.apply)
    
    print("\n" + "=" * 60)
    print("AUDIT COMPLETE")
    print(f"Review outputs in: {output_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()
