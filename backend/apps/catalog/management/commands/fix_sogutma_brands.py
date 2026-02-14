"""
Fix brand-category M2M relationships for Soğutma category
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Brand, Category, BrandCategory, Product

class Command(BaseCommand):
    help = 'Link brands to Soğutma category based on products'

    def handle(self, *args, **options):
        # Find Soğutma category
        sogutma = Category.objects.get(slug='sogutma-uniteleri')
        self.stdout.write(f"Found category: {sogutma.name} (id={sogutma.id})")
        
        # Find all brands that have products in this category
        products_in_sogutma = Product.objects.filter(category=sogutma)
        brand_ids = set(products_in_sogutma.values_list('brand_id', flat=True))
        
        self.stdout.write(f"\nBrands with products in Soğutma: {len(brand_ids)}")
        
        with transaction.atomic():
            for brand_id in brand_ids:
                if not brand_id:
                    continue
                    
                brand = Brand.objects.get(id=brand_id)
                self.stdout.write(f"  Checking brand: {brand.name} ({brand.slug})")
                
                # Check if link exists
                link, created = BrandCategory.objects.get_or_create(
                    brand=brand,
                    category=sogutma,
                    defaults={'is_active': True}
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f"    Created BrandCategory link"))
                else:
                    # Make sure it's active
                    if not link.is_active:
                        link.is_active = True
                        link.save()
                        self.stdout.write(self.style.SUCCESS(f"    Activated existing link"))
                    else:
                        self.stdout.write(f"    Link already exists and active")
        
        # Verify
        brand_links = BrandCategory.objects.filter(category=sogutma, is_active=True)
        self.stdout.write(f"\nTotal active brand links for Soğutma: {brand_links.count()}")
        for bl in brand_links:
            self.stdout.write(f"  - {bl.brand.name}")
