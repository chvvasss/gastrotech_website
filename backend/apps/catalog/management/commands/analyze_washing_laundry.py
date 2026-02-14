from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from apps.catalog.models import Category, Series, Product, Brand, BrandCategory

class Command(BaseCommand):
    help = 'Analyze and fix Dishwashing and Laundry categories'

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write("ANALYZING DISHWASHING & LAUNDRY")
        self.stdout.write("=" * 70)

        # Target Categories
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

        categories = {}
        for slug in targets.keys():
            try:
                cat = Category.objects.get(slug=slug)
                categories[slug] = cat
                self.stdout.write(f"Found Category: {cat.name} ({cat.slug}) - ID: {cat.id}")
            except Category.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Category not found: {slug}"))
                return

        # 1. Identify Candidates
        self.stdout.write("\nSEARCHING FOR CANDIDATES...")
        
        candidates = []
        
        # We search through ALL series to find miscategorized ones
        all_series = Series.objects.select_related('category').prefetch_related('products').all()
        
        for series in all_series:
            # Check if likely single product series
            products = list(series.products.all())
            if not products:
                continue

            product_names = " ".join([p.name.lower() or "" for p in products])
            series_name = series.name.lower()
            combined_text = f"{series_name} {product_names}"
            
            matched_slug = None
            matched_keywords = []

            for slug, keywords in targets.items():
                for kw in keywords:
                    if kw.lower() in combined_text:
                        matched_slug = slug
                        matched_keywords.append(kw)
                        break # Found a keyword for this category
                if matched_slug:
                    break # Found a category
            
            if matched_slug:
                current_slug = series.category.slug if series.category else "None"
                
                # If currently in a different category (and not already in the target or a sub-category context)
                # Note: "Hazırlık" might have overlap (e.g. vegetable washer), but "Dishwasher" is specific.
                
                if current_slug != matched_slug:
                    candidates.append({
                        'series': series,
                        'current_cat': series.category.name if series.category else "None",
                        'target_cat': categories[matched_slug],
                        'keyword': matched_keywords[0],
                        'products_count': len(products)
                    })

        self.stdout.write(f"Found {len(candidates)} candidates for moving.\n")
        
        for cand in candidates:
            self.stdout.write(f"  [MOVE] '{cand['series'].name}' ({cand['products_count']} products)")
            self.stdout.write(f"         From: {cand['current_cat']} -> To: {cand['target_cat'].name} (Matched: '{cand['keyword']}')")

        # 2. Fix Logic (Dry Run by default unless --apply passed? No, let's just do it directly if user asked)
        # But this is a script, maybe I should use an argument. 
        # I'll add an argument --apply
        
        # Actually I can't easily pass args via run_command nicely sometimes, but I'll assume I run it with flags.
        # Wait, I'll just separate analysis and fix.
        # Or I'll output SQL. The user seems to appreciate SQL.
        
        # Let's generate SQL.
        
        with open('fix_washing_laundry.sql', 'w', encoding='utf-8') as f:
            f.write("-- Fix Dishwashing and Laundry Categories\n")
            f.write("BEGIN;\n\n")
            
            for cand in candidates:
                series_id = cand['series'].id
                target_id = cand['target_cat'].id
                
                f.write(f"-- Moving {cand['series'].name}\n")
                f.write(f"UPDATE catalog_series SET category_id = '{target_id}' WHERE id = '{series_id}';\n")
                f.write(f"UPDATE catalog_product SET category_id = '{target_id}' WHERE series_id = '{series_id}';\n")
                f.write("\n")
                
            f.write("COMMIT;\n")
            
        self.stdout.write(f"\nSQL script generated: fix_washing_laundry.sql")

        # 3. Check for Brands in these categories
        self.stdout.write("\nCHECKING BRANDS...")
        for slug, cat in categories.items():
            # Get brands of products currently in this category OR in the candidates
            
            # Current products
            current_brands = set(Product.objects.filter(category=cat).values_list('brand_id', flat=True))
            
            # Candidate products (if we move them)
            future_brands = set()
            for cand in candidates:
                if cand['target_cat'] == cat:
                    for p in cand['series'].products.all():
                        if p.brand_id:
                            future_brands.add(p.brand_id)
            
            all_brand_ids = current_brands.union(future_brands)
            
            self.stdout.write(f"Category: {cat.name} will have {len(all_brand_ids)} brands.")
            
            for bid in all_brand_ids:
                if not bid: continue
                # Check link
                exists = BrandCategory.objects.filter(brand_id=bid, category=cat).exists()
                if not exists:
                    self.stdout.write(f"  [MISSING LINK] Brand {bid} needs link to {cat.name}")
                    # SQL for this too
                    with open('fix_washing_laundry_brands.sql', 'a', encoding='utf-8') as f:
                        # We need a predictable UUID for the link? No, let DB handle if possible or auto-gen.
                        # Using raw SQL insert for M2M is tricky with IDs. 
                        # Better to use Django to create links or output a Django script command.
                        pass
        
        self.stdout.write("\nAnalysis Complete.")
