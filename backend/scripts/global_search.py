import os
import sys
import django
from pathlib import Path
from django.db.models import Q

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import Category, Series, Product

def run():
    print("--- Global Search for keywords: 'bulasik', 'camasir' ---")
    
    keywords = ['bulasik', 'camasir', 'yikama']
    
    for kw in keywords:
        print(f"\nResults for '{kw}':")
        
        # Categories
        cats = Category.objects.filter(Q(name__icontains=kw) | Q(slug__icontains=kw))
        for c in cats:
            print(f"  [Category] {c.name} ({c.slug}) ID:{c.id}")
            
        # Series
        series = Series.objects.filter(Q(name__icontains=kw) | Q(slug__icontains=kw))
        for s in series:
            print(f"  [Series] {s.name} ({s.slug}) ParentCat:{s.category.slug}")
            
        # Products
        prods = Product.objects.filter(Q(title_tr__icontains=kw) | Q(slug__icontains=kw))
        for p in prods:
            print(f"  [Product] {p.title_tr} ({p.slug}) Series:{p.series.slug if p.series else 'None'}")

if __name__ == "__main__":
    run()
