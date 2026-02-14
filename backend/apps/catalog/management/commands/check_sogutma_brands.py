"""
Check and fix brands for Soğutma category products
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Product, Category, Brand, Series

class Command(BaseCommand):
    help = 'Check and fix brands for Soğutma category'

    def handle(self, *args, **options):
        # Find Soğutma category
        sogutma = Category.objects.get(slug='sogutma-uniteleri')
        
        # Get products in this category
        products = Product.objects.filter(category=sogutma)
        self.stdout.write(f"Products in Soğutma: {products.count()}")
        
        # Check brand distribution
        self.stdout.write("\nBrand distribution:")
        with_brand = 0
        without_brand = 0
        
        for p in products:
            if p.brand:
                with_brand += 1
                self.stdout.write(f"  {p.name[:50]} - Brand: {p.brand.name}")
            else:
                without_brand += 1
                self.stdout.write(self.style.WARNING(f"  {p.name[:50]} - Brand: NULL"))
        
        self.stdout.write(f"\n{with_brand} products with brand, {without_brand} without brand")
        
        # Check series in this category
        series_list = Series.objects.filter(category=sogutma)
        self.stdout.write(f"\nSeries in Soğutma: {series_list.count()}")
        for s in series_list:
            prod_count = Product.objects.filter(series=s).count()
            self.stdout.write(f"  {s.name} ({prod_count} products)")
        
        # List all brands in database
        self.stdout.write("\n\nAll brands in database:")
        for b in Brand.objects.all():
            prod_count = Product.objects.filter(brand=b).count()
            self.stdout.write(f"  {b.name} (slug: {b.slug}) - {prod_count} products")
