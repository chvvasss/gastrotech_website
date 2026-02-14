
import os
import django
import sys
import json
import re

# Setup Django environment
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.catalog.models import Product, Series

def normalize_name(name, model_code):
    # 1. Remove Model Code prefix
    # "EDT7050 Elektrikli Devrilir Tava 50 lt." -> "Elektrikli Devrilir Tava 50 lt."
    cleaned = name
    if model_code and name.startswith(model_code):
        cleaned = name[len(model_code):].strip()
    
    # 2. Remove Capacity/Size suffixes commonly used in variants
    # "50 lt.", "10+10 Lt", "80x80"
    cleaned = re.sub(r'\s+\d+(\+\d+)?\s*(lt|Lt|LT)\.?$', '', cleaned)
    
    # 3. Remove "X Brülörlü" etc.
    cleaned = re.sub(r'\s+\d+\s+(Brülörlü|brülörlü|Gözlü|gözlü|Pleytli|pleytli|Bölmeli|bölmeli).*', '', cleaned)
    
    # 4. Remove dimensions if at end "400x900"
    cleaned = re.sub(r'\s+\d+x\d+(x\d+)?$', '', cleaned)
    
    # 5. Remove "Modeli" etc.
    cleaned = cleaned.replace(' Modeli', '')

    return cleaned.strip()

def analyze():
    series_slug = '700-serisi'
    products = Product.objects.filter(series__slug=series_slug).prefetch_related('variants')
    
    groups = {}
    
    for p in products:
        # Assuming 1 variant per product in current broken state
        variant = p.variants.first()
        model_code = variant.model_code if variant else ""
        
        base_name = normalize_name(p.name, model_code)
        
        if base_name not in groups:
            groups[base_name] = []
            
        groups[base_name].append({
            "id": str(p.id),
            "slug": p.slug,
            "name": p.name,
            "model_code": model_code,
            "image_count": p.product_media.count()
        })
        
    # Convert to list
    plan = []
    for base_name, items in groups.items():
        # Sort items by model code
        items.sort(key=lambda x: x['model_code'])
        
        plan.append({
            "proposed_name": f"700 Serisi {base_name}",
            "base_name_raw": base_name,
            "product_count": len(items),
            "items": items
        })
        
    print(json.dumps(plan, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    analyze()
