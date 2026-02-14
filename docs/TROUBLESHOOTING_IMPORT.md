# Import Troubleshooting Guide

**Version**: V5
**Last Updated**: 2026-01-15
**Audience**: End users, support staff, administrators

---

## Table of Contents

1. [Quick Diagnostic](#quick-diagnostic)
2. [Validation Errors](#validation-errors)
3. [Commit Issues](#commit-issues)
4. [Report Issues](#report-issues)
5. [Template Issues](#template-issues)
6. [Data Issues](#data-issues)
7. [Performance Issues](#performance-issues)
8. [Advanced Troubleshooting](#advanced-troubleshooting)
9. [Getting Help](#getting-help)

---

## Quick Diagnostic

### Symptom → Cause → Fix Table

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| "Brand is required" error | Missing Brand column or empty values | Add Brand column with valid brand slugs |
| "Category is required" error | Missing Category column or empty values | Add Category column with valid category slugs |
| "Series is required" error | Missing Series column or empty values | Add Series column with valid series slugs |
| "Product not found" error | Variant references non-existent product | Add product to Products sheet or use existing slug |
| "Series-Category mismatch" | Series belongs to different category | Use correct category for existing series |
| File upload fails | File too large (>10MB) | Split into multiple smaller files |
| Validation timeout | Too many rows (>10,000) | Split into multiple files |
| Commit shows success but entities missing | **PREVENTED in V5** - db_verify checks this | If still occurs, report as critical bug |
| Report download fails | Browser/network issue | Retry or use different browser |
| Duplicate model codes | Same model_code in multiple rows | System auto-renames (GKO-6010 → GKO-6010-2) |

---

## Validation Errors

### 1. "Brand is required"

**Symptom**: Validation fails with error on Brand column

**Error Message**:
```
Row 5, Column: Brand
Severity: ERROR
Message: Brand is required
Expected: Brand slug (e.g., acme, beta-corp)
```

**Cause**:
- Missing Brand column in your file
- Empty/blank Brand values in rows

**Fix**:
1. Ensure your file has a "Brand" column (or "brand_slug")
2. Fill in all Brand values with valid brand slugs
3. Brand slugs must be lowercase, hyphenated (e.g., `gastrotech`, `acme-corp`)

**In Smart Mode**: Missing brands will be auto-created as candidates
**In Strict Mode**: All brands must exist in database before import

---

### 2. "Category is required"

**Symptom**: Validation fails with error on Category column

**Error Message**:
```
Row 8, Column: Category
Severity: ERROR
Message: Category is required
Expected: Category slug (e.g., electronics, furniture)
```

**Cause**: Missing or empty Category values

**Fix**:
1. Add "Category" column (or "category_slug")
2. Fill in valid category slugs
3. Categories must be lowercase, hyphenated (e.g., `fryers`, `ovens`, `grills`)

**In Smart Mode**: Missing categories will be auto-created
**In Strict Mode**: Categories must exist before import

---

### 3. "Series is required"

**Symptom**: Validation fails with error on Series column

**Error Message**:
```
Row 12, Column: Series
Severity: ERROR
Message: Series is required
Expected: Series slug (e.g., premium-series, eco-line)
```

**Cause**: Missing or empty Series values

**Fix**:
1. Add "Series" column (or "series_slug")
2. Fill in valid series slugs
3. Series must be lowercase, hyphenated (e.g., `600-series`, `premium-line`)

**In Smart Mode**: Missing series will be auto-created with the specified Category
**In Strict Mode**: Series must exist before import

---

### 4. "Series-Category mismatch"

**Symptom**: Validation fails with series/category conflict

**Error Message**:
```
Row 15, Column: Series / Category
Severity: ERROR
Value: Series=premium-line, Category=ovens
Message: Series 'premium-line' belongs to category 'fryers' but file specifies 'ovens'
Expected: Category should be 'fryers' to match Series
```

**Cause**: The Series already exists in the database and is linked to a different Category than what's in your file

**Fix - Option 1** (Recommended): Update your file to use the correct Category
```
# Change this:
Series: premium-line, Category: ovens

# To this:
Series: premium-line, Category: fryers
```

**Fix - Option 2**: Use a different Series name
```
# If you really need ovens + premium-line:
Series: premium-line-ovens, Category: ovens
```

**Why this happens**: In V5, each Series is linked to exactly one Category. You cannot put the same Series under multiple Categories.

---

### 5. "Invalid foreign key"

**Symptom**: Reference to non-existent entity

**Error Message**:
```
Row 20, Column: Product Slug
Severity: ERROR
Value: industrial-fryer
Message: Product 'industrial-fryer' not found
Expected: Existing slugs: commercial-oven, gas-range, ...
```

**Cause**:
- Variant references a Product that doesn't exist
- Typo in product slug
- Product not in Products sheet (for multi-sheet imports)

**Fix - Option 1**: Add Product to Products sheet
```excel
# Products Sheet
Product Slug       | Title TR           | Series    | Brand      | Category
industrial-fryer   | Endüstriyel Fritöz | 600-series| gastrotech | fryers
```

**Fix - Option 2**: Correct the slug to match existing product
```excel
# Check existing products in database, then fix typo:
industrial-fryer → industrial-fryer-v2
```

**In Smart Mode**: Product candidates will be flagged as warnings (you'll need to create them manually or add to Products sheet)
**In Strict Mode**: This is a blocking error

---

### 6. "Duplicate slug"

**Symptom**: Same product slug appears multiple times

**Error Message**:
```
Row 25, Column: Product Slug
Severity: WARNING
Value: gas-oven
Message: Duplicate product slug 'gas-oven' found in rows 10, 25
Expected: Each product slug should appear only once
```

**Cause**: Multiple rows in Products sheet have the same slug

**Fix**:
- If they're truly the same product, remove duplicate rows
- If they're different products, use different slugs:
  ```
  gas-oven-small
  gas-oven-large
  gas-oven-commercial
  ```

**Note**: System will merge/overwrite duplicates during commit

---

### 7. "Model Code is required"

**Symptom**: Empty model_code in Variants sheet

**Error Message**:
```
Row 30, Column: Model Code
Severity: ERROR
Message: Model Code is required
Expected: Non-empty value like GKO9010
```

**Cause**: Missing or empty Model Code column

**Fix**:
1. Ensure "Model Code" column exists
2. Fill in unique model codes for each variant
3. Model codes must be unique across ALL variants

**Example**:
```
Model Code | Product Slug    | Name TR
GKO-6010   | gas-oven        | 6 Gözlü Gazlı Ocak
GKO-8010   | gas-oven        | 8 Gözlü Gazlı Ocak
```

---

### 8. "Invalid decimal"

**Symptom**: Invalid price or weight format

**Error Message**:
```
Row 35, Column: List Price
Severity: ERROR
Value: 15.000,50€
Message: Invalid decimal value for List Price: '15.000,50€'
Expected: Number like 15000.50 or 15000,50 or 15.000,50
```

**Cause**:
- Currency symbols (€, $, TL)
- Invalid number format

**Fix**: Remove currency symbols and use numeric format
```
# Wrong:
15.000,50€
$1,500.00
15 000,50

# Right:
15000.50
15000,50
15.000,50
1500.00
```

**Supported formats**:
- US format: `15000.50` (dot for decimal)
- EU format: `15.000,50` (dot for thousands, comma for decimal)
- Mixed: `15000,50` (comma for decimal)

---

## Commit Issues

### 1. "Created but not in DB" (NOW PREVENTED)

**Old Bug**: System showed success message but entities were missing from database

**V5 Fix**: The system now has `db_verify` that checks ALL created entities:
- After commit, system re-queries database for each created entity
- If ANY entity is missing, `db_verify.created_entities_found_in_db` = false
- Frontend MUST check this flag before showing success

**How it works**:
```json
{
  "status": "success",
  "db_verify": {
    "enabled": true,
    "created_entities_found_in_db": true,  ← MUST BE TRUE
    "created_product_slugs": ["gas-oven", "fryer-xl"],
    "created_variant_model_codes": ["GKO-6010", "FRY-200"],
    "verification_details": {
      "products_verified": true,
      "variants_verified": true
    }
  }
}
```

**If you see this flag as false**: Report immediately as critical bug with:
- Job ID
- Snapshot hash
- Full response JSON

---

### 2. Partial Commit Failures

**Symptom**: Some rows succeed, others fail during commit

**Error Message**:
```
Job Status: partial
Created: 45 variants
Errors: 5 rows failed
```

**Cause**:
- Database constraint violations on specific rows
- FK reference deleted between validate and commit (rare)

**Fix**:
1. Download report XLSX
2. Check "Issues" sheet for failed rows
3. Fix those specific rows
4. Re-import ONLY the failed rows (or entire file)

**Example workflow**:
```
1. Download report: GET /api/admin/import-jobs/{id}/report/
2. Open "Issues" sheet
3. See: Row 50 failed - "Product 'xyz' not found"
4. Fix: Create product 'xyz' or change variant to reference existing product
5. Re-import
```

---

### 3. Transaction Rollback

**Symptom**: Commit fails completely, all changes reverted

**Error Message**:
```
Job Status: failed
Message: Commit failed: Transaction rolled back
```

**Cause**:
- Database constraint violation (any row)
- Foreign key integrity error
- Unique constraint violation

**Why this is GOOD**: System uses atomic transactions - either ALL changes succeed or NONE do. Your database stays consistent.

**Fix**:
1. Review validation report for ALL errors (not just first few)
2. Fix all blocking errors
3. Re-upload and validate again
4. Only commit when validation shows zero errors

---

### 4. Snapshot Integrity Failure

**Symptom**: "Snapshot integrity check FAILED"

**Error Message**:
```
Snapshot integrity check FAILED for job abc-123.
Expected hash: 7a3d4f..., got: 9b2c1e...
Snapshot may have been tampered with.
```

**Cause**:
- Snapshot file corrupted (disk error, database issue)
- **Extremely rare** - indicates system integrity problem

**Fix**:
1. DO NOT retry commit on this job
2. Re-upload original file
3. Run validate again to create new snapshot
4. Commit the new job

**If this happens frequently**: Contact system administrator - may indicate:
- Database corruption
- Storage system issues
- Memory errors

---

## Report Issues

### 1. Report Download Fails

**Symptom**: Clicking "Download Report" shows error or downloads empty file

**Possible Causes**:
- Browser timeout (large reports)
- Network interruption
- Server-side error

**Fix - Try these in order**:
1. **Retry**: Click download button again
2. **Different browser**: Try Chrome, Firefox, or Edge
3. **Check job status**:
   ```
   GET /api/admin/import-jobs/{id}/
   Ensure status is not "validating" or "running"
   ```
4. **Download via curl** (if browser fails):
   ```bash
   curl -H "Authorization: Bearer <token>" \
        https://api.example.com/api/admin/import-jobs/{id}/report/ \
        -o report.xlsx
   ```

---

### 2. Missing Candidates Sheet

**Symptom**: Report XLSX has no "Candidates" sheet

**Cause**: No missing entities detected

**When this is normal**:
- **Strict mode**: Candidates sheet is always empty (strict mode doesn't create candidates)
- **All entities exist**: If all brands/categories/series already exist, no candidates needed

**When this is a problem**:
- **Smart mode with errors**: If you're in smart mode and getting "not found" errors, candidates should appear
- **Check Issues sheet**: Look for "missing_*_candidate" messages

---

### 3. Incorrect Row Numbers

**Symptom**: Error says "Row 50" but that row looks fine

**Cause**: Row numbers are **Excel row numbers** (1-indexed, including header)

**Understanding row numbers**:
```
Excel:
Row 1: Header (Model Code, Product Slug, ...)
Row 2: First data row (GKO-6010, gas-oven, ...)    ← Error shows "Row 2"
Row 3: Second data row (GKO-8010, gas-oven, ...)   ← Error shows "Row 3"

Your data (ignoring header):
Data row 1: GKO-6010  ← This is "Row 2" in errors
Data row 2: GKO-8010  ← This is "Row 3" in errors
```

**Fix**: Add 1 to your mental count when looking at errors
- Error "Row 2" = First data row (below header)
- Error "Row 50" = 49th data row

---

## Template Issues

### 1. Wrong Template Version

**Symptom**: Validation fails with "missing required columns"

**Cause**: Using old template (pre-V5) with new column names

**V5 Required Columns**:

**Products Sheet**:
- Brand (or brand_slug)
- Category (or category_slug)
- Series (or series_slug)
- Product Name (or name)
- Product Slug (or slug)
- Title TR (or title_tr)

**Variants Sheet**:
- Model Code (or model_code)
- Product Slug (or product_slug)

**Fix**: Download latest template
```
GET /api/admin/import-jobs/template/?format=xlsx&include_examples=true
```

---

### 2. Missing Required Sheets

**Symptom**: "No Products/Variants sheets found"

**Cause**:
- Excel file has wrong sheet names
- Using CSV when multi-sheet needed

**Expected Sheet Names**:
- Must contain "product" (case-insensitive): "Products", "Product Data", "PRODUCTS"
- Must contain "variant" (case-insensitive): "Variants", "Variant Data", "VARIANTS"

**Fix**:
1. Rename sheets to "Products" and "Variants"
2. Or use exact template sheet names
3. For simple variant-only imports, use CSV or single-sheet XLSX

---

### 3. Column Order Wrong

**Symptom**: Values appear in wrong fields after import

**Cause**: Column order matters if using header-less CSV (not recommended)

**Fix**:
- **Always include header row** with column names
- Column order doesn't matter if headers are present
- System matches by column name, not position

---

### 4. Invalid Column Names

**Symptom**: "Missing required columns" despite columns being present

**Cause**: Typo or unexpected column name

**Column Aliases (all accepted)**:

| Required Field | Accepted Column Names |
|----------------|----------------------|
| Brand | Brand, brand, Brand Slug, brand_slug, Marka |
| Category | Category, category, Category Slug, category_slug, Kategori |
| Series | Series, series, Series Slug, series_slug, Seri |
| Product Name | Product Name, product_name, name, Ürün Adı |
| Product Slug | Product Slug, product_slug, slug |
| Model Code | Model Code, model_code, Model Kodu |
| Variant Name TR | Variant Name TR, Variant Name, name_tr, Varyant Adı |

**Fix**: Use any of the accepted column names above

---

## Data Issues

### 1. Series-Category Mismatch

**Symptom**: "Series 'premium-line' belongs to category 'fryers' but file specifies 'ovens'"

**Root Cause**: Series was previously created under a different Category

**Fix - Option 1**: Change Category in your file to match existing Series
```excel
# If Series "premium-line" belongs to "fryers" in database:
Series         | Category
premium-line   | fryers     ← Change to this
```

**Fix - Option 2**: Create new Series with different name
```excel
Series             | Category
premium-line-ovens | ovens    ← New unique name
```

**Fix - Option 3** (Admin only): Update Series.category in database
```python
# Django shell (ONLY if you're sure)
series = Series.objects.get(slug='premium-line')
series.category = Category.objects.get(slug='ovens')
series.save()
```

---

### 2. Duplicate Model Codes

**Symptom**: Same model_code appears multiple times in file

**What V5 does automatically**:
```
Original file:
Row 10: GKO-6010
Row 25: GKO-6010  ← Duplicate!

After auto-disambiguation:
Row 10: GKO-6010
Row 25: GKO-6010-2  ← System renamed
```

**Check "Normalization" sheet in report** to see all auto-renames

**If this is wrong** (both should be same variant):
- Remove duplicate row
- Or merge data manually before import

---

### 3. Invalid Status Values

**Symptom**: Status field has unexpected value

**Valid Status Values**:
- `active`, `Active`, `aktif`, `yayinda` → active
- `draft`, `Draft`, `taslak` → draft
- `archived`, `Archived`, `arsivlenmis`, `pasif` → archived

**Invalid values default to**: `active`

**Fix**: Use one of the valid values above

---

### 4. Decimal Format Errors

**Symptom**: "Invalid decimal value"

**Cause**: Unsupported number format

**Supported Formats**:
```
✓ 15000.50      (US format)
✓ 15000,50      (EU format without thousands)
✓ 15.000,50     (EU format with thousands)
✓ 15,000.50     (US format with thousands - auto-detected)

✗ 15000.50€     (currency symbols)
✗ $15,000.50    (currency symbols)
✗ 15 000.50     (space as separator)
✗ 15'000.50     (apostrophe as separator)
```

**Fix**: Remove all non-numeric characters except dots and commas

---

## Performance Issues

### 1. Slow Validation

**Symptom**: Validation takes >2 minutes

**Likely Causes**:
- File too large (>10MB)
- Too many rows (>10,000)
- Complex Excel formatting (merged cells, formulas)

**Fix**:
1. **Split file**: Break into multiple files of ~5,000 rows each
2. **Simplify**: Remove Excel formatting, use simple data
3. **Use CSV**: CSV is faster than XLSX for large files

**Splitting example**:
```
Original: 15,000 variants
Split into:
- file1.xlsx: rows 1-5000
- file2.xlsx: rows 5001-10000
- file3.xlsx: rows 10001-15000
Import sequentially
```

---

### 2. Timeout Errors

**Symptom**: "Request timeout" or "Gateway timeout"

**Cause**: File too large or too many rows

**Limits**:
- Max file size: 10 MB (recommended)
- Max rows: 10,000 per file (recommended)
- Timeout: 2 minutes for validation, 5 minutes for commit

**Fix**:
1. Split into smaller files
2. Remove unnecessary columns (keep only required + changed fields)
3. Import during off-peak hours (less server load)

---

### 3. Memory Issues

**Symptom**: "Out of memory" or validation crashes

**Cause**: Excel file with complex formatting or embedded objects

**Fix**:
1. **Save as CSV**: Remove all Excel-specific features
2. **Remove images**: Delete embedded images/charts
3. **Simplify formulas**: Replace formulas with values (Paste Special → Values)
4. **Split file**: Break into smaller chunks

---

## Advanced Troubleshooting

### Enabling Debug Logging

**For developers/admins**: Enable detailed import logging

```python
# settings.py or Django shell
import logging

logger = logging.getLogger('apps.ops.services.unified_import')
logger.setLevel(logging.DEBUG)

# Now all import operations log detailed info
```

**Look for**:
```
[VALIDATE] Starting validation for file.xlsx (512345 bytes)
[CACHE] Loaded 50 categories, 120 series, 10 brands
[LOAD] Found Products sheet 'Products' with 100 rows
[LOAD] Found Variants sheet 'Variants' with 500 rows
[VALIDATE] Complete: 480 valid rows, 5 errors, 15 warnings
[SNAPSHOT] Created snapshot abc123 (hash=7a3d4f...)
[COMMIT] Starting commit for job abc-123
[COMMIT] Created category: new-category
[COMMIT] Created series: new-series (category=new-category)
[COMMIT] Complete: 3 categories, 2 brands, 5 series, 100 products, 480 variants
```

---

### Using Django Shell for Investigation

```python
python manage.py shell

from apps.ops.models import ImportJob
import json

# Load job
job = ImportJob.objects.get(id='<job-id>')

# Inspect report structure
report = job.report_json
print("Status:", report.get('status'))
print("Counts:", json.dumps(report.get('counts'), indent=2))

# Find specific error
issues = report.get('issues', [])
for issue in issues:
    if issue.get('severity') == 'error':
        print(f"Row {issue['row']}: {issue['message']}")

# Check candidates (smart mode)
candidates = report.get('candidates', {})
for entity_type, items in candidates.items():
    print(f"{entity_type}: {len(items)} candidates")

# Examine snapshot
if job.snapshot_file:
    snapshot_content = job.snapshot_file.bytes.decode('utf-8')
    snapshot = json.loads(snapshot_content)
    print("Products in snapshot:", len(snapshot.get('products_data', [])))
    print("Variants in snapshot:", len(snapshot.get('variants_data', [])))
```

---

### Checking Snapshot Integrity

```python
import hashlib

job = ImportJob.objects.get(id='<job-id>')

# Recompute hash
snapshot_content = job.snapshot_file.bytes.decode('utf-8')
actual_hash = hashlib.sha256(snapshot_content.encode('utf-8')).hexdigest()

# Compare
if actual_hash == job.snapshot_hash:
    print("✓ Snapshot integrity OK")
else:
    print(f"✗ INTEGRITY FAILURE!")
    print(f"  Expected: {job.snapshot_hash}")
    print(f"  Actual:   {actual_hash}")
```

---

### Examining Validation Details

```python
job = ImportJob.objects.get(id='<job-id>')
report = job.report_json

# Error breakdown by type
from collections import Counter
error_codes = [i.get('code') for i in report.get('issues', []) if i.get('severity') == 'error']
print("Error distribution:")
for code, count in Counter(error_codes).most_common():
    print(f"  {code}: {count}")

# Column-level errors
error_columns = [i.get('column') for i in report.get('issues', []) if i.get('severity') == 'error']
print("\nColumns with errors:")
for column, count in Counter(error_columns).most_common():
    print(f"  {column}: {count}")

# Sample error messages
print("\nFirst 5 errors:")
errors = [i for i in report.get('issues', []) if i.get('severity') == 'error'][:5]
for err in errors:
    print(f"  Row {err['row']}, {err['column']}: {err['message']}")
```

---

### Testing with Small Sample

Before importing large file:

1. **Extract first 10 rows** to test.xlsx
2. **Validate** the sample
3. **Fix any errors** in full file
4. **Import full file**

```python
# Python script to extract sample
import pandas as pd

# Read original
df = pd.read_excel('full_import.xlsx', sheet_name='Variants')

# Take first 10 rows
sample = df.head(10)

# Save
with pd.ExcelWriter('sample.xlsx') as writer:
    sample.to_excel(writer, sheet_name='Variants', index=False)

print("Sample created: sample.xlsx")
```

---

## Getting Help

### Information to Provide

When reporting an issue, include:

**Required**:
1. **Job ID**: UUID from import job (e.g., `abc12345-def6-7890-ghij-klmnopqrstuv`)
2. **Error message**: Exact text from UI or report
3. **File**: Upload original Excel/CSV file (sanitize sensitive data if needed)

**Optional but helpful**:
4. **Snapshot hash**: From job details
5. **Screenshots**: Of error messages or unexpected behavior
6. **Report XLSX**: Downloaded report file
7. **Browser/environment**: If UI-related issue

### How to Get Job ID

**From UI**:
- Import history page shows Job ID in table
- Job detail page shows UUID at top

**From API**:
```bash
# List recent jobs
curl -H "Authorization: Bearer <token>" \
     https://api.example.com/api/admin/import-jobs/

# Response includes job IDs
```

**From logs**:
```
[VALIDATE] Starting validation for job abc-123
```

---

### Sanitizing Files for Support

Before sharing files with support:

```python
import pandas as pd

# Read file
df = pd.read_excel('original.xlsx', sheet_name='Variants')

# Anonymize sensitive columns (optional)
df['sku'] = 'SKU-' + df.index.astype(str)
df['list_price'] = 1000.00

# Save sanitized version
df.to_excel('sanitized.xlsx', index=False)
```

---

### Common Self-Service Fixes

Before contacting support, try these:

| Problem | Self-Service Fix |
|---------|------------------|
| Validation errors | Download report, fix errors in "Issues" sheet, re-upload |
| Missing entities | Use smart mode, or pre-create entities manually |
| Slow validation | Split file into smaller chunks |
| Format errors | Use template, copy data into template columns |
| Series mismatch | Check existing series-category mappings, update file |
| Timeout | Reduce file size, import during off-peak hours |

---

### Contact Information

**For users**:
- Check this guide first
- Review downloaded XLSX report "Issues" sheet
- Try fixes documented above

**For support staff**:
- Escalate if: Snapshot integrity failure, DB verification failure, or system crashes
- Provide: Job ID, snapshot hash, full logs

**For developers**:
- Review: `OPS_RUNBOOK_IMPORT.md` for operational procedures
- Check: Django logs, PostgreSQL query logs
- Debug: Django shell with job inspection commands above

---

## Appendix: Error Code Reference

### Complete Error Code List

| Code | Severity | Meaning | Fix |
|------|----------|---------|-----|
| `missing_required_columns` | ERROR | Required column(s) not found in file | Add missing columns using template |
| `required_field_missing` | ERROR | Required field is empty/null | Fill in the required field |
| `invalid_foreign_key` | ERROR | Referenced entity doesn't exist | Create entity or fix reference |
| `series_category_mismatch` | ERROR | Series belongs to different category | Use correct category or different series |
| `invalid_decimal` | ERROR | Invalid number format | Use numeric format (no symbols) |
| `invalid_integer` | ERROR | Invalid integer format | Use whole numbers only |
| `duplicate_slug` | WARNING | Same slug used multiple times | Use unique slugs or remove duplicates |
| `missing_category_candidate` | INFO | Category will be created (smart mode) | No action needed (auto-created) |
| `missing_series_candidate` | INFO | Series will be created (smart mode) | No action needed (auto-created) |
| `missing_brand_candidate` | INFO | Brand will be created (smart mode) | No action needed (auto-created) |
| `missing_product_candidate` | WARNING | Product needs to be created | Add to Products sheet or create manually |
| `fatal_error` | ERROR | System error during processing | Contact support with job ID |

---

**End of Troubleshooting Guide**
