import pandas as pd

# Load data
prod_df = pd.read_csv('sss/catalog_product_202601181553.csv')
series_df = pd.read_csv('sss/catalog_series_202601181553.csv')
cat_df = pd.read_csv('sss/catalog_category_202601181553.csv')

# Cooling category ID
cooling_cat_id = 'e6d3b22f-c5cc-4847-92f1-852fbfd2374c'

print("=" * 60)
print("SOĞUTMA CATEGORY ANALYSIS")
print("=" * 60)

# Products stats
print(f"\nTotal products: {len(prod_df)}")
print(f"Products WITH category_id: {prod_df['category_id'].notna().sum()}")
print(f"Products WITHOUT category_id: {prod_df['category_id'].isna().sum()}")

# Cooling products
cooling_prods = prod_df[prod_df['category_id'] == cooling_cat_id]
print(f"\nProducts in Soğutma category: {len(cooling_prods)}")
if len(cooling_prods) > 0:
    print("\nCooling products:")
    print(cooling_prods[['name', 'brand_id', 'series_id']].head(20))

# Cooling series
cooling_series = series_df[series_df['category_id'] == cooling_cat_id]
print(f"\nSeries in Soğutma category: {len(cooling_series)}")
if len(cooling_series) > 0:
    print("\nCooling series:")
    print(cooling_series[['id', 'name']].head(20))

# Check if products have series that link to cooling
if len(cooling_series) > 0:
    cooling_series_ids = set(cooling_series['id'])
    products_via_series = prod_df[prod_df['series_id'].isin(cooling_series_ids)]
    print(f"\nProducts linked via cooling series: {len(products_via_series)}")
    if len(products_via_series) > 0:
        print("\nSample products (via series):")
        print(products_via_series[['name', 'series_id', 'category_id']].head(20))
