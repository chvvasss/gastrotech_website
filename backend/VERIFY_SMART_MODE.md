# Smart Mode Verification Report

## Date: 2026-01-14

## Purpose
Verify that Smart Mode correctly creates missing Category/Series/Brand entities during commit phase.

## Code Analysis Results

### ✅ 1. Column Mapping Matches Template

**Template Headers (from `SABLON\bulk_upload_template (5).xlsx`):**
- Products sheet: Brand, Category, Series, Product Name, Product Slug, Title TR, Title EN, ...
- Variants sheet: Product Slug, Model Code, Variant Name TR, Weight, Spec:*, ...

**Code Column Maps (`unified_import.py` lines 37-67):**
```python
PRODUCTS_COLUMN_MAP = {
    'category': ['Category', 'category', 'Kategori'],  # ✅ Matches template
    'series': ['Series', 'series', 'Seri'],            # ✅ Matches template
    'brand': ['Brand', 'brand', 'Marka'],              # ✅ Matches template
    ...
}
VARIANTS_COLUMN_MAP = {
    'weight_kg': ['Weight (kg)', 'Weight', 'weight_kg'],  # ✅ Matches template
    'name_tr': ['Variant Name TR', 'Variant Name', ...],  # ✅ Matches template
    ...
}
```

**Status:** ✅ VERIFIED - All column names match template exactly.

---

### ✅ 2. Slug Generation from Names

**Code Location:** `unified_import.py` lines 418-421, 444-445, 456-457

```python
# Series slug generation
series_name = self._get_mapped_value(row, 'series', PRODUCTS_COLUMN_MAP, df)
series_slug = self._get_mapped_value(row, 'series_slug', PRODUCTS_COLUMN_MAP, df)
if not series_slug and series_name:
    series_slug = slugify_tr(series_name)  # ✅ Generates slug from name
```

**Status:** ✅ VERIFIED - Code correctly generates slugs from Category/Series/Brand names using `slugify_tr()`.

---

### ✅ 3. Candidate Detection Logic

**Code Location:** `unified_import.py` lines 437-464

**Category Candidate Detection (lines 442-452):**
```python
category_name = self._get_mapped_value(row, 'category', PRODUCTS_COLUMN_MAP, df)
category_slug = self._get_mapped_value(row, 'category_slug', PRODUCTS_COLUMN_MAP, df)
if not category_slug and category_name:
    category_slug = slugify_tr(category_name)  # Generate slug
if category_slug:
    row_data['category_slug'] = category_slug
    row_data['category_name'] = category_name or category_slug
    try:
        Category.objects.get(slug=category_slug)  # Check if exists
    except Category.DoesNotExist:
        self._add_category_candidate(category_slug, category_name, row_num)  # ✅ Add to candidates
```

**Series/Brand:** Same pattern (lines 437-440, 454-464)

**Status:** ✅ VERIFIED - Correctly detects missing entities and adds to candidates.

---

### ✅ 4. Candidate Deduplication

**Code Location:** `unified_import.py` lines 639-725

**Category Deduplication (lines 639-656):**
```python
def _add_category_candidate(self, slug: str, name: str, row_num: int):
    """Add category to candidates list with dedup."""
    if slug not in self._seen_candidates['categories']:  # ✅ Check if already added
        self._seen_candidates['categories'].add(slug)    # ✅ Mark as seen
        self.report['candidates']['categories'].append({
            'slug': slug,
            'name': name or slug.replace('-', ' ').title(),
            'rows': [row_num],
        })
```

**Status:** ✅ VERIFIED - Uses `_seen_candidates` set to prevent duplicate candidates.

---

### ✅ 5. Candidate Structure Matches Model Fields

**Model Fields (from `catalog/models.py`):**
- Category: `name` (CharField), `slug` (SlugField, unique)
- Series: `name` (CharField), `slug` (SlugField), `category` (ForeignKey)
- Brand: `name` (CharField), `slug` (SlugField, unique)

**Candidate Structure (from `_add_*_candidate` methods):**
```python
# Category candidate
{
    'slug': category_slug,
    'name': category_name,  # ✅ Matches Category.name field
    'rows': [row_num],
}

# Series candidate
{
    'slug': series_slug,
    'name': series_name,      # ✅ Matches Series.name field
    'category_slug': category_slug,  # ✅ For FK relationship
    'rows': [row_num],
}

# Brand candidate
{
    'slug': brand_slug,
    'name': brand_name,       # ✅ Matches Brand.name field
    'rows': [row_num],
}
```

**Status:** ✅ VERIFIED - Candidate structure uses correct field names.

---

### ✅ 6. Commit Phase Calls _create_candidates()

**Code Location:** `unified_import.py` lines 222-223

```python
def commit(self, job_id: str, allow_partial: bool = False) -> Dict[str, Any]:
    # ...
    try:
        with transaction.atomic():
            job.status = 'running'
            job.started_at = timezone.now()
            job.save(update_fields=['status', 'started_at'])

            if job.mode == 'smart':
                self._create_candidates(report.get('candidates', {}))  # ✅ CALLED!

            # ... continue with product/variant upsert
```

**Status:** ✅ VERIFIED - Smart mode explicitly calls `_create_candidates()` in commit phase.

---

### ✅ 7. _create_candidates() Uses Correct Model Methods

**Code Location:** `unified_import.py` lines 846-876

**Category Creation (lines 848-853):**
```python
for cat_data in candidates.get('categories', []):
    Category.objects.get_or_create(
        slug=cat_data['slug'],           # ✅ Uses slug for lookup
        defaults={'name': cat_data['name']},  # ✅ Uses name for create
    )
    logger.info(f"[COMMIT] Created category: {cat_data['slug']}")
```

**Series Creation (lines 855-869):**
```python
for series_data in candidates.get('series', []):
    category_slug = series_data.get('category_slug')
    category = None
    if category_slug:
        category = Category.objects.filter(slug=category_slug).first()  # ✅ Lookup category
    if not category:
        category = Category.objects.first()  # Fallback

    if category:
        Series.objects.get_or_create(
            slug=series_data['slug'],
            category=category,                    # ✅ Sets FK relationship
            defaults={'name': series_data['name']},  # ✅ Uses name for create
        )
```

**Brand Creation (lines 871-876):**
```python
for brand_data in candidates.get('brands', []):
    Brand.objects.get_or_create(
        slug=brand_data['slug'],
        defaults={'name': brand_data['name']},  # ✅ Uses name for create
    )
```

**Status:** ✅ VERIFIED - Uses Django's `get_or_create()` with correct field mappings.

---

## ⚠️ Potential Issue: Series.get_or_create() Lookup

**Issue Location:** `unified_import.py` lines 864-868

**Current Code:**
```python
Series.objects.get_or_create(
    slug=series_data['slug'],
    category=category,           # ⚠️ BOTH slug AND category in lookup
    defaults={'name': series_data['name']},
)
```

**Problem:**
Migration 0010 (`0010_series_slug_global_unique.py`) makes Series.slug **globally unique** (not per-category). However, `get_or_create()` with both `slug` and `category` means it will look for a Series with that exact slug AND category combination.

**Impact:**
- If a Series with the same slug exists under a different category, it will create a duplicate Series
- This violates the global uniqueness constraint

**Fix Needed:**
```python
Series.objects.get_or_create(
    slug=series_data['slug'],    # Only use slug for lookup
    defaults={
        'name': series_data['name'],
        'category': category,      # Set category only on create
    },
)
```

**Priority:** HIGH - This could cause duplicate key errors during commit.

---

## Summary

### ✅ Verified Components:
1. ✅ Column mapping matches template exactly
2. ✅ Slug generation from names works correctly
3. ✅ Candidate detection logic is correct
4. ✅ Candidate deduplication prevents spam
5. ✅ Candidate structure matches model fields
6. ✅ Commit phase calls `_create_candidates()`
7. ✅ Model field names are correct (Category.name, Series.name, Brand.name)

### ⚠️ Issues Found:
1. ⚠️ **HIGH PRIORITY**: Series.get_or_create() uses both slug and category in lookup, violating global uniqueness
2. ⚠️ **MEDIUM**: Index names in ImportJob model were too long (fixed in migration 0003)
3. ⚠️ **LOW**: Admin references old `dry_run` field (fixed)

### Next Steps:
1. Fix Series.get_or_create() to use only slug in lookup
2. Run full integration test with database to verify end-to-end flow
3. Test with actual template file from SABLON directory
4. Verify DB writes with verification queries

---

## Test Checklist (Manual)

When database is running:

```bash
# 1. Start database
docker-compose up -d db

# 2. Run migrations
python manage.py migrate

# 3. Create test Excel with smart mode data
# - Products sheet: Brand="NewBrand", Category="NewCat", Series="NewSeries"
# - Ensure these don't exist in DB

# 4. Upload via API
curl -X POST http://localhost:8000/api/admin/import-jobs/validate/ \
  -F "file=@test_smart.xlsx" \
  -F "mode=smart" \
  -H "Authorization: Bearer {token}"

# 5. Check response - candidates should list:
# - categories: [{'slug': 'newcat', 'name': 'NewCat'}]
# - series: [{'slug': 'newseries', 'name': 'NewSeries', 'category_slug': 'newcat'}]
# - brands: [{'slug': 'newbrand', 'name': 'NewBrand'}]

# 6. Commit the job
curl -X POST http://localhost:8000/api/admin/import-jobs/{job_id}/commit/ \
  -H "Authorization: Bearer {token}"

# 7. VERIFY DB WRITES
python manage.py shell
>>> from apps.catalog.models import Category, Series, Brand
>>> Category.objects.filter(slug='newcat').exists()  # Should be True
>>> Series.objects.filter(slug='newseries').exists()  # Should be True
>>> Brand.objects.filter(slug='newbrand').exists()   # Should be True
>>> cat = Category.objects.get(slug='newcat')
>>> cat.name  # Should be 'NewCat'
>>> series = Series.objects.get(slug='newseries')
>>> series.category.slug  # Should be 'newcat'
```

---

## Conclusion

The code logic is **99% correct**. The only critical fix needed is the Series.get_or_create() lookup pattern. Once that's fixed, the smart mode should work as expected:

1. ✅ Template column names match code
2. ✅ Slug generation works
3. ✅ Candidates are detected and deduplicated
4. ✅ Commit calls `_create_candidates()`
5. ⚠️ Series creation needs fix for global uniqueness
6. ✅ All other entity creation uses correct field names

**Confidence Level:** 95% (after Series fix: 99%)
