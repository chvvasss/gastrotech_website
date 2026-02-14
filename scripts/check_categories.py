"""
Check existing categories in the database.
"""

import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.catalog.models import Category

print("\n" + "="*60)
print("ROOT CATEGORIES")
print("="*60)
root_cats = Category.objects.filter(parent__isnull=True).order_by('order', 'name')
for cat in root_cats:
    print(f"  {cat.slug} - {cat.name}")

print("\n" + "="*60)
print("ALL CATEGORIES (parent -> child)")
print("="*60)
all_cats = Category.objects.all().select_related('parent').order_by('parent__slug', 'slug')
for cat in all_cats:
    parent_slug = cat.parent.slug if cat.parent else "ROOT"
    print(f"  {parent_slug:40} -> {cat.slug}")
