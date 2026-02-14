from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Product, Category

class Command(BaseCommand):
    help = 'Fix missing spec_layout for products'

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write("FIXING SPEC LAYOUTS")
        self.stdout.write("=" * 70)

        # Target: ALL Products
        # cats = Category.objects.filter(slug__in=['bulasikhane', 'camasirhane'])
        
        fixed_count = 0
        
        with transaction.atomic():
            # Process ALL products
            self.stdout.write(f"\nScanning ALL Categories")
            products = Product.objects.all()
            
            for product in products:
                    # Check if spec_layout is empty
                    if not product.spec_layout or len(product.spec_layout) == 0:
                        
                        # Gather keys from all variants
                        all_keys = set()
                        variants = product.variants.all()
                        
                        if not variants.exists():
                            self.stdout.write(f"  [SKIP] {product.name} (No variants)")
                            continue
                            
                        for v in variants:
                            if v.specs:
                                all_keys.update(v.specs.keys())
                        
                        if not all_keys:
                            self.stdout.write(f"  [SKIP] {product.name} (Variants have no specs)")
                            continue
                            
                        # Sort keys for consistency (you might want a smarter sort later)
                        # Common order: capacity, power, voltage, dimensions, weight
                        preferred_order = ['capacity', 'power', 'voltage', 'dimensions', 'weight_kg', 'material']
                        
                        sorted_keys = []
                        # Add preferred keys first
                        for k in preferred_order:
                            if k in all_keys:
                                sorted_keys.append(k)
                                all_keys.remove(k)
                        
                        # Add remaining keys
                        sorted_keys.extend(sorted(list(all_keys)))
                        
                        old_layout = product.spec_layout
                        product.spec_layout = sorted_keys
                        product.save()
                        
                        self.stdout.write(f"  [FIXED] {product.name}")
                        self.stdout.write(f"          Layout: {old_layout} -> {sorted_keys}")
                        fixed_count += 1
                    else:
                        # Optional: Identify missing keys even if layout exists? 
                        # For now, only fix empty ones as requested "Zero Model".
                        pass

        self.stdout.write(self.style.SUCCESS(f"\nFixed {fixed_count} products."))
