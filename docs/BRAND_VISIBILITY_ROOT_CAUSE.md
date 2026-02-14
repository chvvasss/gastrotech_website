# Brand Visibility Root Cause Analysis

## Issue Summary
Brands added in the Admin panel for a specific category were not appearing on the Public Category page.
- **Error Message**: "Marka henüz bulunmuyor" / "No brand found yet"
- **Affected Route**: `/urunler/[categorySlug]`
- **Affected API**: `GET /api/v1/brands?category=[slug]`

## Root Cause
**Source of Truth Mismatch (Option 2)**
The Public API `BrandListView` was filtering brands by checking if they had *active products* in the requested category (`products__series__category__slug=category_slug`).
It ignored the explicit `Brand-Category` M2M relationship created in the Admin panel.
So, a brand explicitly assigned to a category but having 0 products (or 0 active products) would not appear.

## Resolution
Modified `backend/apps/catalog/views.py` to change the source of truth for the `category` filter:
- **Old Behavior**: Return brands with active products in category.
- **New Behavior**: Return brands explicitly assigned to category (via `BrandCategory` M2M table), regardless of product count.

## Verification
- **Reproduction**: Confirmed failure with script `repro_brand_visibility.py`.
- **Fix Verification**: Confirmed success with same script after fix.
- **Regression Test**: Added `backend/apps/catalog/tests/test_brand_visibility.py` to ensure this logic persists.
