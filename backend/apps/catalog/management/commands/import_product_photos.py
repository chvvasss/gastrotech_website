
# apps/catalog/management/commands/import_product_photos.py

"""
Import product images from C:\\Users\\emir\\Desktop\\Fotolar

Strategy:
1. Scan all image files in subdirectories
2. For files named with model codes (e.g. EKO6010.png), match to Variant.model_code -> Product
3. For files named "0.png"/"0.jpg", match folder name (page range) to Product.pdf_ref
4. Create Media records and link via ProductMedia

Run: python manage.py import_product_photos --dry-run
     python manage.py import_product_photos

"""
import os
import hashlib
import mimetypes
from pathlib import Path
from PIL import Image as PILImage
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.catalog.models import Media, Product, ProductMedia, Variant


class Command(BaseCommand):
    help = "Import product images from C:\\Users\\emir\\Desktop\\Fotolar"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without creating records",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        photos_dir = Path(r"C:\Users\emir\Desktop\Fotolar")
        image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
        skip_filenames = {"liste.png", "liste.jpg"}

        if dry_run:
            self.stdout.write(self.style.WARNING("=== DRY RUN MODE ==="))

        if not photos_dir.exists():
            self.stdout.write(self.style.ERROR(f"Directory not found: {photos_dir}"))
            return

        # Listing stats
        all_variants_count = Variant.objects.count()
        all_products_count = Product.objects.count()
        self.stdout.write(f"Total variants in DB: {all_variants_count}")
        self.stdout.write(f"Total products in DB: {all_products_count}")

        matched = []
        unmatched = []
        skipped = []
        duplicates = []

        # Recurse
        for folder in sorted(photos_dir.iterdir()):
            if not folder.is_dir():
                continue
            
            for img_file in sorted(folder.iterdir()):
                if not img_file.is_file():
                    continue
                if img_file.suffix.lower() not in image_extensions:
                    continue
                if img_file.name.lower() in skip_filenames:
                    skipped.append(str(img_file))
                    continue
                
                filename_stem = img_file.stem
                folder_name = folder.name
                
                product, variant, method = self.find_product_for_image(filename_stem, folder_name)

                if product is None:
                    unmatched.append((str(img_file), filename_stem))
                    continue
                
                # Check existance
                existing = Media.objects.filter(filename=img_file.name).first()
                if existing:
                    already_linked = ProductMedia.objects.filter(
                        product=product, media=existing
                    ).exists()
                    if already_linked:
                        duplicates.append((str(img_file), product.name, "already_linked"))
                        continue
                
                matched.append({
                    "file": img_file,
                    "product": product,
                    "variant": variant,
                    "method": method,
                    "filename_stem": filename_stem,
                })

        # Report stats
        self.stdout.write("\n=== SCAN RESULTS ===")
        self.stdout.write(f"Matched:    {len(matched)}")
        self.stdout.write(f"Unmatched:  {len(unmatched)}")
        self.stdout.write(f"Duplicates: {len(duplicates)}")
        self.stdout.write(f"Skipped:    {len(skipped)}")

        if unmatched:
            self.stdout.write("\n--- UNMATCHED FILES (First 20) ---")
            for path, stem in unmatched[:20]:
                self.stdout.write(f"  {stem:30s}  ({path})")

        if matched:
            self.stdout.write("\n--- MATCHED FILES (First 20) ---")
            for m in matched[:20]:
                v_code = m["variant"].model_code if m["variant"] else "-"
                self.stdout.write(f"  {m['filename_stem']:20s} -> {m['product'].name:40s}  variant={v_code}  method={m['method']}")

        if dry_run:
            self.stdout.write(self.style.SUCCESS("\n=== DRY RUN COMPLETE — no changes made ==="))
            return

        # Execution
        self.stdout.write(f"\n=== IMPORTING {len(matched)} IMAGES ===")
        created_count = 0
        error_count = 0

        for i, m in enumerate(matched):
            img_file = m["file"]
            product = m["product"]
            variant = m["variant"]
            
            try:
                file_bytes = img_file.read_bytes()
                content_type = mimetypes.guess_type(img_file.name)[0] or "image/png"
                width, height = self.get_image_dimensions(img_file)
                
                checksum = hashlib.sha256(file_bytes).hexdigest()
                existing_media = Media.objects.filter(checksum_sha256=checksum).first()
                
                if existing_media:
                    media = existing_media
                else:
                    media = Media(
                        kind=Media.Kind.IMAGE,
                        filename=img_file.name,
                        content_type=content_type,
                        bytes=file_bytes,
                        size_bytes=len(file_bytes),
                        width=width,
                        height=height,
                        checksum_sha256=checksum,
                    )
                    media.save()
                
                if not ProductMedia.objects.filter(product=product, media=media).exists():
                    max_order = ProductMedia.objects.filter(product=product).order_by("-sort_order").values_list("sort_order", flat=True).first()
                    sort_order = (max_order or 0) + 1
                    
                    has_primary = ProductMedia.objects.filter(product=product, is_primary=True).exists()
                    
                    ProductMedia.objects.create(
                        product=product,
                        media=media,
                        variant=variant,
                        alt=product.title_tr or product.name,
                        sort_order=sort_order,
                        is_primary=not has_primary,
                    )
                
                created_count += 1
                if (i + 1) % 10 == 0:
                    self.stdout.write(f"  Imported {i + 1}/{len(matched)}...")
            
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"  ERROR importing {img_file.name}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n=== IMPORT COMPLETE ==="))
        self.stdout.write(f"Successfully imported: {created_count}")
        self.stdout.write(f"Errors: {error_count}")

    def get_image_dimensions(self, filepath):
        try:
            with PILImage.open(filepath) as img:
                return img.width, img.height
        except Exception:
            return None, None

    def find_product_for_image(self, filename_stem, folder_name):
        # 1. Exact variant match
        variant = Variant.objects.filter(model_code=filename_stem).select_related("product").first()
        if variant:
            return variant.product, variant, "variant_exact"
        
        # 2. Case-insensitive variant match
        variant = Variant.objects.filter(model_code__iexact=filename_stem).select_related("product").first()
        if variant:
            return variant.product, variant, "variant_iexact"
        
        # 3. "0" -> PDF ref match
        if filename_stem == "0":
            # "009-010" -> "9", "10", "p9", "p10", etc.
            # Usually folder names map to pages in PDF catalog
            parts = folder_name.replace(".", "-").split("-")
            for part in parts:
                part = part.strip()
                if part.isdigit():
                    num = int(part)
                    # Try p9, p09, 9
                    candidates = [f"p{num}", f"p{part}", part]
                    for ref in candidates:
                        product = Product.objects.filter(pdf_ref=ref).first()
                        if product:
                            return product, None, f"pdf_ref:{ref}"
        
        # 4. Slug match
        product = Product.objects.filter(slug__iexact=filename_stem).first()
        if product:
            return product, None, "slug_match"
        
        # 5. Name match
        product = Product.objects.filter(name__iexact=filename_stem).first()
        if product:
            return product, None, "name_match"
        
        return None, None, "no_match"
