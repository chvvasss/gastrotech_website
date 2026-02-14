
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from apps.catalog.models import Product, Series, Category

class Command(BaseCommand):
    help = "Finds and optionally fixes products/series that are orphans (in root category but not in subcategory)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply fixes (create mapped subcategories and move series). Default is dry-run.",
        )

    def handle(self, *args, **options):
        apply_mode = options["apply"]
        self.stdout.write(f"Running in {'APPLY' if apply_mode else 'DRY-RUN'} mode...")

        # Find Root Categories that have BOTH subcategories AND direct series
        # (This is the mixed state that caused visibility issues before the frontend fix)
        root_categories = Category.objects.filter(parent__isnull=True)
        
        orphans_found = 0
        fixed_count = 0

        for root_cat in root_categories:
            # Check if this category has subcategories
            has_subcategories = root_cat.children.exists()
            
            if not has_subcategories:
                # If a root category has NO subcategories, then having direct series is NORMAL.
                # Use --verbosity 2 to see these if needed.
                if options['verbosity'] > 1:
                    self.stdout.write(f"Skipping {root_cat.name}: No subcategories (pure series mode).")
                continue

            # Find direct series in this root category (Orphans in the context of a mixed category)
            # These are series where category=root_cat
            orphan_series = Series.objects.filter(category=root_cat)
            
            if not orphan_series.exists():
                continue

            self.stdout.write(f"\nScanning Category: {root_cat.name}")
            self.stdout.write(f"- Has {root_cat.children.count()} subcategories.")
            self.stdout.write(f"- Found {orphan_series.count()} direct series (orphans).")

            for series in orphan_series:
                product_count = series.products.filter(status='active').count()
                self.stdout.write(f"  > Series: {series.name} (Slug: {series.slug}) - {product_count} active products")
                
                orphans_found += 1

                if apply_mode:
                    # Fix logic: Move to "Diğer / Uncategorized" subcategory
                    # 1. Ensure "Diğer" subcategory exists for this root category
                    other_cat_slug = f"{root_cat.slug}-diger"
                    other_cat_name = "Diğer"
                    
                    other_cat, created = Category.objects.get_or_create(
                        slug=other_cat_slug,
                        parent=root_cat,
                        defaults={
                            "name": other_cat_name,
                            "menu_label": "Diğer Ürünler",
                            "order": 999, # Put at end
                            "is_featured": False
                        }
                    )
                    
                    if created:
                        self.stdout.write(f"    + Created 'Diğer' subcategory: {other_cat.name}")
                    
                    # 2. Move series to this subcategory
                    series.category = other_cat
                    series.save()
                    self.stdout.write(f"    -> Moved series '{series.name}' to '{other_cat.name}'")
                    
                    # 3. Update products in this series to also point to new category (denormalization)
                    products_updated = Product.objects.filter(series=series).update(category=other_cat)
                    self.stdout.write(f"    -> Updated {products_updated} products to new category.")
                    
                    fixed_count += 1

        self.stdout.write("\nSummary:")
        self.stdout.write(f"Orphan Series Found: {orphans_found}")
        if apply_mode:
            self.stdout.write(f"Fixed/Moved: {fixed_count}")
        else:
            self.stdout.write("No changes made (Dry-run). Use --apply to fix.")
