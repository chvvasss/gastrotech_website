# SUBCATEGORY NAVIGATION AUDIT & IMPLEMENTATION PLAN

**Date**: 2026-01-17
**Feature**: Subcategory Navigation Layer (Category → Subcategory → Brand → Series → Products)
**Status**: Planning Phase

---

## EXECUTIVE SUMMARY

This document audits the current navigation architecture and defines a complete implementation plan for adding a subcategory layer to the product catalog. The subcategory layer will enable hierarchical categorization (e.g., "Fırınlar" → "Pizza Fırını") while maintaining backward compatibility with existing category-first navigation.

**Current Flow**: Category → Brand → Series → Products → Product → Variants
**Target Flow**: Category → Subcategory → Brand → Series → Products → Product → Variants

---

## PHASE 0: CURRENT STATE AUDIT

### A. Category Model Analysis

**Location**: `backend/apps/catalog/models.py:163-236`

**Current Fields**:
```python
class Category(TimeStampedUUIDModel):
    name = CharField(max_length=160)
    slug = SlugField(max_length=160, unique=True, db_index=True)
    menu_label = CharField(max_length=100, blank=True)
    description_short = CharField(max_length=280, blank=True)
    order = PositiveIntegerField(default=0, db_index=True)
    is_featured = BooleanField(default=False, db_index=True)
    cover_media = ForeignKey(Media, null=True, blank=True)
    parent = ForeignKey("self", null=True, blank=True, related_name="children")  # ✅ ALREADY EXISTS
```

**Key Findings**:
- ✅ **Category model already has hierarchical support** via `parent` field (line 208-215)
- ✅ Indexes exist: `["parent", "order"]` (line 224)
- ✅ `__str__` method already shows hierarchy: `"{parent.name} > {name}"` (line 227-230)
- ✅ Ordering supports hierarchy: `["parent__order", "order", "name"]` (line 220)
- ⚠️ **No depth limit or tree validation** - could allow deep nesting
- ⚠️ **No helper properties**: `is_root`, `is_leaf`, `depth`, `breadcrumbs` missing

**Assessment**: Category model is **ready for subcategory usage** without migration. Only need to add helper properties and validation.

---

### B. Product Categorization Analysis

**Location**: `backend/apps/catalog/models.py:529-695`

**Current Product Linking**:
```python
class Product(TimeStampedUUIDModel):
    series = ForeignKey(Series, on_delete=PROTECT)          # Primary series
    primary_node = ForeignKey(TaxonomyNode, null=True)      # Taxonomy classification
    brand = ForeignKey(Brand, null=True)                    # Product brand
    # ... no direct category FK
```

**Location**: `backend/apps/catalog/models.py:293-362`

**Current Series Linking**:
```python
class Series(TimeStampedUUIDModel):
    category = ForeignKey(Category, on_delete=CASCADE)      # Parent category
    name = CharField(max_length=160)
    slug = SlugField(max_length=160, db_index=True)
    # ...
```

**Key Findings**:
- Product → Series → Category (indirect link)
- Series.category is the **primary categorization point**
- No direct Product.category FK exists
- TaxonomyNode exists but is series-specific (not category-specific)

**Decision**:
- **Option A**: Keep current structure, interpret Series.category as "leaf category" (subcategory)
- **Option B**: Add Product.category FK for direct leaf assignment
- **Chosen**: **Option A** (minimal changes, leverage existing Series.category)

**Rationale**:
- Products are already grouped by Series
- Series already has category FK
- Adding Product.category would create redundancy
- For subcategory support: Series.category should point to **leaf categories only**

---

### C. Current Navigation Routes & Query Params

**Frontend Route**: `/kategori/[slug]`
**Location**: `frontend/public/src/app/(site)/kategori/[slug]/page.tsx`

**Current URL Pattern**:
```
/kategori/<categorySlug>?brand=<brandSlug>&series=<seriesSlug>
```

**Current Query Parameters**:
- `brand`: Selected brand slug
- `series`: Selected series slug
- `cursor`: Pagination cursor

**Current Navigation Flow** (from `page.tsx:26-148`):
1. User visits `/kategori/<categorySlug>`
2. System fetches brands for that category
3. User selects brand → URL becomes `?brand=<slug>`
4. System fetches series for category + brand
5. User selects series → URL becomes `?brand=<slug>&series=<slug>`
6. System shows product listing

**Key Frontend Code**:
- Line 57-61: Fetch brands by category slug
- Line 63-68: Fetch series by category + brand
- Line 71-81: handleBrandSelect updates URL params
- Line 97-134: Brand/Series selection view (HUB)
- Line 137-296: Product listing view (SPOKE)

---

### D. Current API Endpoints

**Location**: `backend/apps/catalog/urls.py` & `backend/apps/catalog/views.py`

**Relevant Endpoints**:

1. **Category Tree** (line 37 of urls.py):
   - `GET /api/v1/categories/tree/`
   - View: `CategoryTreeView` (views.py:186-229)
   - ✅ Already returns hierarchical tree with children
   - ✅ Uses cache key: `categories_tree_key()`
   - Response: `CategoryTreeSerializer` with recursive children

2. **Category Detail** (line 38 of urls.py):
   - `GET /api/v1/categories/<slug>/`
   - View: `CategoryDetailView` (views.py:232-294)
   - Returns: Series list with product counts
   - ⚠️ Query param `?brand=<slug>` filters series by brand (line 257)

3. **Brand List** (line 44 of urls.py):
   - `GET /api/v1/brands/`
   - View: `BrandListView`
   - ⚠️ **No category filter parameter**

4. **Series List** (line 41 of urls.py):
   - `GET /api/v1/series/`
   - View: `SeriesListView`
   - ⚠️ **No category or brand filter parameters**

5. **Product List** (line 55 of urls.py):
   - `GET /api/v1/products/`
   - View: `ProductListView`
   - Uses `ProductFilter` for filtering

**Key Findings**:
- Category tree endpoint **already supports hierarchy**
- Brand/Series endpoints **lack category filtering**
- No endpoint for "get subcategories of a category"

---

### E. Import System Analysis

**Location**: `backend/apps/ops/import_api.py`

**Current Template Columns** (line 378-401):
```python
columns = [
    'model_code',
    'product_slug',
    'name_tr',
    'series_slug',      # Required for new products
    'title_tr',
    'brand_slug',
    'spec_*',
    # ... no taxonomy/category column
]
```

**Key Findings**:
- Import uses `series_slug` to link products
- No direct category assignment in import
- ⚠️ **No taxonomy/category hierarchy support**

**Impact**:
- Need to add category/subcategory columns
- Must support path syntax: `"Fırınlar > Pizza Fırını"`
- Smart mode should create missing subcategories

---

## PHASE 1: DATA MODEL ENHANCEMENTS

### 1.1 Category Model Helper Properties

**File**: `backend/apps/catalog/models.py`
**Location**: After line 236 (end of Category class)

**Add Helper Properties**:

```python
@property
def is_root(self) -> bool:
    """Check if this is a root category (no parent)."""
    return self.parent_id is None

@property
def is_leaf(self) -> bool:
    """Check if this is a leaf category (no children)."""
    return not self.children.exists()

@property
def depth(self) -> int:
    """Return depth in tree (0 = root, 1 = subcategory, etc.)."""
    depth = 0
    current = self.parent
    while current:
        depth += 1
        current = current.parent
    return depth

@property
def breadcrumbs(self) -> list:
    """Return list of ancestor categories including self."""
    crumbs = [self]
    current = self.parent
    while current:
        crumbs.insert(0, current)
        current = current.parent
    return crumbs

@property
def full_path(self) -> str:
    """Return breadcrumb path as string."""
    return " > ".join(c.name for c in self.breadcrumbs)

def get_descendants(self):
    """Get all descendant categories recursively."""
    descendants = []
    for child in self.children.all():
        descendants.append(child)
        descendants.extend(child.get_descendants())
    return descendants
```

**Validation Method**:

```python
def clean(self):
    """Validate category hierarchy."""
    super().clean()

    # Prevent circular references
    if self.parent:
        if self.parent == self:
            raise ValidationError("Category cannot be its own parent")

        # Check depth limit (max 2 levels: root + subcategory)
        if self.depth >= 2:
            raise ValidationError("Maximum category depth is 2 (root → subcategory)")

        # Check for circular reference in ancestors
        current = self.parent
        visited = {self.id}
        while current:
            if current.id in visited:
                raise ValidationError("Circular category reference detected")
            visited.add(current.id)
            current = current.parent
```

---

### 1.2 Series Categorization Rules

**Validation**: Series.category **must be a leaf category** (subcategory)

**File**: `backend/apps/catalog/models.py`
**Location**: Series model clean() method (after line 361)

```python
def clean(self):
    """Validate series category is a leaf."""
    super().clean()

    # Series should belong to leaf categories (subcategories)
    if self.category and not self.category.is_leaf:
        # Allow if category has no children yet (during migration)
        if self.category.children.exists():
            raise ValidationError({
                'category': f'Series must belong to a leaf category (subcategory). '
                           f'"{self.category.name}" has subcategories.'
            })
```

**Note**: This validation is **soft** to allow migration. During migration, root categories with series will remain valid until subcategories are added.

---

### 1.3 Product-Category Relationship

**Decision**: **No changes needed**

Products remain linked via Series → Category hierarchy:
- Product → Series (FK)
- Series → Category (FK)
- Category can be root or leaf

**Future Enhancement** (optional):
- Add `Product.category` FK for direct leaf assignment
- Add validation: `Product.category must be leaf`
- Add constraint: `Product.category must be descendant of Series.category`

---

## PHASE 2: BACKEND API ENHANCEMENTS

### 2.1 New Endpoints

#### A. Get Category Children
**Endpoint**: `GET /api/v1/categories/<slug>/children/`
**Purpose**: Fetch subcategories of a category

**Serializer**:
```python
class CategoryChildrenSerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description_short', 'cover_media',
                  'order', 'products_count']
```

**View**:
```python
@extend_schema(
    summary="Get category children (subcategories)",
    description="Returns immediate children of a category with product counts",
    tags=["Categories"],
)
class CategoryChildrenView(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = CategoryChildrenSerializer

    def get_queryset(self):
        parent_slug = self.kwargs['slug']
        parent = get_object_or_404(Category, slug=parent_slug)

        return (
            Category.objects
            .filter(parent=parent)
            .annotate(
                products_count=Count(
                    'series__products',
                    filter=Q(series__products__status='active'),
                    distinct=True
                )
            )
            .order_by('order', 'name')
        )
```

**URL**: Add to `backend/apps/catalog/urls.py`:
```python
path("categories/<slug:slug>/children/", CategoryChildrenView.as_view(), name="category-children"),
```

---

#### B. Enhanced Brand List with Category Filter

**Endpoint**: `GET /api/v1/brands/?category=<subcategory_slug>`
**Purpose**: Get brands that have products in a specific leaf category

**Update Existing View**: `BrandListView` in `views.py`

**Add Query Parameter Handler**:
```python
def get_queryset(self):
    queryset = Brand.objects.filter(is_active=True)

    # Filter by category (leaf category)
    category_slug = self.request.query_params.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)

        # Get brands that have products in this category
        queryset = queryset.filter(
            products__series__category=category,
            products__status='active'
        ).distinct()

    return queryset.order_by('order', 'name')
```

---

#### C. Enhanced Series List with Category & Brand Filter

**Endpoint**: `GET /api/v1/series/?category=<slug>&brand=<slug>`
**Purpose**: Get series filtered by category and optional brand

**Update Existing View**: `SeriesListView` in `views.py`

```python
def get_queryset(self):
    queryset = Series.objects.all()

    # Filter by category
    category_slug = self.request.query_params.get('category')
    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)

    # Filter by brand (products in series must have this brand)
    brand_slug = self.request.query_params.get('brand')
    if brand_slug:
        queryset = queryset.filter(
            products__brand__slug=brand_slug,
            products__status='active'
        ).distinct()

    return queryset.order_by('order', 'name')
```

---

#### D. Enhanced Product List with Subcategory Filter

**Endpoint**: `GET /api/v1/products/?category=<subcategory_slug>&brand=<slug>&series=<slug>`

**Update**: `ProductFilter` in `backend/apps/catalog/filters.py`

**Add category filter to existing filters**:
```python
class ProductFilter(filters.FilterSet):
    category = filters.CharFilter(method='filter_category')
    brand = filters.CharFilter(field_name='brand__slug')
    series = filters.CharFilter(field_name='series__slug')
    # ... existing filters

    def filter_category(self, queryset, name, value):
        """Filter by category slug (leaf category via series)."""
        return queryset.filter(series__category__slug=value)
```

---

### 2.2 Updated Category Tree Serializer

**File**: `backend/apps/catalog/serializers.py`

**Enhance CategoryTreeSerializer** to include counts:

```python
class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    products_count = serializers.IntegerField(read_only=True, default=0)
    subcategory_count = serializers.IntegerField(read_only=True, default=0)
    is_leaf = serializers.BooleanField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description_short', 'cover_media',
                  'order', 'is_featured', 'children', 'products_count',
                  'subcategory_count', 'is_leaf']

    def get_children(self, obj):
        # Use prefetched children if available
        children = getattr(obj, '_prefetched_children', obj.children.all())
        return CategoryTreeSerializer(children, many=True).data
```

**Update CategoryTreeView** to add counts:

```python
def get(self, request):
    # ... existing cache logic

    # Annotate counts
    all_categories = list(
        Category.objects
        .select_related("parent")
        .annotate(
            products_count=Count(
                'series__products',
                filter=Q(series__products__status='active'),
                distinct=True
            ),
            subcategory_count=Count('children', distinct=True)
        )
    )

    # Build children map with counts
    # ... existing tree building logic
```

---

## PHASE 3: PUBLIC UI FLOW UPDATES

### 3.1 New Navigation Flow

**Route**: `/kategori/<rootCategorySlug>`

**State Machine**:

```
State 1: ROOT CATEGORY VIEW
├─ URL: /kategori/<root>
├─ Shows: Subcategory selection grid
├─ Action: User selects subcategory
└─ Next: State 2

State 2: SUBCATEGORY + BRAND SELECTION
├─ URL: /kategori/<root>?subcategory=<sub>
├─ Shows: Brand selection grid
├─ Action: User selects brand
└─ Next: State 3

State 3: SUBCATEGORY + BRAND + SERIES SELECTION
├─ URL: /kategori/<root>?subcategory=<sub>&brand=<brand>
├─ Shows: Series selection grid
├─ Action: User selects series
└─ Next: State 4

State 4: PRODUCT LISTING
├─ URL: /kategori/<root>?subcategory=<sub>&brand=<brand>&series=<series>
├─ Shows: Product grid with filters
├─ Action: User browses products
└─ End
```

**Deep Link Support**:
- URL with `?subcategory=<sub>&brand=<brand>&series=<series>` → Skip to State 4
- URL with `?subcategory=<sub>&brand=<brand>` → Skip to State 3
- URL with `?subcategory=<sub>` → Skip to State 2

---

### 3.2 Frontend Component Updates

**File**: `frontend/public/src/app/(site)/kategori/[slug]/page.tsx`

**Key Changes**:

1. **Add subcategory state**:
```typescript
const selectedSubcategorySlug = searchParams.get("subcategory");
```

2. **Fetch subcategories** (if root category):
```typescript
const { data: subcategories = [] } = useQuery({
  queryKey: ["categories", "children", slug],
  queryFn: () => fetchCategoryChildren(slug),
  enabled: !!slug && !selectedSubcategorySlug && category?.is_leaf === false,
});
```

3. **Update brand/series fetching** to use subcategory:
```typescript
// Use subcategory slug if available, else root slug
const categorySlugForQuery = selectedSubcategorySlug || slug;

const { data: brands = [] } = useQuery({
  queryKey: ["brands", "category", categorySlugForQuery],
  queryFn: () => fetchBrands(undefined, categorySlugForQuery),
  enabled: !!categorySlugForQuery,
});
```

4. **Add subcategory selection handler**:
```typescript
const handleSubcategorySelect = (subcategorySlug: string | null) => {
  const newParams = new URLSearchParams();
  if (subcategorySlug) {
    newParams.set("subcategory", subcategorySlug);
  }
  router.push(`?${newParams.toString()}`);
};
```

5. **Add view condition** for subcategory selection:
```typescript
// VIEW 0: SUBCATEGORY SELECTION (if root category)
if (!category?.is_leaf && !selectedSubcategorySlug) {
  return <SubcategorySelectionView
    category={category}
    subcategories={subcategories}
    onSelect={handleSubcategorySelect}
  />;
}

// VIEW 1: BRAND & SERIES SELECTION
if (!selectedSeriesSlug) {
  return <BrandSeriesSelector ... />;
}

// VIEW 2: PRODUCT LISTING
return <ProductListingView ... />;
```

---

### 3.3 New API Client Functions

**File**: `frontend/public/src/lib/api/index.ts`

**Add**:
```typescript
export async function fetchCategoryChildren(parentSlug: string) {
  const res = await fetch(`${ENDPOINTS.CATEGORIES}/${parentSlug}/children/`);
  if (!res.ok) throw new Error('Failed to fetch subcategories');
  return res.json();
}
```

**Update fetchBrands** to support category param:
```typescript
export async function fetchBrands(
  search?: string,
  category?: string  // Add category param
) {
  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (category) params.set('category', category);  // Use for filtering

  const res = await fetch(`${ENDPOINTS.BRANDS}/?${params}`);
  if (!res.ok) throw new Error('Failed to fetch brands');
  return res.json();
}
```

**Update fetchSeries** to use category param:
```typescript
export async function fetchSeries(
  category?: string,
  brand?: string
) {
  const params = new URLSearchParams();
  if (category) params.set('category', category);
  if (brand) params.set('brand', brand);

  const res = await fetch(`${ENDPOINTS.SERIES}/?${params}`);
  if (!res.ok) throw new Error('Failed to fetch series');
  return res.json();
}
```

---

## PHASE 4: ADMIN UI UPDATES

### 4.1 Category Management UI

**Location**: Admin dashboard categories section

**Features to Add**:

1. **Tree View Display**
   - Show categories in tree structure
   - Visual indentation for subcategories
   - Expand/collapse root categories
   - Drag-and-drop reordering within same parent

2. **Category Create/Edit Form**
   - Add "Parent Category" dropdown
   - Show depth indicator
   - Validate depth limit (max 2 levels)
   - Show breadcrumb path preview

3. **Category Detail Tabs**:
   - **Subcategories Tab**: List children categories
   - **Series Tab**: Series in this category
   - **Products Tab**: All products (via series)
   - **Stats Tab**: Product counts, brand counts

---

### 4.2 Series Management Updates

**Add Validation**:
- When editing Series, validate that selected category is a leaf
- Show warning if category has subcategories
- Suggest moving series to subcategory

---

## PHASE 5: IMPORT SYSTEM COMPATIBILITY

### 5.1 Template Updates

**File**: `backend/apps/ops/import_api.py`

**Add Taxonomy Column** to template (line 378):

```python
columns = [
    # ... existing columns
    'taxonomy',  # NEW: Category hierarchy path
    'series_slug',
    'brand_slug',
    # ...
]
```

**Example Row**:
```
taxonomy: "Fırınlar > Pizza Fırını"
series_slug: "600-series"
brand_slug: "gastrotech"
```

---

### 5.2 Import Validation Logic

**File**: `backend/apps/ops/services/unified_import.py`

**Add Taxonomy Parsing**:

```python
def parse_taxonomy(taxonomy_str: str) -> tuple[str, str | None]:
    """
    Parse taxonomy path into (root_category_slug, subcategory_slug).

    Examples:
    - "Fırınlar" → ("firinlar", None)
    - "Fırınlar > Pizza Fırını" → ("firinlar", "pizza-firini")

    Returns:
        (root_slug, subcategory_slug)
    """
    if not taxonomy_str or not taxonomy_str.strip():
        return (None, None)

    parts = [p.strip() for p in taxonomy_str.split('>')]

    if len(parts) == 1:
        # Root category only
        return (slugify_tr(parts[0]), None)
    elif len(parts) == 2:
        # Root > Subcategory
        return (slugify_tr(parts[0]), slugify_tr(parts[1]))
    else:
        raise ValidationError(f"Invalid taxonomy path: {taxonomy_str}. Max depth is 2.")
```

**Add Category Resolution** in validation:

```python
def validate_row_taxonomy(row, mode):
    """Validate and resolve taxonomy path."""
    taxonomy_str = row.get('taxonomy', '').strip()

    if not taxonomy_str:
        return {'error': 'taxonomy is required'}

    try:
        root_slug, sub_slug = parse_taxonomy(taxonomy_str)
    except ValidationError as e:
        return {'error': str(e)}

    # Resolve root category
    root_category = Category.objects.filter(slug=root_slug, parent__isnull=True).first()

    if not root_category:
        if mode == 'smart':
            # Create candidate
            return {
                'candidate': {
                    'type': 'category',
                    'slug': root_slug,
                    'name': taxonomy_str.split('>')[0].strip(),
                    'parent': None
                }
            }
        else:
            return {'error': f'Root category "{root_slug}" not found'}

    # Resolve subcategory if specified
    if sub_slug:
        subcategory = Category.objects.filter(slug=sub_slug, parent=root_category).first()

        if not subcategory:
            if mode == 'smart':
                # Create subcategory candidate
                return {
                    'candidate': {
                        'type': 'category',
                        'slug': sub_slug,
                        'name': taxonomy_str.split('>')[-1].strip(),
                        'parent': root_category.id
                    }
                }
            else:
                return {'error': f'Subcategory "{sub_slug}" not found under "{root_slug}"'}

        # Use subcategory as target
        return {'category': subcategory}
    else:
        # Use root category as target
        return {'category': root_category}
```

---

### 5.3 Series Assignment

**Update Series Resolution**:

When creating/updating products, ensure Series.category matches the resolved taxonomy category:

```python
def resolve_series(series_slug, taxonomy_category):
    """
    Resolve series and validate it belongs to taxonomy category.
    """
    series = Series.objects.filter(slug=series_slug).first()

    if not series:
        if mode == 'smart':
            # Create series candidate under taxonomy category
            return {
                'candidate': {
                    'type': 'series',
                    'slug': series_slug,
                    'category': taxonomy_category.id
                }
            }
        else:
            return {'error': f'Series "{series_slug}" not found'}

    # Validate series belongs to taxonomy category
    if series.category != taxonomy_category:
        return {
            'error': f'Series "{series_slug}" belongs to category "{series.category.name}", '
                    f'but taxonomy specifies "{taxonomy_category.name}"'
        }

    return {'series': series}
```

---

## PHASE 6: TESTING REQUIREMENTS

### 6.1 Backend Tests

**File**: `backend/apps/catalog/tests/test_subcategory_api.py` (new)

**Test Cases**:

1. **Category Tree Tests**:
   - Test root categories have `is_leaf=False`
   - Test subcategories have `is_leaf=True`
   - Test `children` field returns correct subcategories
   - Test `products_count` includes products from subcategories

2. **Category Children Endpoint**:
   - Test returns immediate children only
   - Test counts are correct
   - Test ordering (by order, then name)
   - Test 404 for non-existent parent

3. **Brand Filtering by Category**:
   - Test `/api/v1/brands/?category=<subcategory>` returns correct brands
   - Test excludes brands without products in that subcategory
   - Test distinct results (no duplicates)

4. **Series Filtering**:
   - Test `/api/v1/series/?category=<slug>` filters correctly
   - Test `/api/v1/series/?category=<slug>&brand=<slug>` combines filters
   - Test empty results when no match

5. **Product Filtering by Subcategory**:
   - Test `/api/v1/products/?category=<subcategory>` returns correct products
   - Test combination: `?category=<sub>&brand=<brand>&series=<series>`

---

### 6.2 Frontend E2E Tests

**File**: `frontend/public/tests/e2e/subcategory-navigation.spec.ts` (new)

**Test Scenarios**:

1. **Root Category → Subcategory Flow**:
   - Navigate to `/kategori/firinlar`
   - Verify subcategory grid is shown
   - Click "Pizza Fırını" subcategory
   - Verify URL updates to `?subcategory=pizza-firini`
   - Verify brand selection view is shown

2. **Subcategory → Brand → Series → Products Flow**:
   - Start at `/kategori/firinlar?subcategory=pizza-firini`
   - Select brand
   - Verify series list shows only series for that brand+subcategory
   - Select series
   - Verify products list shows only products matching filters

3. **Deep Link Navigation**:
   - Navigate directly to `/kategori/firinlar?subcategory=pizza-firini&brand=gastrotech&series=600`
   - Verify products are shown immediately
   - Verify breadcrumb shows full path
   - Click breadcrumb to go back to brand selection

4. **Back Button Behavior**:
   - Navigate through flow: root → sub → brand → series → products
   - Click browser back button
   - Verify state reverts correctly at each step

---

### 6.3 Import System Tests

**File**: `backend/apps/ops/tests/test_import_taxonomy.py` (new)

**Test Cases**:

1. **Taxonomy Parsing**:
   - Test `"Fırınlar"` → `(firinlar, None)`
   - Test `"Fırınlar > Pizza Fırını"` → `(firinlar, pizza-firini)`
   - Test invalid depth (3+ levels) raises error

2. **Smart Mode Category Creation**:
   - Import with taxonomy `"Yeni Kategori > Alt Kategori"`
   - Verify root category "Yeni Kategori" created
   - Verify subcategory "Alt Kategori" created with correct parent
   - Verify series assigned to subcategory

3. **Strict Mode Validation**:
   - Import with non-existent taxonomy
   - Verify validation error
   - Verify no database changes

4. **Series-Category Consistency**:
   - Import product with taxonomy `"Fırınlar > Pizza Fırını"` and series `"600-series"`
   - If `600-series` belongs to different category, verify error
   - If `600-series` belongs to `"Pizza Fırını"`, verify success

---

## IMPLEMENTATION PHASES SUMMARY

### Phase 1: Data Model (1-2 days)
- ✅ Category already has parent field
- Add helper properties: `is_root`, `is_leaf`, `depth`, `breadcrumbs`, `full_path`
- Add validation: depth limit, circular reference prevention
- Add Series.category validation (soft, leaf-only check)
- **No migrations needed**

### Phase 2: Backend API (2-3 days)
- Add `CategoryChildrenView` endpoint
- Update `BrandListView` with category filter
- Update `SeriesListView` with category + brand filter
- Update `ProductFilter` with category support
- Update `CategoryTreeSerializer` with counts
- Add OpenAPI schema documentation
- **Deliverable**: API endpoints ready for frontend

### Phase 3: Public UI (3-4 days)
- Update `/kategori/[slug]` page with subcategory selection
- Add `SubcategorySelectionView` component
- Update `BrandSeriesSelector` to use subcategory context
- Update API client functions
- Update breadcrumb navigation
- Add deep link support
- **Deliverable**: Fully functional subcategory navigation

### Phase 4: Admin UI (2-3 days)
- Add category tree view in admin
- Update category create/edit forms with parent selection
- Add category detail tabs (subcategories, series, products)
- Update series forms with category validation
- Add bulk move operations
- **Deliverable**: Admin can manage subcategories

### Phase 5: Import System (2-3 days)
- Add `taxonomy` column to template
- Implement taxonomy parsing logic
- Add category creation in smart mode
- Update series resolution with category validation
- Update validation reports
- **Deliverable**: Import supports subcategory assignment

### Phase 6: Testing (2-3 days)
- Write backend unit tests
- Write integration tests
- Write frontend E2E tests
- Write import system tests
- Manual QA testing
- **Deliverable**: All tests passing

---

## MIGRATION STRATEGY

### Backward Compatibility

**Existing Data**:
- All current categories are **root categories** (parent=NULL)
- All current series point to root categories
- No breaking changes to existing data

**Migration Path**:
1. Deploy Phase 1 (model updates) - **no visible changes**
2. Deploy Phase 2 (API updates) - **backward compatible**
   - Existing `/kategori/<slug>` still works (treats slug as leaf)
   - New `?subcategory=<slug>` param optional
3. Create subcategories via admin UI
4. Move series to subcategories manually or via script
5. Deploy Phase 3 (UI updates) - **progressive enhancement**
   - If category has children, show subcategory selection
   - If category has no children, show brand selection (existing flow)

**Rollback Plan**:
- All changes are additive
- No data migrations required
- Can rollback code without data loss
- Subcategories can be deleted without breaking products (series still linked to parent)

---

## RISKS & MITIGATIONS

### Risk 1: Deep Linking Complexity
**Risk**: Users bookmark URLs with subcategory params, then subcategory is deleted
**Mitigation**:
- Validate subcategory slug on page load
- Fallback to parent category if subcategory not found
- Show user-friendly error message

### Risk 2: Performance (N+1 Queries)
**Risk**: Category tree fetching causes N+1 queries
**Mitigation**:
- Use `prefetch_related('children')` in tree views
- Cache category tree for 5 minutes
- Use `select_related('parent')` for breadcrumbs

### Risk 3: Import Conflicts
**Risk**: Existing products use root categories, new imports use subcategories
**Mitigation**:
- Allow series to belong to both root and leaf categories (during transition)
- Validation warns but doesn't fail if series in root category
- Provide migration script to move series to subcategories

### Risk 4: SEO Impact
**Risk**: URL structure change affects SEO
**Mitigation**:
- Keep existing `/kategori/<slug>` URLs working
- Use 301 redirects if needed
- Update sitemap.xml with new subcategory URLs
- Add canonical tags

---

## SUCCESS CRITERIA

### Must Have (Blocking)
- ✅ Category tree supports 2-level hierarchy (root → subcategory)
- ✅ User can navigate: Root → Subcategory → Brand → Series → Products
- ✅ Deep links work: `/kategori/<root>?subcategory=<sub>&brand=<brand>&series=<series>`
- ✅ API endpoints return correct filtered results
- ✅ Import system supports taxonomy column
- ✅ Admin can create/edit subcategories
- ✅ All tests pass (backend + frontend + E2E)

### Should Have (Important)
- ✅ Breadcrumb navigation shows full path
- ✅ Category tree cached for performance
- ✅ Smart mode creates missing subcategories
- ✅ Series validation prevents wrong category assignment

### Nice to Have (Optional)
- Drag-and-drop category reordering in admin
- Bulk move series to subcategories
- Category merge/split tools
- Analytics on subcategory usage

---

## APPENDIX A: API REQUEST/RESPONSE EXAMPLES

### Example 1: Category Tree
```http
GET /api/v1/categories/tree/

Response 200:
[
  {
    "id": "uuid-1",
    "name": "Fırınlar",
    "slug": "firinlar",
    "is_leaf": false,
    "products_count": 45,
    "subcategory_count": 2,
    "children": [
      {
        "id": "uuid-2",
        "name": "Pizza Fırını",
        "slug": "pizza-firini",
        "is_leaf": true,
        "products_count": 20,
        "subcategory_count": 0,
        "children": []
      },
      {
        "id": "uuid-3",
        "name": "Elektrikli Fırın",
        "slug": "elektrikli-firin",
        "is_leaf": true,
        "products_count": 25,
        "subcategory_count": 0,
        "children": []
      }
    ]
  }
]
```

### Example 2: Category Children
```http
GET /api/v1/categories/firinlar/children/

Response 200:
[
  {
    "id": "uuid-2",
    "name": "Pizza Fırını",
    "slug": "pizza-firini",
    "products_count": 20
  },
  {
    "id": "uuid-3",
    "name": "Elektrikli Fırın",
    "slug": "elektrikli-firin",
    "products_count": 25
  }
]
```

### Example 3: Brands by Subcategory
```http
GET /api/v1/brands/?category=pizza-firini

Response 200:
[
  {
    "id": "uuid-10",
    "name": "Gastrotech",
    "slug": "gastrotech"
  },
  {
    "id": "uuid-11",
    "name": "Partner Brand A",
    "slug": "partner-brand-a"
  }
]
```

### Example 4: Series by Subcategory + Brand
```http
GET /api/v1/series/?category=pizza-firini&brand=gastrotech

Response 200:
[
  {
    "id": "uuid-20",
    "name": "600 Series",
    "slug": "600-series",
    "products_count": 8
  },
  {
    "id": "uuid-21",
    "name": "700 Series",
    "slug": "700-series",
    "products_count": 12
  }
]
```

---

## APPENDIX B: DATABASE QUERIES

### Query 1: Get all products in subcategory
```sql
SELECT p.*
FROM catalog_product p
JOIN catalog_series s ON p.series_id = s.id
JOIN catalog_category c ON s.category_id = c.id
WHERE c.slug = 'pizza-firini'
  AND p.status = 'active';
```

### Query 2: Get brands in subcategory
```sql
SELECT DISTINCT b.*
FROM catalog_brand b
JOIN catalog_product p ON p.brand_id = b.id
JOIN catalog_series s ON p.series_id = s.id
JOIN catalog_category c ON s.category_id = c.id
WHERE c.slug = 'pizza-firini'
  AND p.status = 'active'
  AND b.is_active = true
ORDER BY b.order, b.name;
```

### Query 3: Get category tree with counts
```sql
-- Root categories with subcategory counts
SELECT
  c.id,
  c.name,
  c.slug,
  COUNT(DISTINCT children.id) as subcategory_count,
  COUNT(DISTINCT p.id) as products_count
FROM catalog_category c
LEFT JOIN catalog_category children ON children.parent_id = c.id
LEFT JOIN catalog_series s ON s.category_id = c.id
LEFT JOIN catalog_product p ON p.series_id = s.id AND p.status = 'active'
WHERE c.parent_id IS NULL
GROUP BY c.id
ORDER BY c.order, c.name;
```

---

## CONCLUSION

This implementation plan adds a subcategory layer to the existing category-first navigation without breaking changes. The Category model already supports hierarchical structure via the `parent` field, so no database migrations are required.

The implementation is phased to allow incremental deployment and testing, with backward compatibility maintained at each step. Existing data remains valid, and the system gracefully handles both root-only categories and subcategory-based navigation.

**Total Estimated Time**: 12-18 days (2-3 weeks)
**Risk Level**: Low (additive changes, no breaking changes)
**Migration Complexity**: Low (no data migrations, optional adoption)

---

**Next Steps**:
1. Review and approve this plan
2. Create implementation tasks in project tracker
3. Begin Phase 1 (Data Model) implementation
4. Set up test environment for validation
5. Proceed phase-by-phase with testing after each phase

**Document Version**: 1.0
**Last Updated**: 2026-01-17
**Author**: Staff Engineer + Data Model Architect
