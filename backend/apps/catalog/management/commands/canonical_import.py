"""
Django Management Command: Canonical Brand/Category Import Helpers
Prevents duplicates during import with deterministic slug generation
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify as django_slugify
import unicodedata
from typing import Optional, Tuple
from apps.catalog.models import Brand, Category


def canonical_form(text: str) -> str:
    """
    Unicode normalize + casefold + TR transliteration + trim + collapse whitespace
    """
    if not text:
        return ''
    
    # NFD normalize
    text = unicodedata.normalize('NFD', text)
    
    # Turkish transliteration
    tr_map = str.maketrans({
        'ç': 'c', 'Ç': 'c',
        'ğ': 'g', 'Ğ': 'g',
        'ı': 'i', 'İ': 'i', 'I': 'i',
        'ö': 'o', 'Ö': 'o',
        'ş': 's', 'Ş': 's',
        'ü': 'u', 'Ü': 'u',
    })
    text = text.translate(tr_map)
    
    # Remove diacritics
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    
    # Casefold + trim + collapse whitespace
    return ' '.join(text.casefold().split())


def get_or_create_brand_canonical(name: str, **defaults) -> Tuple[Brand, bool]:
    """
    Get or create brand using canonical name matching
    Returns: (brand, created)
    """
    canonical = canonical_form(name)
    
    # Try exact canonical match first
    from django.db.models import F, Value
    from django.db.models.functions import Lower, Replace, Trim
    
    # Search existing brands with canonical matching
    existing_brands = Brand.objects.all()
    for brand in existing_brands:
        if canonical_form(brand.name) == canonical:
            return brand, False
    
    # No match - create new
    with transaction.atomic():
        # Generate unique slug
        base_slug = django_slugify(name)
        slug = base_slug
        counter = 1
        while Brand.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        brand = Brand.objects.create(
            name=name.strip(),
            slug=slug,
            **defaults
        )
        return brand, True


def get_or_create_category_canonical(
    name: str,
    parent: Optional[Category] = None,
    **defaults
) -> Tuple[Category, bool]:
    """
    Get or create category using canonical name matching
    Enforces hierarchical uniqueness (same parent)
    Returns: (category, created)
    """
    canonical = canonical_form(name)
    
    # Search within same parent level
    siblings = Category.objects.filter(parent=parent)
    for sibling in siblings:
        if canonical_form(sibling.name) == canonical:
            return sibling, False
    
    # No match - create new
    with transaction.atomic():
        # Generate unique slug (hierarchical scope)
        base_slug = django_slugify(name)
        slug = base_slug
        counter = 1
        while Category.objects.filter(slug=slug, parent=parent).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        category = Category.objects.create(
            name=name.strip(),
            slug=slug,
            parent=parent,
            **defaults
        )
        return category, True


def parse_category_path(path: str) -> Category:
    """
    Parse category path like "Parent / Child / Grandchild"
    Creates missing nodes deterministically
    Returns: deepest category
    """
    parts = [p.strip() for p in path.split('/')]
    
    current_parent = None
    for part in parts:
        category, created = get_or_create_category_canonical(
            name=part,
            parent=current_parent,
            series_mode='disabled'  # default, will be computed later
        )
        current_parent = category
    
    return current_parent


class Command(BaseCommand):
    help = 'Utility functions for canonical import (also importable)'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            'This module provides canonical import utilities:\n'
            '  - get_or_create_brand_canonical(name, **defaults)\n'
            '  - get_or_create_category_canonical(name, parent, **defaults)\n'
            '  - parse_category_path(path)\n'
            '\n'
            'Import in your code:\n'
            '  from apps.catalog.management.commands.canonical_import import (\n'
            '      get_or_create_brand_canonical,\n'
            '      get_or_create_category_canonical,\n'
            '      parse_category_path\n'
            '  )\n'
        ))
