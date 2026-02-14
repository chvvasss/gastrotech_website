"""
Reorganize all series into correct categories based on product names/types
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Brand, Category, Series, Product, BrandCategory

class Command(BaseCommand):
    help = 'Reorganize series into correct categories'

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write("REORGANIZING SERIES INTO CORRECT CATEGORIES")
        self.stdout.write("=" * 70)
        
        # Define category keywords (Turkish)
        category_keywords = {
            'sogutma-uniteleri': [
                'buzdolabı', 'buzdolap', 'dondurucu', 'soğutma', 'sogutma', 
                'buz makin', 'ice', 'şok soğutucu', 'sok sogutucu', 'chiller',
                'blast', 'scotsman', 'şişe soğutucu', 'sise sogutucu'
            ],
            'bulasıkhane': [
                'bulaşık', 'bulasik', 'bardak yıkama', 'bardak yikama', 
                'kazan yıkama', 'kazan yikama', 'yıkama makine'
            ],
            'camasirhane': [
                'çamaşır', 'camasir', 'ütü', 'kurutma', 'yıkama sıkma',
                'silindir ütü', 'paskala', 'pres ütü', 'leke çıkarma'
            ],
            'hazirlik-ekipmanlari': [
                'doğrama', 'dograma', 'dilimleme', 'kesme', 'parçalama',
                'hamur', 'vakum', 'sebze', 'meyve', 'mikser', 'blender',
                'el mikseri', 'stand mikser'
            ],
            'kafeterya-ekipmanlari': [
                'kahve', 'espresso', 'değirmen', 'degirmen', 'fincan',
                'süt soğutucu', 'sut sogutucu', 'bar blender', 'narenciye',
                'meyve presi', 'sıkacağı', 'sikacagi', 'barista', 'tamper'
            ],
            'pisirme-ekipmanlari': [
                'pişirme', 'pisirme', 'ocak', 'izgar', 'gril', 'frit', 
                'wok', 'benmari', 'devrilir', 'salamander', 'kızartma'
            ],
            'firinlar': [
                'fırın', 'firin', 'kombi', 'konveksiyon', 'pizza fırın',
                'taş tabanlı', 'bakery', 'maestro', 'prime', 'thermospeed',
                'icombi', 'i-combi', 'vario', 'rational'
            ],
            'tamamlayici-ekipmanlar': [
                'ayak', 'raf', 'istif', 'eviye', 'ızgara', 'sinek tutucu',
                'sterilizatör', 'tepsi', 'tablet'
            ],
            'aksesuarlar': [
                'aksesuar', 'yedek', 'parça'
            ]
        }
        
        # Get all categories
        categories = {cat.slug: cat for cat in Category.objects.all()}
        
        with transaction.atomic():
            move_count = 0
            
            for series in Series.objects.all():
                # Get the product name (for single-product series)
                products = Product.objects.filter(series=series)
                if not products.exists():
                    continue
                
                # Check product names for keywords
                product_names = ' '.join([p.name.lower() for p in products])
                series_name = series.name.lower()
                combined_text = f"{series_name} {product_names}"
                
                # Find matching category
                best_category = None
                for cat_slug, keywords in category_keywords.items():
                    if cat_slug in categories:
                        for keyword in keywords:
                            if keyword.lower() in combined_text:
                                best_category = categories[cat_slug]
                                break
                    if best_category:
                        break
                
                # If found and different from current, move it
                if best_category and series.category != best_category:
                    old_cat_name = series.category.name if series.category else 'None'
                    self.stdout.write(f"Moving '{series.name}' from '{old_cat_name}' -> '{best_category.name}'")
                    
                    series.category = best_category
                    series.save()
                    
                    # Also update products
                    for product in products:
                        product.category = best_category
                        product.save()
                    
                    move_count += 1
            
            self.stdout.write(self.style.SUCCESS(f"\nMoved {move_count} series to correct categories"))
        
        # Create brand-category links for moved items
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("CREATING BRAND-CATEGORY LINKS")
        self.stdout.write("=" * 50)
        
        with transaction.atomic():
            link_count = 0
            for cat in Category.objects.all():
                products_in_cat = Product.objects.filter(category=cat)
                brand_ids = set(products_in_cat.values_list('brand_id', flat=True))
                
                for brand_id in brand_ids:
                    if not brand_id:
                        continue
                    brand = Brand.objects.get(id=brand_id)
                    
                    link, created = BrandCategory.objects.get_or_create(
                        brand=brand,
                        category=cat,
                        defaults={'is_active': True}
                    )
                    
                    if created:
                        self.stdout.write(f"  Created: {brand.name} -> {cat.name}")
                        link_count += 1
            
            self.stdout.write(self.style.SUCCESS(f"\nCreated {link_count} new brand-category links"))
        
        # Final summary
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("FINAL CATEGORY DISTRIBUTION")
        self.stdout.write("=" * 70)
        
        for cat in Category.objects.all().order_by('name'):
            series_count = Series.objects.filter(category=cat).count()
            product_count = Product.objects.filter(category=cat).count()
            self.stdout.write(f"{cat.name}: {series_count} series, {product_count} products")
