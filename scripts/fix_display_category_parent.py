"""
Fix parent category for setustu-teshir-uniteleri.

Move it from tamamlayici-ekipmanlar -> teshir-uniteleri 
to sogutma-uniteleri (cooling equipment).
"""

import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.catalog.models import Category


def fix_display_category_parent():
    """Move display units category to cooling equipment."""
    
    print("\n" + "="*60)
    print("FIXING DISPLAY UNITS CATEGORY PARENT")
    print("="*60 + "\n")
    
    # Get the category that needs to be moved
    try:
        display_cat = Category.objects.get(slug='setustu-teshir-uniteleri')
        print(f"[OK] Found category: {display_cat.name}")
        print(f"    Current parent: {display_cat.parent.name} ({display_cat.parent.slug})")
    except Category.DoesNotExist:
        print("[ERROR] Category 'setustu-teshir-uniteleri' not found!")
        return
    
    # Get the new parent (cooling equipment)
    try:
        sogutma = Category.objects.get(slug='sogutma-uniteleri')
        print(f"[OK] Found new parent: {sogutma.name} ({sogutma.slug})")
    except Category.DoesNotExist:
        print("[ERROR] Parent category 'sogutma-uniteleri' not found!")
        return
    
    # Update the parent
    old_parent = display_cat.parent
    display_cat.parent = sogutma
    display_cat.save()
    
    print(f"\n[+] Updated category parent:")
    print(f"    Category: {display_cat.name}")
    print(f"    Old parent: {old_parent.name}")
    print(f"    New parent: {sogutma.name}")
    
    print("\n[OK] Display units category is now under cooling equipment!\n")


if __name__ == '__main__':
    fix_display_category_parent()
