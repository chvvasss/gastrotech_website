from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.catalog.models import Product, SpecTemplate, SpecKey

class Command(BaseCommand):
    help = 'Extracts common Spec Templates from existing Product spec_layout usage'

    def handle(self, *args, **options):
        self.stdout.write("Analyzing existing product Spec Layouts...")
        
        # 1. Group products by layout
        # Map: tuple(layout) -> list of products
        layout_groups = {}
        
        products = Product.objects.filter(spec_layout__isnull=False).select_related('series', 'series__category')
        
        for p in products:
            if not p.spec_layout or not isinstance(p.spec_layout, list) or len(p.spec_layout) == 0:
                continue
                
            # Normalize layout (maybe sort? No, order matters visually)
            # We keep the order as is, assuming consistent entry.
            # If duplicates exist with different order, they are treated as different templates.
            layout_tuple = tuple(p.spec_layout)
            
            if layout_tuple not in layout_groups:
                layout_groups[layout_tuple] = []
            
            layout_groups[layout_tuple].append(p)
            
        self.stdout.write(f"Found {len(layout_groups)} unique layouts across {products.count()} products.")
        
        created_count = 0
        
        # 2. Create Templates
        for layout_tuple, group_products in layout_groups.items():
            count = len(group_products)
            layout_list = list(layout_tuple)
            
            # Determine best name
            # Find most common category
            categories = [p.series.category.name for p in group_products if p.series and p.series.category]
            if categories:
                # Simple mode: Takes the most frequent category
                from collections import Counter
                most_common = Counter(categories).most_common(1)
                cat_name = most_common[0][0]
                
                # Construct name
                # e.g. "Pişiriciler Şablonu (4 Özellik)"
                # If multiple templates for same category exists, we might need differentiation.
                # We'll rely on unique constraint check or append keys helper.
                base_name = f"{cat_name} Şablonu"
                suffix = f" ({len(layout_list)} Özellik)"
                
                # Check if specific enough
                name = f"{base_name}{suffix}"
                
                # If name exists but layout logic is different, append first key to disambiguate
                if SpecTemplate.objects.filter(name=name).exclude(spec_layout=layout_list).exists():
                     name = f"{base_name} - {layout_list[0].title()}{suffix}"
            else:
                name = f"Genel Şablon ({len(layout_list)} Özellik)"

            # Ensure unique name if collision still persists (e.g. same category, same length, different keys)
            counter = 1
            original_name = name
            while SpecTemplate.objects.filter(name=name).exclude(spec_layout=layout_list).exists():
                counter += 1
                name = f"{original_name} {counter}"

            # Create or Get
            # We filter by spec_layout to match existing
            
            # Note: storing JSON lists in exact order match for lookup is tricky in some DBs,
            # but usually fine if we just create if not exists by name/content logic.
            # Here we try to get by layout first if possible? No, we can't query exact JSON list equality easily across DBs consistently without strict exactness
            # So we check if *any* template has this layout.
            
            existing = None
            for t in SpecTemplate.objects.all():
                if t.spec_layout == layout_list:
                    existing = t
                    break
            
            if existing:
                self.stdout.write(f"Skipping existing template for {name} (matches {existing.name})")
                continue
                
            # Create
            SpecTemplate.objects.create(
                name=name,
                spec_layout=layout_list,
                # We could infer default notes from products here too, but let's keep it simple
            )
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"Created Template: {name} (used by {count} products)"))

        self.stdout.write(self.style.SUCCESS(f"Done. Created {created_count} new SpecTemplates."))
