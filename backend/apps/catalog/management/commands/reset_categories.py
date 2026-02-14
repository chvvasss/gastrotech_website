"""
Django management command to reset and create main categories.
Run with: python manage.py reset_categories
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Category, Product, Series, Brand, Variant


class Command(BaseCommand):
    help = 'Reset all categories and create 8 main categories'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*70)
        self.stdout.write("CATEGORY RESET & CREATION SCRIPT")
        self.stdout.write("="*70 + "\n")

        # Step 1: Reset everything
        self.reset_all_categories()

        # Step 2: Create main categories
        self.create_main_categories()

        # Step 3: Verify
        self.verify_categories()

        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("ALL DONE!"))
        self.stdout.write("="*70)
        self.stdout.write("\nNext steps:")
        self.stdout.write("1. Restart Django server: python manage.py runserver")
        self.stdout.write("2. Visit: http://localhost:3000/kategori")
        self.stdout.write("3. All 8 main categories should be visible\n")

    def reset_all_categories(self):
        """Delete all categories, products, series, and brands."""
        self.stdout.write("\n" + "="*70)
        self.stdout.write("RESETTING DATABASE - DELETING ALL DATA")
        self.stdout.write("="*70)

        with transaction.atomic():
            # Delete in correct order to avoid FK constraints
            self.stdout.write("\n[1/5] Deleting Variants...")
            variant_count = Variant.objects.count()
            Variant.objects.all().delete()
            self.stdout.write(f"    [OK] Deleted {variant_count} variants")

            self.stdout.write("\n[2/5] Deleting Products...")
            product_count = Product.objects.count()
            Product.objects.all().delete()
            self.stdout.write(f"    [OK] Deleted {product_count} products")

            self.stdout.write("\n[3/5] Deleting Series...")
            series_count = Series.objects.count()
            Series.objects.all().delete()
            self.stdout.write(f"    [OK] Deleted {series_count} series")

            self.stdout.write("\n[4/5] Deleting Categories...")
            category_count = Category.objects.count()
            Category.objects.all().delete()
            self.stdout.write(f"    [OK] Deleted {category_count} categories")

            self.stdout.write("\n[5/5] Deleting Brands...")
            brand_count = Brand.objects.count()
            Brand.objects.all().delete()
            self.stdout.write(f"    [OK] Deleted {brand_count} brands")

        self.stdout.write(f"\n{self.style.SUCCESS('Database reset complete!')}\n")

    def create_main_categories(self):
        """Create the 8 main root categories."""
        self.stdout.write("="*70)
        self.stdout.write("CREATING MAIN CATEGORIES")
        self.stdout.write("="*70 + "\n")

        categories = [
            {
                'name': 'Pişirme Ekipmanları',
                'slug': 'pisirme-ekipmanlari',
                'description_short': 'Profesyonel mutfak pişirme çözümleri',
                'order': 1,
            },
            {
                'name': 'Fırınlar',
                'slug': 'firinlar',
                'description_short': 'Profesyonel fırın çözümleri',
                'order': 2,
            },
            {
                'name': 'Soğutma Üniteleri',
                'slug': 'sogutma-uniteleri',
                'description_short': 'Endüstriyel soğutma sistemleri',
                'order': 3,
            },
            {
                'name': 'Hazırlık Ekipmanları',
                'slug': 'hazirlik-ekipmanlari',
                'description_short': 'Mutfak hazırlık ve işleme ekipmanları',
                'order': 4,
            },
            {
                'name': 'Kafeterya Ekipmanları',
                'slug': 'kafeterya-ekipmanlari',
                'description_short': 'Kafeterya ve self-servis çözümleri',
                'order': 5,
            },
            {
                'name': 'Çamaşırhane',
                'slug': 'camasirhane',
                'description_short': 'Endüstriyel çamaşırhane ekipmanları',
                'order': 6,
            },
            {
                'name': 'Tamamlayıcı Ekipmanlar',
                'slug': 'tamamlayici-ekipmanlar',
                'description_short': 'Mutfak tamamlayıcı ekipmanları',
                'order': 7,
            },
            {
                'name': 'Bulaşıkhane',
                'slug': 'bulasıkhane',
                'description_short': 'Profesyonel bulaşıkhane sistemleri',
                'order': 8,
            },
        ]

        with transaction.atomic():
            for cat_data in categories:
                category = Category.objects.create(
                    name=cat_data['name'],
                    slug=cat_data['slug'],
                    description_short=cat_data['description_short'],
                    order=cat_data['order'],
                    parent=None,  # Root category
                    is_featured=True,
                    menu_label=cat_data['name'],
                )
                self.stdout.write(f"[OK] Created: {category.name} (slug: {category.slug})")

        self.stdout.write(f"\n{self.style.SUCCESS('Successfully created 8 main categories!')}\n")

    def verify_categories(self):
        """Verify created categories."""
        self.stdout.write("="*70)
        self.stdout.write("VERIFICATION")
        self.stdout.write("="*70 + "\n")

        root_categories = Category.objects.filter(parent=None).order_by('order')

        self.stdout.write(f"Total root categories: {root_categories.count()}\n")
        self.stdout.write("Category Structure:")
        self.stdout.write("-" * 50)

        for cat in root_categories:
            self.stdout.write(f"{cat.order}. {cat.name}")
            self.stdout.write(f"   Slug: {cat.slug}")
            self.stdout.write(f"   Featured: {cat.is_featured}")
            self.stdout.write(f"   Description: {cat.description_short}")
            self.stdout.write("")

        self.stdout.write(self.style.SUCCESS("Verification complete!\n"))
