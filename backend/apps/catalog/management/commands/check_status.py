"""Check DB status for images and PDFs."""
from django.core.management.base import BaseCommand
from apps.catalog.models import Media, ProductMedia, Product, CategoryCatalog, Variant
import os


class Command(BaseCommand):
    help = "Check DB status for images and PDFs"

    def handle(self, *args, **options):
        self.stdout.write("=== DB STATUS ===")
        self.stdout.write(f"Total Media: {Media.objects.count()}")
        self.stdout.write(f"Image Media: {Media.objects.filter(kind='image').count()}")
        self.stdout.write(f"Document Media: {Media.objects.filter(kind='document').count()}")
        self.stdout.write(f"Products: {Product.objects.count()}")
        self.stdout.write(f"Variants: {Variant.objects.count()}")
        self.stdout.write(f"ProductMedia links: {ProductMedia.objects.count()}")
        self.stdout.write(f"CategoryCatalog links: {CategoryCatalog.objects.count()}")

        prods_with_img = Product.objects.filter(product_media__media__kind='image').distinct().count()
        prods_total = Product.objects.count()
        self.stdout.write(f"Products WITH images: {prods_with_img}")
        self.stdout.write(f"Products WITHOUT images: {prods_total - prods_with_img}")

        # Check PDF status
        self.stdout.write("\n=== CATALOG PDFs ===")
        cats = CategoryCatalog.objects.select_related('media', 'category').all()
        for c in cats:
            if c.media:
                blob_size = c.media.size_bytes or 0
                media_info = f"{c.media.filename} ({blob_size} bytes)"
            else:
                media_info = "NO MEDIA"
            cat_name = c.category.name if c.category else "NO CAT"
            self.stdout.write(f"  CC#{c.id}: category='{cat_name}' media='{media_info}'")

        # Check for document media
        self.stdout.write("\n=== DOCUMENT MEDIA ===")
        doc_media = Media.objects.filter(kind='document')
        for m in doc_media:
            has_bytes = bool(m.bytes) if m.bytes else False
            self.stdout.write(f"  Media#{m.id}: {m.filename} | has_bytes={has_bytes} | size_bytes={m.size_bytes}")

        # Products without images
        self.stdout.write("\n=== PRODUCTS WITHOUT IMAGES (first 30) ===")
        prods_no_img = Product.objects.exclude(product_media__media__kind='image')[:30]
        for p in prods_no_img:
            variants = list(p.variants.values_list('model_code', flat=True))
            self.stdout.write(f"  {p.name} | variants={variants}")

        # Count source files
        src_dir = r"C:\Users\emir\Desktop\Fotolar"
        total_files = 0
        for root, dirs, files in os.walk(src_dir):
            total_files += len([f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        self.stdout.write(f"\nTotal image files in Fotolar: {total_files}")

        # Check all variant model codes vs available images
        self.stdout.write("\n=== MATCHING ANALYSIS ===")
        all_variants = Variant.objects.all().values_list('model_code', flat=True)
        variant_codes = set(all_variants)
        self.stdout.write(f"Total unique variant model codes: {len(variant_codes)}")

        # Scan all image filenames
        image_names = set()
        for root, dirs, files in os.walk(src_dir):
            for f in files:
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    name_no_ext = os.path.splitext(f)[0]
                    image_names.add(name_no_ext)
        self.stdout.write(f"Total unique image names: {len(image_names)}")

        matched = variant_codes & image_names
        self.stdout.write(f"Matching variant codes to image names: {len(matched)}")
        unmatched_variants = variant_codes - image_names
        self.stdout.write(f"Variant codes WITHOUT matching image: {len(unmatched_variants)}")
        unmatched_images = image_names - variant_codes
        self.stdout.write(f"Image names WITHOUT matching variant: {len(unmatched_images)}")
