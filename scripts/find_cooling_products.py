import pandas as pd

# Load all CSV data
prod_df = pd.read_csv('sss/catalog_product_202601181553.csv')
series_df = pd.read_csv('sss/catalog_series_202601181553.csv')
cat_df = pd.read_csv('sss/catalog_category_202601181553.csv')

print("=" * 70)
print("ANALYZING COOLING PRODUCTS IN CSV")
print("=" * 70)

# List all categories
print("\n=== ALL CATEGORIES ===")
for _, cat in cat_df.iterrows():
    print(f"  {cat['id'][:8]}... | {cat['name']} | slug: {cat['slug']}")

# Find cooling-related terms in products
cooling_terms = ['sogutma', 'soğutma', 'cooling', 'buzdolabi', 'buzdolabı', 
                 'dondurucu', 'freezer', 'refriger', 'cold', 'ice', 
                 'blast chiller', 'şok soğutucu', 'sok sogutucu']

print("\n=== PRODUCTS WITH COOLING TERMS IN NAME ===")
for term in cooling_terms:
    matches = prod_df[prod_df['name'].str.lower().str.contains(term, na=False)]
    if len(matches) > 0:
        print(f"\nTerm '{term}': {len(matches)} products")
        for _, p in matches.iterrows():
            series_name = "N/A"
            if pd.notna(p['series_id']):
                series_match = series_df[series_df['id'] == p['series_id']]
                if len(series_match) > 0:
                    series_name = series_match.iloc[0]['name']
            print(f"  - {p['name'][:50]} | Series: {series_name}")

# Find series with cooling terms
print("\n=== SERIES WITH COOLING TERMS ===")
for term in cooling_terms:
    matches = series_df[series_df['name'].str.lower().str.contains(term, na=False)]
    if len(matches) > 0:
        print(f"\nTerm '{term}': {len(matches)} series")
        for _, s in matches.iterrows():
            cat_name = "N/A"
            if pd.notna(s['category_id']):
                cat_match = cat_df[cat_df['id'] == s['category_id']]
                if len(cat_match) > 0:
                    cat_name = cat_match.iloc[0]['name']
            # Count products in this series
            prod_count = len(prod_df[prod_df['series_id'] == s['id']])
            print(f"  - {s['name']} | Category: {cat_name} | Products: {prod_count}")

# Find Soğutma category ID
cooling_cat = cat_df[cat_df['name'].str.contains('Soğutma|sogutma', case=False, na=False)]
print(f"\n=== SOĞUTMA CATEGORY ===")
print(cooling_cat[['id', 'name', 'slug']])

# Find what's currently in Soğutma category
if len(cooling_cat) > 0:
    cooling_cat_id = cooling_cat.iloc[0]['id']
    series_in_cooling = series_df[series_df['category_id'] == cooling_cat_id]
    print(f"\nSeries currently in Soğutma: {len(series_in_cooling)}")
    for _, s in series_in_cooling.iterrows():
        print(f"  - {s['name']}")

# Check Konveksiyonel Fırınlar
konv = cat_df[cat_df['name'].str.contains('Konveksiyonel|KWIK', case=False, na=False)]
print(f"\n=== KONVEKSIYONEL FIRINLAR CATEGORY ===")
print(konv[['id', 'name', 'slug']])

if len(konv) > 0:
    konv_cat_id = konv.iloc[0]['id']
    series_in_konv = series_df[series_df['category_id'] == konv_cat_id]
    print(f"\nSeries in Konveksiyonel ({len(series_in_konv)} total):")
    for _, s in series_in_konv.iterrows():
        # Check if this is actually a cooling series
        is_cooling = any(term in s['name'].lower() for term in ['sogutma', 'soğutma', 'cooling', 'blast', 'chiller', 'şok', 'sok'])
        marker = " *** COOLING ***" if is_cooling else ""
        prod_count = len(prod_df[prod_df['series_id'] == s['id']])
        print(f"  - {s['name']} ({prod_count} products){marker}")
