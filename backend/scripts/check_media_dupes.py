import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import CategoryCatalog

def run():
    print("--- Catalog Media Analysis ---")
    catalogs = CategoryCatalog.objects.select_related('media', 'category').all().order_by('category__slug')
    
    seen_sizes = {}
    
    for c in catalogs:
        size = c.media.size_bytes if c.media else 0
        filename = c.media.filename if c.media else "No Media"
        print(f"Category: {c.category.name:<25} | Title: {c.title_tr:<20} | File: {filename:<30} | Size: {size}")
        
        if size > 0:
            if size in seen_sizes:
                prev_cat, prev_title = seen_sizes[size]
                print(f"  *** POSSIBLE DUPLICATE FILE (Same Size) with: {prev_cat.name} - {prev_title} ***")
            seen_sizes[size] = (c.category, c.title_tr)

if __name__ == "__main__":
    run()
