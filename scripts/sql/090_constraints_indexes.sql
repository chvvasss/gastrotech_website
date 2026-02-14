-- Constraints & Indexes
-- Phase 6: Enforce data integrity and improve query performance

-- ============================================================================
-- NOT NULL Constraints
-- ============================================================================

-- Brands
ALTER TABLE catalog_brand ALTER COLUMN name SET NOT NULL;
ALTER TABLE catalog_brand ALTER COLUMN slug SET NOT NULL;

-- Categories
ALTER TABLE catalog_category ALTER COLUMN name SET NOT NULL;
ALTER TABLE catalog_category ALTER COLUMN slug SET NOT NULL;
-- Ensure series_mode is never NULL (default to 'disabled')
UPDATE catalog_category SET series_mode = 'disabled' WHERE series_mode IS NULL;
ALTER TABLE catalog_category ALTER COLUMN series_mode SET NOT NULL;
ALTER TABLE catalog_category ALTER COLUMN series_mode SET DEFAULT 'disabled';

-- Series
ALTER TABLE catalog_series ALTER COLUMN name SET NOT NULL;
ALTER TABLE catalog_series ALTER COLUMN slug SET NOT NULL;

-- Products
ALTER TABLE catalog_product ALTER COLUMN name SET NOT NULL;
ALTER TABLE catalog_product ALTER COLUMN slug SET NOT NULL;
ALTER TABLE catalog_product ALTER COLUMN status SET NOT NULL;
ALTER TABLE catalog_product ALTER COLUMN status SET DEFAULT 'draft';

-- Variants
ALTER TABLE catalog_variant ALTER COLUMN product_id SET NOT NULL;

-- ============================================================================
-- UNIQUE Constraints & Indexes
-- ============================================================================

-- Brand: global slug uniqueness
CREATE UNIQUE INDEX IF NOT EXISTS idx_brand_slug_unique
    ON catalog_brand(slug);

-- Category: hierarchical slug uniqueness (slug unique within same parent)
-- Use COALESCE to handle NULL parent_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_category_slug_parent_unique
    ON catalog_category(slug, COALESCE(parent_id, 0));

-- Series: global slug uniqueness
CREATE UNIQUE INDEX IF NOT EXISTS idx_series_slug_unique
    ON catalog_series(slug);

-- Product: global slug uniqueness
CREATE UNIQUE INDEX IF NOT EXISTS idx_product_slug_unique
    ON catalog_product(slug);

-- Variant: SKU uniqueness (only for non-null SKUs)
-- Adjust to per-product if collision rate > 2%
CREATE UNIQUE INDEX IF NOT EXISTS idx_variant_sku_unique
    ON catalog_variant(sku)
    WHERE sku IS NOT NULL;

-- Alternative: per-product SKU uniqueness (uncomment if needed)
-- DROP INDEX IF EXISTS idx_variant_sku_unique;
-- CREATE UNIQUE INDEX idx_variant_sku_product_unique
--     ON catalog_variant(product_id, sku)
--     WHERE sku IS NOT NULL;

-- ============================================================================
-- Foreign Key Indexes (improve JOIN performance)
-- ============================================================================

-- Category parent relationship
CREATE INDEX IF NOT EXISTS idx_category_parent_id
    ON catalog_category(parent_id)
    WHERE parent_id IS NOT NULL;

-- Series → Category
CREATE INDEX IF NOT EXISTS idx_series_category_id
    ON catalog_series(category_id)
    WHERE category_id IS NOT NULL;

-- Product → Brand
CREATE INDEX IF NOT EXISTS idx_product_brand_id
    ON catalog_product(brand_id)
    WHERE brand_id IS NOT NULL;

-- Product → Category
CREATE INDEX IF NOT EXISTS idx_product_category_id
    ON catalog_product(category_id)
    WHERE category_id IS NOT NULL;

-- Product → Series
CREATE INDEX IF NOT EXISTS idx_product_series_id
    ON catalog_product(series_id)
    WHERE series_id IS NOT NULL;

-- Variant → Product
CREATE INDEX IF NOT EXISTS idx_variant_product_id
    ON catalog_variant(product_id);

-- ============================================================================
-- Status Indexes (for filtering active/published items)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_brand_is_active
    ON catalog_brand(is_active);

CREATE INDEX IF NOT EXISTS idx_product_status
    ON catalog_product(status);

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- 1. Check constraint violations
-- Should return 0 for all:

-- NULL checks
SELECT 'Brands with NULL name' AS check, COUNT(*) AS violations
FROM catalog_brand WHERE name IS NULL
UNION ALL
SELECT 'Categories with NULL series_mode', COUNT(*)
FROM catalog_category WHERE series_mode IS NULL
UNION ALL
SELECT 'Products with NULL category', COUNT(*)
FROM catalog_product WHERE category_id IS NULL;

-- Uniqueness checks
SELECT 'Duplicate brand slugs' AS check, COUNT(*) AS violations
FROM (
    SELECT slug FROM catalog_brand GROUP BY slug HAVING COUNT(*) > 1
) sub
UNION ALL
SELECT 'Duplicate product slugs', COUNT(*)
FROM (
    SELECT slug FROM catalog_product GROUP BY slug HAVING COUNT(*) > 1
) sub
UNION ALL
SELECT 'Duplicate variant SKUs', COUNT(*)
FROM (
    SELECT sku FROM catalog_variant WHERE sku IS NOT NULL GROUP BY sku HAVING COUNT(*) > 1
) sub;

-- 2. Orphaned references
SELECT 'Products with invalid brand_id' AS check, COUNT(*) AS violations
FROM catalog_product p
LEFT JOIN catalog_brand b ON p.brand_id = b.id
WHERE p.brand_id IS NOT NULL AND b.id IS NULL
UNION ALL
SELECT 'Products with invalid category_id', COUNT(*)
FROM catalog_product p
LEFT JOIN catalog_category c ON p.category_id = c.id
WHERE p.category_id IS NOT NULL AND c.id IS NULL
UNION ALL
SELECT 'Series with invalid category_id', COUNT(*)
FROM catalog_series s
LEFT JOIN catalog_category c ON s.category_id = c.id
WHERE s.category_id IS NOT NULL AND c.id IS NULL
UNION ALL
SELECT 'Variants with invalid product_id', COUNT(*)
FROM catalog_variant v
LEFT JOIN catalog_product p ON v.product_id = p.id
WHERE p.id IS NULL;
