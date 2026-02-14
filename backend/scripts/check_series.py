import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import Category, Series

def run():
    print("--- Series Analysis ---")
    
    target_slugs = ['bulasik-yikama', 'camasirhane-ekipmanlari', 'firinlar', 'hazirlik-ekipmanlari', 'pisirme-uniteleri']
    
    for slug in target_slugs:
        try:
            cat = Category.objects.get(slug=slug)
            products_count = cat.products.count()
            print(f"\nCategory: {cat.name} ({cat.slug}) | Total Products: {products_count}")
            series = Series.objects.filter(category=cat).order_by('name')
            if series.exists():
                for s in series:
                    print(f"  - Series: '{s.name}' (slug: {s.slug}) [Products: {s.products.count()}]")
            else:
                print("  (No Series found)")
        except Category.DoesNotExist:
            print(f"\nCategory '{slug}' not found!")

if __name__ == "__main__":
    run()
