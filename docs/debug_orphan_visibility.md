# Debug: Orphan Series Visibility

## What I Changed
Added console logging to `/urunler/[categorySlug]/page.tsx` to debug the data flow.

## How to Verify

### Step 1: Open Browser Console
1. Navigate to [http://localhost:3000/kategori/firinlar](http://localhost:3000/kategori/firinlar) (or the ngrok URL)
2. Open browser developer tools (F12)
3. Go to the Console tab

### Step 2: Check the Debug Output
Look for a log entry like:
```
[CategoryPage Debug] {
  categorySlug: "firinlar",
  allSeries: 26,
  filteredSeries: 5,
  hasSubcategories: true,
  hasLogoGroups: false,
  hasDirectSeries: true,
  seriesData: [{name: "...", slug: "...", products_count: ...}, ...]
}
```

### Step 3: Interpret the Results

**IF `hasDirectSeries: true` AND you still don't see the series on the page:**
- The data is being fetched correctly
- The UI rendering logic has a bug
- Check the DOM to see if the "Fırınlar Modelleri" section is being rendered but hidden

**IF `hasDirectSeries: false` but `allSeries > 0`:**
- Series are being fetched but filtered out
- Possible causes:
  - `products_count < 2` (not enough products)
  - `is_visible === false` (explicitly hidden)

**IF `allSeries === 0`:**
- Backend is not returning any series
- Check the API response directly in Network tab
- Verify the API endpoint `/api/v1/series/?category=firinlar` returns data

## Expected Output
Based on the dry-run of `fix_orphan_subcategories`, we should see:
- `allSeries: 26` (26 orphan series in Fırınlar)
- Some of these should have `products_count >= 2`
- Example: `prime-serisi` (3 active products)

## Next Steps
Once you've checked the console, let me know what you see and I can fix the specific issue.
