-- Fix Dishwashing and Laundry Categories
BEGIN;

-- Moving flight-tip-bulasik-yikama-makinesi
UPDATE catalog_series SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE id = 'e63a1ff5-3c45-47d7-8c29-601c95001eb0';
UPDATE catalog_product SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE series_id = 'e63a1ff5-3c45-47d7-8c29-601c95001eb0';

-- Moving giyotin-tip-bulasik-makinesi
UPDATE catalog_series SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE id = '03b2fd06-52c5-410a-9f11-19ed84d18917';
UPDATE catalog_product SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE series_id = '03b2fd06-52c5-410a-9f11-19ed84d18917';

-- Moving giyotin-tip-bulasik-makinesi-manuel
UPDATE catalog_series SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE id = 'd1cbf05e-ca1d-47fa-842c-ec41c718d03b';
UPDATE catalog_product SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE series_id = 'd1cbf05e-ca1d-47fa-842c-ec41c718d03b';

-- Moving kazan-yikama-makinesi
UPDATE catalog_series SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE id = 'ebdef075-7164-41c8-8370-db3a39490572';
UPDATE catalog_product SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE series_id = 'ebdef075-7164-41c8-8370-db3a39490572';

-- Moving konveyorlu-bulasik-makineleri
UPDATE catalog_series SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE id = '532643f3-4a3e-4a94-9158-91a61d549ddb';
UPDATE catalog_product SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE series_id = '532643f3-4a3e-4a94-9158-91a61d549ddb';

-- Moving tezgah-alti-bardak-yikama-makinesi
UPDATE catalog_series SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE id = 'f8aa1c86-63a6-4077-b609-afa02f36c749';
UPDATE catalog_product SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE series_id = 'f8aa1c86-63a6-4077-b609-afa02f36c749';

-- Moving tezgah-alti-bulasik-makinesi
UPDATE catalog_series SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE id = 'e96ba399-2462-49d5-832e-76d9974a92b1';
UPDATE catalog_product SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE series_id = 'e96ba399-2462-49d5-832e-76d9974a92b1';

-- Moving tezgah-alti-bulasik-makinesi-vby500-serisi
UPDATE catalog_series SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE id = '273028fc-2f48-4bfe-a587-5bfc71df1531';
UPDATE catalog_product SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE series_id = '273028fc-2f48-4bfe-a587-5bfc71df1531';

-- Moving devrilir
UPDATE catalog_series SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE id = 'fbfb1253-04bb-47b0-a141-23943291431c';
UPDATE catalog_product SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE series_id = 'fbfb1253-04bb-47b0-a141-23943291431c';

-- Moving sym-serisi
UPDATE catalog_series SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE id = '8db4daf2-5413-48ab-bfbb-d23601d60d3e';
UPDATE catalog_product SET category_id = '38e2ee38-0e90-4974-aa2e-0794f297c32c' WHERE series_id = '8db4daf2-5413-48ab-bfbb-d23601d60d3e';

COMMIT;
