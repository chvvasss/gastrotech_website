# Catalog Orphan Subcategory Fix

## Problem
Products that were assigned directly to a Root Category (e.g., "Fırınlar") but not to any Subcategory were **invisible** on the frontend Category Page if that category also had subcategories (e.g., "Pizza Fırınları").

### Context
- **Example Product**: "Elektrikli Buharlı Konveksiyonlu Dijital Fırın"
- **Location**: Associated with `prime-serisi`, which is directly under `Fırınlar`.
- **Root Cause**: The frontend `category/page.tsx` had mutually exclusive logic:
    - IF `hasSubcategories`: Show Subcategory Grid.
    - ELSE: Show Series Grid.
    - Result: Mixed content (Subcategories + Direct Series) meant the Direct Series were ignored.

## Solution

### 1. Frontend Logic Update
Modified `frontend/public/src/app/(site)/urunler/[categorySlug]/page.tsx` to handle the "Mixed Mode":
- If a category has **both** subcategories and direct series:
    1. Render the **Subcategory Grid** (Top).
    2. Render a separator header ("Diğer Ürünler" / "Modeller").
    3. Render the **Series Grid** for the direct series (Bottom).

### 2. Backend Data Integrity Tool
Created a management command to identify and optionally "fix" these orphans by moving them to a dedicated "Uncategorized" subcategory.

**Command**: `python manage.py fix_orphan_subcategories`
- **Default (Dry-Run)**: Lists all orphan series/products.
- **`--apply`**: 
    1. Creates a "Diğer" subcategory under the parent.
    2. Moves the orphan series to this new subcategory.
    3. Updates related products.

*Note: The frontend fix makes the `--apply` optional. The system now supports "orphan" display natively.*

## Verification
- **Data Analysis**: Run `python manage.py fix_orphan_subcategories` (dry-run) to confirm existence of orphan series (e.g., `prime-serisi` in `Fırınlar`).
- **Code Review**: Verified `page.tsx` logic allows `SeriesGrid` rendering when `hasSubcategories` is true, provided `hasDirectSeries` is also true.

## How to Verify (Manual)
1. Open [http://localhost:3000/kategori/firinlar](http://localhost:3000/kategori/firinlar)
2. Scroll below the "Alt Kategoriler" grid.
3. You should now see a section (e.g. "Fırınlar Modelleri") listing series like **Prime Serisi**.
4. Inside Prime Serisi, the target product is visible.
