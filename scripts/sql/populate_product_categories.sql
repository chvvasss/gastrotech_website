-- Populate product.category_id from series.category_id
-- Generated from CSV analysis

-- This fixes the issue where products have no direct category link

UPDATE catalog_product SET category_id='ff725d2f-00e7-44cf-961c-d0b16be5b5f1' WHERE id='b76be88b-98eb-44e2-9156-b2b9ebf97fb2';
UPDATE catalog_product SET category_id='ff725d2f-00e7-44cf-961c-d0b16be5b5f1' WHERE id='9f2751be-6114-40d4-a61d-e5bfbab98c87';
UPDATE catalog_product SET category_id='ff725d2f-00e7-44cf-961c-d0b16be5b5f1' WHERE id='02c26640-7079-4463-85d4-d213bde1a4be';
UPDATE catalog_product SET category_id='ff725d2f-00e7-44cf-961c-d0b16be5b5f1' WHERE id='0f36a357-cf58-49f0-8dc8-3e465d58e1e4';
UPDATE catalog_product SET category_id='ff725d2f-00e7-44cf-961c-d0b16be5b5f1' WHERE id='c47b365f-3e66-4048-b66d-71a5f3603184';
UPDATE catalog_product SET category_id='ff725d2f-00e7-44cf-961c-d0b16be5b5f1' WHERE id='272a8142-2fc0-4ce4-bad9-5508f3bd4f5f';
UPDATE catalog_product SET category_id='ff725d2f-00e7-44cf-961c-d0b16be5b5f1' WHERE id='92ddc425-cacb-47e7-91c2-a365ceae9831';
UPDATE catalog_product SET category_id='ff725d2f-00e7-44cf-961c-d0b16be5b5f1' WHERE id='485f8d13-75ff-4a4e-bdaa-78e723fbb268';
UPDATE catalog_product SET category_id='ff725d2f-00e7-44cf-961c-d0b16be5b5f1' WHERE id='222d07ce-fd53-454b-a1fb-3a2759742d24';
UPDATE catalog_product SET category_id='ff725d2f-00e7-44cf-961c-d0b16be5b5f1' WHERE id='d4769f9b-70f3-47cd-bc31-f0b4cd7bbfa4';

-- ... and 242 more updates

-- Or use this batch approach:
UPDATE catalog_product p
SET category_id = s.category_id
FROM catalog_series s
WHERE p.series_id = s.id
  AND p.category_id IS NULL
  AND s.category_id IS NOT NULL;
