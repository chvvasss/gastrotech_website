import pandas as pd
import json

# Load data
prod_df = pd.read_csv('sss/catalog_product_202601181553.csv')
series_df = pd.read_csv('sss/catalog_series_202601181553.csv')
cat_df = pd.read_csv('sss/catalog_category_202601181553.csv')

print("=" * 60)
print("PRODUCT-CATEGORY RELATIONSHIP ANALYSIS")
print("=" * 60)

# Check series→category links
series_with_cat = series_df[series_df['category_id'].notna()]
print(f"\nTotal series: {len(series_df)}")
print(f"Series WITH category_id: {len(series_with_cat)}")
print(f"Series WITHOUT category_id: {series_df['category_id'].isna().sum()}")

# Check products→series links
prod_with_series = prod_df[prod_df['series_id'].notna()]
print(f"\nTotal products: {len(prod_df)}")
print(f"Products WITH series_id: {len(prod_with_series)}")
print(f"Products WITHOUT series_id: {prod_df['series_id'].isna().sum()}")

# Products that can be linked via series→category
products_linkable = prod_df.merge(
    series_df[['id', 'category_id']], 
    left_on='series_id', 
    right_on='id', 
    how='left',
    suffixes=('_prod', '_series')
)

linkable_count = products_linkable['category_id_series'].notna().sum()
print(f"\nProducts that CAN be linked via series: {linkable_count}")
print(f"Products that CANNOT be linked: {len(prod_df) - linkable_count}")

# Group by category
category_dist = products_linkable[products_linkable['category_id_series'].notna()].groupby('category_id_series').size()

print("\nProduct distribution by category (via series):")
for cat_id, count in category_dist.items():
    cat_name = cat_df[cat_df['id'] == cat_id]['name'].values
    cat_name_str = cat_name[0] if len(cat_name) > 0 else "Unknown"
    print(f"  {cat_name_str}: {count} products")

# Generate SQL to fix
print("\n" + "=" * 60)
print("GENERATING FIX SQL...")
print("=" * 60)

updates = []
for _, row in products_linkable.iterrows():
    if pd.notna(row['category_id_series']):
        updates.append({
            'product_id': row['id_prod'],
            'category_id': row['category_id_series']
        })

print(f"\nTotal updates to generate: {len(updates)}")

# Write SQL file
with open('scripts/sql/populate_product_categories.sql', 'w', encoding='utf-8') as f:
    f.write("-- Populate product.category_id from series.category_id\n")
    f.write("-- Generated from CSV analysis\n\n")
    f.write("-- This fixes the issue where products have no direct category link\n\n")
    
    for update in updates[:10]:  # Show first 10 as example
        f.write(f"UPDATE catalog_product SET category_id='{update['category_id']}' WHERE id='{update['product_id']}';\n")
    
    if len(updates) > 10:
        f.write(f"\n-- ... and {len(updates) - 10} more updates\n")
        f.write("\n-- Or use this batch approach:\n")
        f.write("UPDATE catalog_product p\n")
        f.write("SET category_id = s.category_id\n")
        f.write("FROM catalog_series s\n")
        f.write("WHERE p.series_id = s.id\n")
        f.write("  AND p.category_id IS NULL\n")
        f.write("  AND s.category_id IS NOT NULL;\n")

print("\nSQL written to: scripts/sql/populate_product_categories.sql")
print("\nThis SQL will populate product.category_id from their series.")
