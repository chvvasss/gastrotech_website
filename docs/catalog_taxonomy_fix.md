# Catalog Taxonomy Fix - Firinlar

## Root Cause Summary
- **Taxonomy drift**: `firinlar` category was seeded under `pisirme-ekipmanlari`, despite being a top-level category.
- **Filtering mismatch**: Products were fetched with recursive category matching, but series/brand lists used direct category matching only, causing empty brand/series panels in legacy routes.
- **Import consistency gap**: Product `category` was not set during import, leaving denormalized fields out of sync with series.

## Fixes Applied
### Backend
- Added **optional descendant filtering** via `include_descendants` for:
  - `GET /api/v1/series/?category=...`
  - `GET /api/v1/brands/?category=...`
  - `GET /api/v1/products/?category=...` (default remains recursive unless explicitly disabled)
- Brand filtering now uses **union of active products + explicit BrandCategory links** for category scopes.
- Import now sets `product.category = series.category` for consistency.

### Data Integrity
- Added **`catalog_fix_taxonomy` management command** (dry-run by default) to:
  - Re-parent `firinlar` to root (if needed)
  - Move oven-related subcategories from `pisirme-ekipmanlari` under `firinlar`
  - Sync `product.category` from `series.category`
  - Backfill `BrandCategory` links from active products

### Frontend
- Added canonical redirect for **legacy URLs**:
  - `/kategori/pisirme-ekipmanlari/?subcategory=firinlar`
  - Redirects to `/kategori/firinlar` (preserves other params)
- Category page now passes `include_descendants` when filtering brands/series/products for parent categories to avoid empty panels.

### Seed / Import Protection
- Updated `seed_pisirme_categories.py` to **keep `firinlar` as root** and move oven subcategories under it.
- Import pipeline now keeps product category in sync with series category.

## Management Command
```
python manage.py catalog_fix_taxonomy
python manage.py catalog_fix_taxonomy --apply
```
Optional flags:
- `--skip-subcategory-moves`
- `--skip-product-sync`
- `--skip-brand-links`

## Audit Script
```
python scripts/catalog_audit.py --root-slug firinlar --legacy-parent-slug pisirme-ekipmanlari
```

### Run Log (2026-01-22 15:46:18)
Dry-run output: `docs/_runs/catalog_fix_taxonomy_dryrun.txt`
- Planned: move 3 oven subcategories under Firinlar
- Planned: sync 11 products from series.category
- Planned: ensure 20 brand-category pairs

Apply output: `docs/_runs/catalog_fix_taxonomy_apply.txt`
- Updated 11 products with series.category
- Created 0 BrandCategory links

Audit outputs:
- Before: `docs/_runs/catalog_audit_before.txt`
- After: `docs/_runs/catalog_audit_after.txt`

Audit summary (before -> after):
- Immediate children: 4 -> 7
- Descendant scope categories: 5 -> 8
- Series in scope: 23 -> 37
- Active products in scope: 28 -> 28
- Brands with active products: 28 -> 28
- Brands linked via BrandCategory: 11 -> 13
- Products with category != series.category: 11 -> 0
- Legacy parent children count: 4 -> 1

### Audit Output (files)
See `docs/_runs/catalog_audit_before.txt` and `docs/_runs/catalog_audit_after.txt` for full output.

## Final Verification
Run timestamp: 2026-01-22 16:37:38

Backend:
- Tests: `docs/_runs/backend_tests_recursive_category_filters.txt`

Frontend:
- Tests: `docs/_runs/frontend_tests.txt`
- Lint: `docs/_runs/frontend_lint.txt`

Redirects:
- Legacy -> Canonical: `docs/_runs/legacy_redirect_headers.txt` (308 to `/kategori/firinlar/`)
- Canonical 200: `docs/_runs/canonical_headers.txt`

API evidence (Firinlar, include_descendants=true):
- Brands: `docs/_runs/api_brands_in_firinlar.json` (count: 8)
- Series: `docs/_runs/api_series_in_firinlar.json` (count: 4)
- Products: `docs/_runs/api_products_in_firinlar.json` (page results: 24; next link present; audit shows 28 total active products in scope)

## Tests
Backend:
```
python manage.py test apps.catalog.tests.test_recursive_category_filters
```

Frontend:
```
cd frontend/public
npm test
```

## Risk & Rollback
- **Low risk**: changes are idempotent and scoped to Firinlar + related categories.
- **Rollback**: revert category parent changes and BrandCategory backfills by restoring from backup or running a targeted revert script.

## Assumptions
- `firinlar` is a **top-level** category by business definition.
- Oven-related subcategories currently under `pisirme-ekipmanlari` should be children of `firinlar`.
