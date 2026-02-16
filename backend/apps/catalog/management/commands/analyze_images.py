"""Analyze unmatched images and variants to find import strategies."""
from django.core.management.base import BaseCommand
from apps.catalog.models import Media, ProductMedia, Product, Variant
import os


class Command(BaseCommand):
    help = "Analyze unmatched images and variants"

    def handle(self, *args, **options):
        src_dir = r"C:\Users\emir\Desktop\Fotolar"

        # Get all variant model codes
        all_variants = {}
        for v in Variant.objects.select_related('product').all():
            all_variants[v.model_code] = v

        # Get all image files
        image_files = {}
        for root, dirs, files in os.walk(src_dir):
            folder = os.path.basename(root)
            for f in files:
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    name_no_ext = os.path.splitext(f)[0]
                    image_files[name_no_ext] = {
                        'path': os.path.join(root, f),
                        'folder': folder,
                        'filename': f,
                    }

        # Find already imported images
        existing_media = set(Media.objects.filter(kind='image').values_list('filename', flat=True))
        self.stdout.write(f"Already imported image media count: {len(existing_media)}")

        # Find already linked products
        linked_products = set(
            ProductMedia.objects.values_list('product_id', flat=True)
        )
        self.stdout.write(f"Products with any media link: {len(linked_products)}")

        # Classify unmatched images
        matched = []
        unmatched = []
        already_imported = []

        for name, info in image_files.items():
            if info['filename'] in existing_media:
                already_imported.append(name)
            elif name in all_variants:
                matched.append(name)
            else:
                unmatched.append(name)

        self.stdout.write(f"\n=== IMAGE CLASSIFICATION ===")
        self.stdout.write(f"Already imported: {len(already_imported)}")
        self.stdout.write(f"Matched but not imported: {len(matched)}")
        self.stdout.write(f"Unmatched: {len(unmatched)}")

        # Show unmatched images
        self.stdout.write(f"\n=== UNMATCHED IMAGES (all) ===")
        for name in sorted(unmatched):
            info = image_files[name]
            self.stdout.write(f"  {info['folder']}/{info['filename']} | name='{name}'")

        # Show matched but not imported
        self.stdout.write(f"\n=== MATCHED BUT NOT IMPORTED ===")
        for name in sorted(matched)[:50]:
            info = image_files[name]
            variant = all_variants[name]
            self.stdout.write(f"  {info['filename']} -> Variant '{name}' -> Product '{variant.product.name}'")

        # Check for numeric-only filenames like "0.png", "1.jpg", etc.
        self.stdout.write(f"\n=== NUMERIC FILENAMES ===")
        for name in sorted(unmatched):
            if name.isdigit():
                info = image_files[name]
                self.stdout.write(f"  {info['folder']}/{info['filename']}")
