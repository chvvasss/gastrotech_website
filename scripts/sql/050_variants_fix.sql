-- Variant SKU Normalization & Spec Harmonization
-- Phase 5: Standardize SKUs, normalize numeric specs

-- Step 1: Normalize SKU format (uppercase, trim)
UPDATE catalog_variant
SET sku = upper(trim(sku))
WHERE sku IS NOT NULL;

-- Step 2: Check SKU collision rate
DO $$
DECLARE
    total_variants INTEGER;
    duplicate_skus INTEGER;
    collision_rate FLOAT;
BEGIN
    SELECT COUNT(*) INTO total_variants FROM catalog_variant WHERE sku IS NOT NULL;
    
    SELECT COUNT(*) INTO duplicate_skus
    FROM (
        SELECT sku FROM catalog_variant
        WHERE sku IS NOT NULL
        GROUP BY sku
        HAVING COUNT(*) > 1
    ) sub;
    
    collision_rate := duplicate_skus::FLOAT / NULLIF(total_variants, 0);
    
    RAISE NOTICE 'SKU Collision Rate: % (% duplicates / % total)', collision_rate, duplicate_skus, total_variants;
    
    IF collision_rate > 0.02 THEN
        RAISE NOTICE 'High collision rate - SKU scope should be per-product';
    ELSE
        RAISE NOTICE 'Low collision rate - SKU can be globally unique';
    END IF;
END $$;

-- Step 3: Resolve SKU conflicts (global uniqueness)
-- Append product_id suffix for duplicates

DO $$
DECLARE
    collision RECORD;
    counter INTEGER;
BEGIN
    FOR collision IN
        SELECT sku, array_agg(id) AS variant_ids
        FROM catalog_variant
        WHERE sku IS NOT NULL
        GROUP BY sku
        HAVING COUNT(*) > 1
    LOOP
        -- Keep first, rename others
        FOR i IN 2..array_length(collision.variant_ids, 1) LOOP
            counter := 1;
            UPDATE catalog_variant
            SET sku = collision.sku || '-' || counter
            WHERE id = collision.variant_ids[i];
            counter := counter + 1;
        END LOOP;
    END LOOP;
END $$;

-- Step 4: Normalize numeric specs (if stored as JSONB)
-- Example: weight_kg, dimensions, power_kw
-- This is a template - adapt to actual spec keys

UPDATE catalog_variant
SET specs = jsonb_set(
    specs,
    '{weight_kg}',
    to_jsonb(
        regexp_replace(
            regexp_replace(specs->>'weight_kg', '[^0-9.,]', '', 'g'),
            ',', '.', 'g'
        )::NUMERIC
    )
)
WHERE specs ? 'weight_kg'
  AND specs->>'weight_kg' IS NOT NULL;

-- Verification queries
-- 1. No SKU duplicates
SELECT sku, COUNT(*) AS cnt
FROM catalog_variant
WHERE sku IS NOT NULL
GROUP BY sku
HAVING COUNT(*) > 1;

-- 2. No invalid numeric specs
SELECT id, specs->>'weight_kg' AS weight
FROM catalog_variant
WHERE specs ? 'weight_kg'
  AND NOT (specs->>'weight_kg' ~ '^[0-9]+(\.[0-9]+)?$');
