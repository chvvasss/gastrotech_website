
import os
import sys
import django
from django.db.models import Count

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import Category, Series, Product

def check_duplicates():
    print("--- CHECKING FOR SUSPICIOUS CATEGORIES ---")
    
    categories = Category.objects.annotate(p_count=Count('series__products')).all()
    
    print(f"Total Categories: {categories.count()}")
    
    # Simple check: listing all to eyeball first (since count is low ~14 from previous logs)
    cat_list = []
    for c in categories:
        print(f"[{c.slug}] Name: '{c.name}' (Products: {c.p_count})")
        cat_list.append(c)
        
    # Check for the specific example user gave
    typos = ["soputma", "bulaskhane", "sogutma"]
    
    print("\n--- Typos / Similar check ---")
    for t in typos:
        matches = [c for c in cat_list if t in c.slug or t in c.name.lower()]
        if matches:
            print(f"Matches for '{t}':")
            for m in matches:
                print(f"  - {m.slug} ({m.name})")

    # Check for Series with 1 product (Recap)
    print("\n--- Single Product Series Recap ---")
    single_series = Series.objects.annotate(pc=Count('products')).filter(pc=1)
    print(f"Count: {single_series.count()}")
    for s in single_series[:5]:
         print(f"  - {s.slug} (Prod: {s.products.first().slug})")

if __name__ == "__main__":
    check_duplicates()
