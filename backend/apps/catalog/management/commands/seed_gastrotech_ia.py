"""
Alias command for seed_demo_catalog.

This command is an alias for `seed_demo_catalog` to match the naming
convention requested in the Catalog IA implementation.

Usage:
    python manage.py seed_gastrotech_ia
    python manage.py seed_gastrotech_ia --clear
    python manage.py seed_gastrotech_ia --generate-leaf-products
"""

from .seed_demo_catalog import Command as SeedDemoCatalogCommand


class Command(SeedDemoCatalogCommand):
    """
    Seed Gastrotech Information Architecture data.
    
    Creates:
    - Categories (Pişirme Üniteleri, Fırınlar, etc.)
    - Series (600/700/900/Drop-in/Eko/Banket)
    - TaxonomyNodes (Ocaklar > Gazlı/Elektrikli, etc.)
    - Products with variants and specs
    - SpecKeys for specification tables
    
    Idempotent: safe to run multiple times.
    """
    
    help = "Seed Gastrotech catalog IA data (alias for seed_demo_catalog)"
