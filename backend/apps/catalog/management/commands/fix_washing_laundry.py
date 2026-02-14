from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Category, Series, Product, Brand, BrandCategory

class Command(BaseCommand):
    help = 'Fix Dishwashing and Laundry categories'

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write("FIXING DISHWASHING & LAUNDRY")
        self.stdout.write("=" * 70)

        # Target Categories & Keywords (Refined)
        targets = {
            'bulasikhane': [
                'bulaşık', 'bulasik', 'bardak yıkama', 'bardak yikama', 
                'kazan yıkama', 'kazan yikama', 'yıkama makinesi', 'yikama makinesi',
                'giyotin', 'konveyorlü bulaşık', 'konveyorlu bulasik', 'bulaşıkhane', 
                'sepetsiz', 'set altı bulaşık', 'set alti bulasik', 'tezgah altı bulaşık',
                'giyotin tip', 'konveyorlü tip'
            ],
            'camasirhane': [
                'çamaşır', 'camasir', 'kurutma makine', 'yıkama sıkma', 'yikama sikma',
                'silindir ütü', 'silindir utu', 'paskala', 'pres ütü', 'pres utu', 
                'leke çıkarma', 'leke cikarma', 'mellan', 'tolon', 'primus',
                'kurutma ve ütü', 'kurutma ve utu'
            ]
        }

        with transaction.atomic():
            categories = {}
            for slug in targets.keys():
                try:
                    cat = Category.objects.get(slug=slug)
                    categories[slug] = cat
                except Category.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Category not found: {slug}"))
                    return

            # 1. Identify and Move Candidates
            move_count = 0
            all_series = Series.objects.select_related('category').prefetch_related('products').all()
            
            for series in all_series:
                products = list(series.products.all())
                if not products:
                    continue

                product_names = " ".join([p.name.lower() or "" for p in products])
                series_name = series.name.lower()
                combined_text = f"{series_name} {product_names}"
                
                matched_slug = None
                
                # Check keywords
                for slug, keywords in targets.items():
                    for kw in keywords:
                        if kw.lower() in combined_text:
                            matched_slug = slug
                            break
                    if matched_slug:
                        break
                
                if matched_slug:
                    target_cat = categories[matched_slug]
                    current_slug = series.category.slug if series.category else "None"
                    
                    if current_slug != matched_slug:
                        self.stdout.write(f"Moving '{series.name}' -> {target_cat.name}")
                        
                        # Move Series
                        series.category = target_cat
                        series.save()
                        
                        # Move Products
                        for p in products:
                            p.category = target_cat
                            p.save()
                            
                        move_count += 1

            self.stdout.write(self.style.SUCCESS(f"\nMoved {move_count} series."))

            # 2. Fix Brand Internal Links for these categories
            self.stdout.write("\nFIXING BRANDS...")
            link_count = 0
            for slug, cat in categories.items():
                # Get all products in this category (now including moved ones)
                products = Product.objects.filter(category=cat)
                brand_ids = set(products.values_list('brand_id', flat=True))
                
                for bid in brand_ids:
                    if not bid: continue
                    brand = Brand.objects.get(id=bid)
                    
                    link, created = BrandCategory.objects.get_or_create(
                        brand=brand,
                        category=cat,
                        defaults={'is_active': True, 'order': 0}
                    )
                    
                    if created:
                        self.stdout.write(f"  Created link: {brand.name} -> {cat.name}")
                        link_count += 1
            
            self.stdout.write(self.style.SUCCESS(f"Created {link_count} new brand links."))
        
        self.stdout.write("\nProcess Complete.")
