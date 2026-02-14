import os
import sys
import django
from pathlib import Path
from django.db.models import Count

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import Category, CategoryCatalog

def run():
    print("--- Detailed Duplicate Check ---")
    
    # Check for categories with similar names
    print("\n1. Categories with potentially similar names:")
    cats = Category.objects.all().values('id', 'name', 'slug')
    seen_names = {}
    for c in cats:
        # Normalize name for comparison (simple lowercasing + removing common suffixes)
        norm_name = c['name'].lower().replace("ekipmanları", "").replace("makineleri", "").strip()
        if norm_name in seen_names:
            print(f"  POTENTIAL DUPLICATE NAME CLUSTER: '{norm_name}'")
            print(f"    - {seen_names[norm_name]['name']} ({seen_names[norm_name]['slug']})")
            print(f"    - {c['name']} ({c['slug']})")
        else:
            seen_names[norm_name] = c

    # Check for duplicate Catalogs (content)
    print("\n2. Duplicate Catalogs (Title matches):")
    dupe_titles = CategoryCatalog.objects.values('title_tr').annotate(count=Count('id')).filter(count__gt=1)
    if dupe_titles:
        for d in dupe_titles:
             print(f"  Title: '{d['title_tr']}' appears {d['count']} times")
             catalogs = CategoryCatalog.objects.filter(title_tr=d['title_tr'])
             for cat in catalogs:
                 print(f"    - ID: {cat.id} | Category: {cat.category.slug} | Published: {cat.published}")
    else:
        print("  None found.")

    # Check for duplicate Catalogs (Media matches)
    print("\n3. Duplicate Catalogs (Media ID matches):")
    dupe_media = CategoryCatalog.objects.values('media_id').annotate(count=Count('id')).filter(count__gt=1)
    if dupe_media:
        for d in dupe_media:
             print(f"  Media ID: '{d['media_id']}' appears {d['count']} times")
    else:
        print("  None found.")
        
    print("\n--- Catalogs per Category ---")
    for cat in Category.objects.all().order_by('slug'):
        catalogs = CategoryCatalog.objects.filter(category=cat).order_by('title_tr')
        if catalogs.exists():
            print(f"\nCategory: {cat.name} ({cat.slug})")
            for c in catalogs:
                print(f"  - [{c.id}] Title: '{c.title_tr}' | Media: {c.media_id} | Published: {c.published}")

if __name__ == "__main__":
    run()
