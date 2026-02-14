"""
Django management command to move cooling-related series to Soğutma Üniteleri category
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Series, Category, Product

class Command(BaseCommand):
    help = 'Move cooling series and products to Soğutma category'

    def handle(self, *args, **options):
        # Find Soğutma category
        try:
            sogutma_cat = Category.objects.get(slug='sogutma-uniteleri')
            self.stdout.write(f"Found Soğutma category: {sogutma_cat.id}")
        except Category.DoesNotExist:
            self.stdout.write(self.style.ERROR("Soğutma Üniteleri category not found!"))
            return
        
        # Series that should be in Soğutma (cooling-related)
        cooling_series_slugs = [
            'basic-seri',  # Has buzdolabı, dondurucu products
            'premium-seri',  # Has buzdolabı, dondurucu, şok soğutucu
            'bar-alti',  # Bar altı dondurucular
            'dik-tip',  # Dik tip buzdolapları
            'scotsman-ec-series',  # Ice machines
            'scotsman-ac-series',
            'scotsman-mxg-series',
            'scotsman-nu-nw-series',
            'scotsman-af-mf-series',
            'scotsman-mxf-series',
            'scotsman-sb-serisi',
            'scotsman-ubh-serisi',
            'scotsman-legacy-series',
            'scotsman-dxn-series',
            'b-serisi-gurme-buz',
        ]
        
        with transaction.atomic():
            moved_series = 0
            moved_products = 0
            
            for slug in cooling_series_slugs:
                try:
                    series = Series.objects.get(slug=slug)
                    old_cat = series.category
                    
                    if series.category_id != sogutma_cat.id:
                        self.stdout.write(f"Moving series '{series.name}' from '{old_cat.name if old_cat else 'None'}' to Soğutma")
                        series.category = sogutma_cat
                        series.save()
                        moved_series += 1
                        
                        # Also update products in this series
                        products = Product.objects.filter(series=series)
                        for product in products:
                            if product.category_id != sogutma_cat.id:
                                product.category = sogutma_cat
                                product.save()
                                moved_products += 1
                    else:
                        self.stdout.write(f"Series '{series.name}' already in Soğutma")
                        
                except Series.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Series '{slug}' not found in database"))
            
            self.stdout.write(self.style.SUCCESS(f"\nMoved {moved_series} series and {moved_products} products to Soğutma"))
            
            # Verify
            sogutma_series = Series.objects.filter(category=sogutma_cat).count()
            sogutma_products = Product.objects.filter(category=sogutma_cat).count()
            self.stdout.write(f"\nSoğutma now has: {sogutma_series} series, {sogutma_products} products")
