
import os
import django
from pathlib import Path

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Product, Variant

# Unmatched examples to test
test_files = [
    "391109_Gazli_Benmari.jpg",
    "Chef_in_casa_Eriste_-_Makarna_Makinesi_6KgSaat.jpg",
    "MAESTRO061G-TOUCH_Gazli_Kombi_Firin_6_GN_11.jpg",
    "AIRPOT_FURENTO_Filtre_Kahve_Dispenseri_22_Lt.jpg",
    "NO10_Narenciye_Sikacagi_Kollu_Model.jpg",
    "CBU143064S4_Demonte_Istif_Rafi_360x765x1630.jpg"
]

def analyze_file(filename):
    print(f"\nAnalyzing: {filename}")
    stem = Path(filename).stem
    parts = stem.split('_')
    
    # Strategy 1: Search by Name parts
    # Skip the "Code" part (first part) usually, but sometimes the code is part of the name
    
    # Construct potential name queries
    # "Gazli Benmari"
    # "Chef in casa Eriste"
    
    potential_names = []
    
    # Try using the whole stem replacing underscores
    clean_name = stem.replace('_', ' ')
    potential_names.append(clean_name)
    
    # Try using parts [1:]
    if len(parts) > 1:
        name_part = " ".join(parts[1:])
        potential_names.append(name_part)
    
    for query in potential_names:
        print(f"  Query: '{query}'")
        # Exact match?
        # Fuzzy match?
        
        # Try simple icontains
        products = Product.objects.filter(title_tr__icontains=query)
        if products.exists():
            print(f"    FOUND {products.count()} products via title_tr (exact string match)")
            for p in products[:3]:
                print(f"      - {p.title_tr} (Slug: {p.slug})")
            return
            
        # Try splitting query
        words = query.split()
        if len(words) > 1:
            # Try matching ALL words
            qs = Product.objects.all()
            for w in words:
                if len(w) > 2: # Skip small words
                    qs = qs.filter(title_tr__icontains=w)
            
            if qs.exists():
                 print(f"    FOUND {qs.count()} products via word intersection")
                 for p in qs[:3]:
                    print(f"      - {p.title_tr} (Slug: {p.slug})")
                 return

    print("  NO MATCH FOUND")

for f in test_files:
    analyze_file(f)
