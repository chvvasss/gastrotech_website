"""
Create missing camasirhane-ekipmanlari category.

5 laundry equipment products are referencing this missing category.
"""

import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.catalog.models import Category


def create_laundry_category():
    """Create the missing laundry equipment category."""
    
    print("\n" + "="*60)
    print("CREATING MISSING LAUNDRY CATEGORY")
    print("="*60 + "\n")
    
    # Get parent category
    try:
        camasirhane = Category.objects.get(slug='camasirhane')
        print(f"[OK] Found parent: {camasirhane.name} ({camasirhane.slug})")
    except Category.DoesNotExist:
        print("[ERROR] Parent category 'camasirhane' not found!")
        return
    
    # Create the missing category
    category_data = {
        'slug': 'camasirhane-ekipmanlari',
        'name': 'Çamaşırhane Ekipmanları',
        'description_short': 'Endüstriyel çamaşırhane ekipmanları',
        'parent': camasirhane,
        'order': 10,
    }
    
    cat, created = Category.objects.get_or_create(
        slug=category_data['slug'],
        defaults=category_data
    )
    
    if created:
        print(f"[+] Created: {cat.name}")
        print(f"    Slug: {cat.slug}")
        print(f"    Parent: {cat.parent.name}")
    else:
        print(f"[=] Already exists: {cat.name}")
    
    print("\n[OK] Laundry equipment category is ready!\n")


if __name__ == '__main__':
    create_laundry_category()
