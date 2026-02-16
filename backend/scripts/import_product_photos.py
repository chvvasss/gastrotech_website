"""
Import product images from C:\\Users\\emir\\Desktop\\Fotolar

Strategy:
1. Scan all image files in subdirectories
2. For files named with model codes (e.g. EKO6010.png), match to Variant.model_code -> Product
3. For files named "0.png"/"0.jpg", match folder name (page range) to Product.pdf_ref
4. Create Media records and link via ProductMedia

Run: python manage.py runscript import_product_photos --script-args dryrun
      python manage.py runscript import_product_photos
"""
import os
import hashlib
import mimetypes
from pathlib import Path
from PIL import Image as PILImage

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django
django.setup()

from apps.catalog.models import Media, Product, ProductMedia, Variant


PHOTOS_DIR = Path(r"C:\Users\emir\Desktop\Fotolar")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
# Files to skip (generic/non-product)
SKIP_FILENAMES = {"liste.png", "liste.jpg"}


def get_image_dimensions(filepath):
    """Get image width and height."""
    try:
        with PILImage.open(filepath) as img:
            return img.width, img.height
    except Exception:
        return None, None


def find_product_for_image(filename_stem, folder_name):
    """
    Try to match an image to a product:
    1. Exact match on Variant.model_code
    2. Case-insensitive match on Variant.model_code
    3. For "0" files, match folder page range to Product.pdf_ref
    """
    # Strategy 1: Exact variant match
    variant = Variant.objects.filter(model_code=filename_stem).select_related("product").first()
    if variant:
        return variant.product, variant, "variant_exact"
    
    # Strategy 2: Case-insensitive variant match
    variant = Variant.objects.filter(model_code__iexact=filename_stem).select_related("product").first()
    if variant:
        return variant.product, variant, "variant_iexact"
    
    # Strategy 3: For generic files (named "0"), match folder name to pdf_ref
    if filename_stem == "0":
        # Folder name like "009-010" -> try matching pages p9, p10, p009, p010
        parts = folder_name.replace(".", "-").split("-")
        for part in parts:
            part = part.strip()
            if part.isdigit():
                # Try with and without leading zeros
                page_num = int(part)
                for ref in [f"p{page_num}", f"p{part}", part]:
                    product = Product.objects.filter(pdf_ref=ref).first()
                    if product:
                        return product, None, f"pdf_ref:{ref}"
    
    # Strategy 4: Try matching filename to product name/slug 
    product = Product.objects.filter(slug__iexact=filename_stem).first()
    if product:
        return product, None, "slug_match"
    
    # Strategy 5: Try matching filename to product name
    product = Product.objects.filter(name__iexact=filename_stem).first()
    if product:
        return product, None, "name_match"
    
    return None, None, "no_match"


def run(*args):
    dry_run = "dryrun" in args if args else False
    
    if dry_run:
        print("=== DRY RUN MODE ===\n")
    
    # First, list all existing variant model codes for reference
    all_variants = set(Variant.objects.values_list("model_code", flat=True))
    print(f"Total variants in DB: {len(all_variants)}")
    print(f"Total products in DB: {Product.objects.count()}")
    
    # Scan all image files
    matched = []
    unmatched = []
    skipped = []
    duplicates = []
    
    for folder in sorted(PHOTOS_DIR.iterdir()):
        if not folder.is_dir():
            continue
        
        for img_file in sorted(folder.iterdir()):
            if not img_file.is_file():
                continue
            if img_file.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            if img_file.name.lower() in SKIP_FILENAMES:
                skipped.append(str(img_file))
                continue
            
            filename_stem = img_file.stem  # e.g. "EKO6010"
            folder_name = folder.name      # e.g. "009-010"
            
            product, variant, method = find_product_for_image(filename_stem, folder_name)
            
            if product is None:
                unmatched.append((str(img_file), filename_stem))
                continue
            
            # Check for existing media with same filename
            existing = Media.objects.filter(filename=img_file.name).first()
            if existing:
                # Check if already linked
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
    
    # Report
    print(f"\n=== SCAN RESULTS ===")
    print(f"Matched:    {len(matched)}")
    print(f"Unmatched:  {len(unmatched)}")
    print(f"Duplicates: {len(duplicates)}")
    print(f"Skipped:    {len(skipped)}")
    
    if unmatched:
        print(f"\n--- UNMATCHED FILES ---")
        for path, stem in unmatched:
            print(f"  {stem:30s}  ({path})")
    
    if matched:
        print(f"\n--- MATCHED FILES (first 20) ---")
        for m in matched[:20]:
            v_code = m["variant"].model_code if m["variant"] else "-"
            print(f"  {m['filename_stem']:20s} -> {m['product'].name:40s}  variant={v_code}  method={m['method']}")
    
    if dry_run:
        print(f"\n=== DRY RUN COMPLETE — no changes made ===")
        return
    
    # Import
    print(f"\n=== IMPORTING {len(matched)} IMAGES ===")
    created_count = 0
    error_count = 0
    
    for i, m in enumerate(matched):
        img_file = m["file"]
        product = m["product"]
        variant = m["variant"]
        
        try:
            # Read file
            file_bytes = img_file.read_bytes()
            content_type = mimetypes.guess_type(img_file.name)[0] or "image/png"
            
            # Get dimensions
            width, height = get_image_dimensions(img_file)
            
            # Check for duplicate by checksum
            checksum = hashlib.sha256(file_bytes).hexdigest()
            existing_media = Media.objects.filter(checksum_sha256=checksum).first()
            
            if existing_media:
                media = existing_media
                # Still link to product if not already linked
            else:
                # Create Media record
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
            
            # Check if already linked
            if not ProductMedia.objects.filter(product=product, media=media).exists():
                # Determine sort order
                max_order = ProductMedia.objects.filter(product=product).order_by("-sort_order").values_list("sort_order", flat=True).first()
                sort_order = (max_order or 0) + 1
                
                # Determine if this should be primary
                has_primary = ProductMedia.objects.filter(product=product, is_primary=True).exists()
                
                ProductMedia.objects.create(
                    product=product,
                    media=media,
                    variant=variant,
                    alt=product.title_tr or product.name,
                    sort_order=sort_order,
                    is_primary=not has_primary,  # Set as primary if none exists
                )
            
            created_count += 1
            if (i + 1) % 10 == 0:
                print(f"  Imported {i + 1}/{len(matched)}...")
        
        except Exception as e:
            error_count += 1
            print(f"  ERROR importing {img_file.name}: {e}")
    
    print(f"\n=== IMPORT COMPLETE ===")
    print(f"Successfully imported: {created_count}")
    print(f"Errors: {error_count}")
