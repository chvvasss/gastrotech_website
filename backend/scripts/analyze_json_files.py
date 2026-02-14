import json
import os
from collections import Counter

# Analyze all JSON files in ceysonlar directory
json_dir = r"C:\gastrotech.com.tr.0101\gastrotech.com_cursor\ceysonlar"

# Dynamic file list sorted by mtime descending
files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
files.sort(key=lambda x: os.path.getmtime(os.path.join(json_dir, x)), reverse=True)

print("=" * 80)
print("JSON FILES ANALYSIS")
print(f"Directory: {json_dir}")
print("=" * 80)

for filename in files:
    filepath = os.path.join(json_dir, filename)
    
    if not os.path.exists(filepath):
        print(f"\n[!] {filename}: FILE NOT FOUND")
        continue
    
    file_size = os.path.getsize(filepath)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Count products
        product_count = len(data) if isinstance(data, list) else 0
        
        # Analyze categories
        categories = [p.get('category', 'UNKNOWN') for p in data if isinstance(p, dict)]
        category_counts = Counter(categories)
        
        # Count fields per product (to measure completeness)
        if data and isinstance(data[0], dict):
            avg_fields = sum(len(p.keys()) for p in data) / len(data)
            has_images = sum(1 for p in data if p.get('images') and len(p.get('images', [])) > 0)
            has_variants = sum(1 for p in data if p.get('variants') and len(p.get('variants', [])) > 0)
        else:
            avg_fields = 0
            has_images = 0
            has_variants = 0
        
        print(f"\n[FILE] {filename}")
        print(f"   Size: {file_size:,} bytes")
        print(f"   Products: {product_count}")
        print(f"   Avg fields: {avg_fields:.1f}")
        print(f"   With images: {has_images} ({has_images/product_count*100:.1f}%)" if product_count else "   With images: 0")
        print(f"   With variants: {has_variants} ({has_variants/product_count*100:.1f}%)" if product_count else "   With variants: 0")
        print(f"   Categories:")
        for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            print(f"      - {cat}: {count} products")
        
        # Check for firinlar and hazirlik-ekipmanlari specifically
        firinlar_count = sum(1 for p in data if p.get('category') == 'firinlar')
        hazirlik_count = sum(1 for p in data if 'hazir' in str(p.get('category', '')).lower())
        
        if firinlar_count > 0 or hazirlik_count > 0:
            print(f"   [TARGET CATEGORIES]:")
            if firinlar_count > 0:
                print(f"      - firinlar: {firinlar_count} products")
            if hazirlik_count > 0:
                print(f"      - hazirlik-ekipmanlari: {hazirlik_count} products")
        
        # Search for keywords in product titles
        keywords = ["sebze", "vakum", "hamur", "kurut", "soyma", "kuteri", "vegetable", "meat", "vacuum", "dough", "slicer", "peeler"]
        print(f"   [KEYWORD SEARCH]:")
        match_count = 0
        for p in data:
            name = p.get('name', '') or p.get('title_tr', '') or p.get('title', '')
            cat = p.get('category', 'UNKNOWN')
            for kw in keywords:
                if kw in str(name).lower():
                    print(f"      - Found '{kw}' in: {name} (Category: {cat})")
                    match_count += 1
        if match_count == 0:
            print("      (No substring matches found)")
        
    except Exception as e:
        print(f"\n[ERROR] {filename}: {str(e)}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
