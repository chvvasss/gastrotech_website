"""
Django management command to add subcategories to Fırınlar category.
Run with: python manage.py add_firinlar_subcategories
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Category


class Command(BaseCommand):
    help = 'Add subcategories to Fırınlar category'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*70)
        self.stdout.write("ADDING FIRINLAR SUBCATEGORIES")
        self.stdout.write("="*70 + "\n")

        # Get Fırınlar category
        try:
            firinlar = Category.objects.get(slug='firinlar')
            self.stdout.write(f"Found parent category: {firinlar.name}\n")
        except Category.DoesNotExist:
            self.stdout.write(self.style.ERROR("Error: Fırınlar category not found!"))
            self.stdout.write("Please run: python manage.py reset_categories first\n")
            return

        # Define subcategories
        subcategories = [
            {
                'name': 'KWIK-CO Serisi Konveksiyonel Fırınlar',
                'slug': 'kwik-co-konveksiyonel',
                'description_short': 'KWIK-CO serisi profesyonel konveksiyonel fırınlar',
                'order': 1,
            },
            {
                'name': 'KWIK Serisi Pro Wash Fırınlar',
                'slug': 'kwik-pro-wash',
                'description_short': 'KWIK serisi pro wash özellikli fırınlar',
                'order': 2,
            },
            {
                'name': 'Elektrikli Fırınlar',
                'slug': 'elektrikli-firinlar',
                'description_short': 'Profesyonel elektrikli fırın çözümleri',
                'order': 3,
            },
            {
                'name': 'Taş Tabanlı Bakery Fırınlar',
                'slug': 'tas-tabanli-bakery',
                'description_short': 'Taş tabanlı profesyonel bakery fırınları',
                'order': 4,
            },
            {
                'name': 'Pizza Fırınları',
                'slug': 'pizza-firinlari',
                'description_short': 'Profesyonel pizza fırını çözümleri',
                'order': 5,
            },
        ]

        # Create subcategories
        with transaction.atomic():
            for subcat_data in subcategories:
                # Check if already exists
                if Category.objects.filter(slug=subcat_data['slug']).exists():
                    self.stdout.write(f"[SKIP] Already exists: {subcat_data['name']}")
                    continue

                subcategory = Category.objects.create(
                    name=subcat_data['name'],
                    slug=subcat_data['slug'],
                    description_short=subcat_data['description_short'],
                    order=subcat_data['order'],
                    parent=firinlar,
                    is_featured=True,
                    menu_label=subcat_data['name'],
                )
                self.stdout.write(f"[OK] Created: {subcategory.name}")

        self.stdout.write(f"\n{self.style.SUCCESS('Successfully added Fırınlar subcategories!')}\n")

        # Verify
        self.verify_subcategories(firinlar)

    def verify_subcategories(self, parent):
        """Verify created subcategories."""
        self.stdout.write("="*70)
        self.stdout.write("VERIFICATION")
        self.stdout.write("="*70 + "\n")

        subcategories = Category.objects.filter(parent=parent).order_by('order')

        self.stdout.write(f"Parent: {parent.name}")
        self.stdout.write(f"Total subcategories: {subcategories.count()}\n")
        self.stdout.write("Subcategory Structure:")
        self.stdout.write("-" * 50)

        for subcat in subcategories:
            self.stdout.write(f"{subcat.order}. {subcat.name}")
            self.stdout.write(f"   Slug: {subcat.slug}")
            self.stdout.write(f"   Parent: {subcat.parent.name}")
            self.stdout.write(f"   Description: {subcat.description_short}")
            self.stdout.write("")

        self.stdout.write(self.style.SUCCESS("Verification complete!\n"))

        self.stdout.write("="*70)
        self.stdout.write("NEXT STEPS")
        self.stdout.write("="*70)
        self.stdout.write("\nTest URLs:")
        self.stdout.write("1. View all categories:")
        self.stdout.write("   http://localhost:3000/kategori")
        self.stdout.write("\n2. View Fırınlar subcategories:")
        self.stdout.write("   http://localhost:3000/kategori/firinlar")
        self.stdout.write("\n3. API endpoints:")
        self.stdout.write("   http://localhost:8000/api/v1/categories/tree/")
        self.stdout.write("   http://localhost:8000/api/v1/categories/firinlar/children/\n")
