-- Product Normalization & Duplicate Merges
-- Phase 4: Detect duplicates via brand+category+canonical_title

-- Step 1: Add helper function for canonical form (if using PostgreSQL)
CREATE OR REPLACE FUNCTION canonical_form(text TEXT) RETURNS TEXT AS $$
BEGIN
    -- Simple version: lowercase + trim + collapse whitespace
    -- For full Turkish transliteration, use application layer
    RETURN regexp_replace(lower(trim(text)), '\s+', ' ', 'g');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Step 2: Detect product duplicates
-- This query identifies potential duplicates for manual review
-- Actual merge logic should use Python script for safety

WITH duplicate_groups AS (
    SELECT
        brand_id,
        category_id,
        canonical_form(name) AS canonical_name,
        array_agg(id ORDER BY id) AS product_ids,
        COUNT(*) AS duplicate_count
    FROM catalog_product
    WHERE brand_id IS NOT NULL
      AND category_id IS NOT NULL
    GROUP BY brand_id, category_id, canonical_form(name)
    HAVING COUNT(*) > 1
)
SELECT
    dg.*,
    array_agg(p.name) AS product_names,
    array_agg(p.slug) AS product_slugs
FROM duplicate_groups dg
JOIN catalog_product p ON p.id = ANY(dg.product_ids)
GROUP BY dg.brand_id, dg.category_id, dg.canonical_name, dg.product_ids, dg.duplicate_count;

-- Step 3: Fix slug collisions
-- Append brand slug to conflicting product slugs

DO $$
DECLARE
    collision RECORD;
    new_slug TEXT;
    counter INTEGER;
BEGIN
    FOR collision IN
        SELECT slug, array_agg(id) AS ids
        FROM catalog_product
        GROUP BY slug
        HAVING COUNT(*) > 1
    LOOP
        -- Keep first, rename others
        FOR i IN 2..array_length(collision.ids, 1) LOOP
            counter := 1;
            SELECT p.slug || '-' || b.slug INTO new_slug
            FROM catalog_product p
            JOIN catalog_brand b ON p.brand_id = b.id
            WHERE p.id = collision.ids[i];
            
            -- Ensure uniqueness
            WHILE EXISTS (SELECT 1 FROM catalog_product WHERE slug = new_slug) LOOP
                SELECT CONCAT(p.slug, '-', b.slug, '-', counter) INTO new_slug
                FROM catalog_product p
                JOIN catalog_brand b ON p.brand_id = b.id
                WHERE p.id = collision.ids[i];
                counter := counter + 1;
            END LOOP;
            
            -- Apply
            UPDATE catalog_product SET slug = new_slug WHERE id = collision.ids[i];
            
            -- Log redirect
            INSERT INTO slug_redirects (entity_type, old_slug, new_slug)
            VALUES ('product', collision.slug, new_slug)
            ON CONFLICT (entity_type, old_slug) DO NOTHING;
        END LOOP;
    END LOOP;
END $$;

-- Step 4: Ensure all products have category_id (populate from series if missing)
UPDATE catalog_product p
SET category_id = s.category_id
FROM catalog_series s
WHERE p.series_id = s.id
  AND p.category_id IS NULL
  AND s.category_id IS NOT NULL;

-- Verification: no products without category
-- SELECT COUNT(*) FROM catalog_product WHERE category_id IS NULL;
