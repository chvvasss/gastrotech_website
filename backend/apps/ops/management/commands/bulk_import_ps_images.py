"""
Django management command for bulk importing product images from Gastrotech PS folders.

This command imports images with format: {MODEL_CODE}_{TURKISH_NAME}.jpg
where the part before the first underscore is matched to Variant.model_code.

Run inside Docker:
    docker exec -it backend-web-1 python manage.py bulk_import_ps_images /path/to/images --commit

Usage:
    # Dry run (default)
    python manage.py bulk_import_ps_images /path/to/images --verbose

    # Actual import
    python manage.py bulk_import_ps_images /path/to/images --commit
"""
import os
import re
import hashlib
import logging
from io import BytesIO
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import Variant, Media, ProductMedia, Product


logger = logging.getLogger(__name__)

# TIF conversion requires PIL
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def compute_sha256(data: bytes) -> str:
    """Compute SHA256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()


def extract_model_code(filename: str) -> tuple[str, int]:
    """
    Extract model code and sort order from filename.
    
    Examples:
        217780_Kombi_Konveksiyonel_Firin_6xGN11.jpg -> ('217780', 0)
        206350_Alt_Stand_icin_Kapak_1.jpg -> ('206350', 1)
        STD7010_Alt_Stant_Kapaksiz.jpg -> ('STD7010', 0)
        VNN14_Kombinasyon_Sogutmali_Buzdolaplari.jpg -> ('VNN14', 0)
    """
    stem = Path(filename).stem
    parts = stem.split('_')
    
    if not parts:
        return stem, 0
    
    # First part is model code
    model_code = parts[0]
    
    # Check if last part is a number (sort order suffix)
    sort_order = 0
    if len(parts) > 1:
        last_part = parts[-1]
        if last_part.isdigit():
            sort_order = int(last_part)
    
    return model_code, sort_order


def convert_tif_to_jpg(file_path: str) -> tuple[bytes, str]:
    """
    Convert TIF/TIFF file to JPEG bytes.
    Returns (jpeg_bytes, new_filename).
    """
    if not HAS_PIL:
        raise ImportError("Pillow is required for TIF conversion: pip install Pillow")
    
    with Image.open(file_path) as img:
        # Convert to RGB if necessary (TIFF can be CMYK)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        elif img.mode == 'CMYK':
            img = img.convert('RGB')
        
        # Save as JPEG to bytes
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        jpeg_bytes = buffer.getvalue()
    
    # New filename
    old_stem = Path(file_path).stem
    new_filename = f"{old_stem}.jpg"
    
    return jpeg_bytes, new_filename


class Command(BaseCommand):
    help = 'Import product images from PS (Photoshop) folder, matching by variant model code'

    def add_arguments(self, parser):
        parser.add_argument(
            'directory',
            type=str,
            help='Directory containing image files to import'
        )
        parser.add_argument(
            '--commit',
            action='store_true',
            help='Actually commit changes to database (default is dry-run)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for all files'
        )
        parser.add_argument(
            '--skip-tif',
            action='store_true',
            help='Skip TIF/TIFF files instead of converting'
        )

    def handle(self, *args, **options):
        directory = options['directory']
        dry_run = not options['commit']
        verbose = options['verbose']
        skip_tif = options.get('skip_tif', False)
        
        if not os.path.isdir(directory):
            raise CommandError(f"Directory does not exist: {directory}")
        
        self.stdout.write(f"Scanning directory: {directory}")
        if dry_run:
            self.stdout.write(self.style.WARNING(
                "Running in DRY RUN mode. Use --commit to apply changes."
            ))
        
        # Statistics
        stats = {
            'processed': 0,
            'matched': 0,
            'created': 0,
            'already_linked': 0,
            'tif_converted': 0,
            'tif_skipped': 0,
        }
        unmatched_files = []
        matched_products = set()
        
        # Supported extensions
        image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff'}
        
        for file in os.listdir(directory):
            ext = Path(file).suffix.lower()
            if ext not in image_extensions:
                continue
            
            stats['processed'] += 1
            file_path = os.path.join(directory, file)
            
            # Extract sort order (last part if digit)
            stem = Path(file).stem
            parts = stem.split('_')
            sort_order = 0
            if len(parts) > 1 and parts[-1].isdigit():
                sort_order = int(parts[-1])
                parts = parts[:-1] # Remove sort order from parts for matching
            
            # Iterative matching: try progressively longer prefixes
            # Example: AC_177_Gurme -> tries "AC", then "AC 177", then "AC 177 Gurme"
            variant = None
            matched_code = ""
            
            # Try combining parts with spaces
            for i in range(1, len(parts) + 1):
                candidate_code = " ".join(parts[:i])
                v = Variant.objects.filter(
                    model_code__iexact=candidate_code
                ).select_related('product').first()
                
                if v:
                    variant = v
                    matched_code = candidate_code
                    # Don't break immediately? 
                    # Actually, usually the shortest match might be wrong if a longer one exists 
                    # (e.g. "PRO" vs "PRO MAX"). But typically model codes are distinct. 
                    # Let's assume we want the longest match? Or shortest?
                    # Given naming convention "CODE_Name_Name", likely the code is the first N parts.
                    # Safe to take the first valid match? 
                    # "AC" is a valid code? Probably not if "AC 177" is the target.
                    # But if "AC" exists as a product, and "AC 177" is another...
                    # Let's stick to "first match" for now, but usually exact match is best.
                    # However, since we are building from left, "AC" might not match "AC 177".
                    # If "AC" IS a variant, and filename is "AC_177_...", is it "AC" product variant named "177..."?
                    # Or "AC 177" product?
                    # Given the examples (AC 177), it's likely the code includes the space.
                    # Taking the *longest* valid match might be safer if collisions exist, but let's try first match.
                    break
            
            # Fallback: Try with underscores (matches original logic somewhat, but for multi-part)
            if not variant:
                 for i in range(1, len(parts) + 1):
                    candidate_code = "_".join(parts[:i])
                    v = Variant.objects.filter(
                        model_code__iexact=candidate_code
                    ).select_related('product').first()
                    if v:
                        variant = v
                        matched_code = candidate_code
                        break
            
            # Fallback 2: Name-based matching (Intelligent Fallback)
            # If still no variant, try to match Product by title using the rest of the filename
            product = None
            if variant:
                product = variant.product
                stats['matched'] += 1
                matched_products.add(str(product.id))
            else:
                 # Extract name part (everything after the first underscore usually, 
                 # or the pure filename if code lookup failed completely)
                 
                 # Construct potential name from parts[1:] if parts exist, else use stem
                 if len(parts) > 1:
                     # Try cleaning up the name part
                     name_query = " ".join(parts[1:]).replace('_', ' ').strip()
                 else:
                     name_query = stem.replace('_', ' ').strip()
                 
                 if len(name_query) > 3: # Only try if we have a decent string
                     # Strategy: check if Product.title_tr is contained in name_query
                     # OR if name_query is contained in Product.title_tr
                     
                     # 1. Try finding products whose title is inside the filename name part
                     # This helps when filename is detailed "X Y Z Feature" and product is "X Y"
                     # We favor the longest matching product title to avoid generic "Firin" matches
                     
                     # To avoid fetching all products, we might filter by words?
                     # Let's try a direct broader icontains search first
                     
                     # Check if we can find a product where the title matches the query closely
                     # Using filtered list might be slow.
                     # Let's search for products that have at least one word from the query?
                     # Safer: Try exact contains both ways
                     
                     p_match = Product.objects.filter(title_tr__iexact=name_query).first()
                     if not p_match:
                         p_match = Product.objects.filter(title_tr__icontains=name_query).first()
                     
                     if not p_match:
                         # Reverse: Filename contains Product Title
                         # Iterate all products? Too slow (1800 variants, maybe fewer products).
                         # Products count is roughly same order magnitude.
                         # Optimization: Filter by first word of name_query
                         first_word = name_query.split()[0]
                         if len(first_word) > 2:
                             candidates = Product.objects.filter(title_tr__icontains=first_word)
                             best_candidate = None
                             best_len = 0
                             for cand in candidates:
                                 if cand.title_tr.lower() in name_query.lower():
                                     # Pick the longest title match (most specific)
                                     if len(cand.title_tr) > best_len:
                                         best_len = len(cand.title_tr)
                                         best_candidate = cand
                             p_match = best_candidate

                     if p_match:
                         product = p_match
                         matched_products.add(str(product.id))
                         stats['matched'] += 1
                         if verbose:
                             self.stdout.write(f"[NAME MATCH] {file} -> Product: {product.title_tr}")
                         # Set variant to None, we work with Product directly
                         variant = None

            if not product and not variant:
                unmatched_files.append((file, parts[0])) # Log first part as guess
                if verbose:
                    self.stdout.write(f"[SKIP] {file} - No matching variant/product found")
                continue
            
            # If we matched via variant, product is already set above.
            # If we matched via name, product is set, variant is None.
            
            if matched_code and variant: # Stats for code match
                if verbose:
                    self.stdout.write(
                        f"[MATCH] {file} -> {matched_code} -> {product.title_tr}"
                    )
            
            # If name match, we already incremented stats['matched'] and printed verbose output
            
            if dry_run:
                continue
                
            # Process file
            try:
                # Handle TIF/TIFF conversion
                if ext in {'.tif', '.tiff'}:
                    if skip_tif:
                        stats['tif_skipped'] += 1
                        continue
                    
                    if not HAS_PIL:
                        self.stderr.write(
                            f"[SKIP] {file} - Pillow not installed for TIF conversion"
                        )
                        stats['tif_skipped'] += 1
                        continue
                    
                    content, new_filename = convert_tif_to_jpg(file_path)
                    content_type = "image/jpeg"
                    stats['tif_converted'] += 1
                    if verbose:
                        self.stdout.write(f"   Converted TIF -> {new_filename}")
                else:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    new_filename = file
                    content_type = f"image/{ext.lstrip('.')}"
                
                checksum = compute_sha256(content)
                
                # Get or create Media
                media = Media.objects.filter(checksum_sha256=checksum).first()
                if not media:
                    media = Media.objects.create(
                        kind=Media.Kind.IMAGE,
                        filename=new_filename,
                        content_type=content_type,
                        bytes=content,
                        size_bytes=len(content),
                        checksum_sha256=checksum
                    )
                    if verbose:
                        self.stdout.write(f"   Created new Media: {media.id}")
                else:
                    if verbose:
                        self.stdout.write(f"   Found existing Media: {media.id}")
                
                # Link to Product
                pm_exists = ProductMedia.objects.filter(
                    product=product, media=media
                ).exists()
                
                if not pm_exists:
                    has_primary = ProductMedia.objects.filter(
                        product=product, is_primary=True
                    ).exists()
                    is_primary = (not has_primary) and (sort_order == 0)
                    
                    ProductMedia.objects.create(
                        product=product,
                        media=media,
                        sort_order=sort_order,
                        is_primary=is_primary,
                        alt=f"{product.title_tr} - {variant.model_code}"
                    )
                    stats['created'] += 1
                    if verbose:
                        self.stdout.write(
                            f"   Linked to Product (Primary: {is_primary})"
                        )
                else:
                    stats['already_linked'] += 1
                    if verbose:
                        self.stdout.write("   Already linked.")
                
            except Exception as e:
                self.stderr.write(f"[ERROR] Failed to process {file}: {e}")
        
        # Summary
        self.stdout.write("-" * 60)
        self.stdout.write(self.style.SUCCESS("IMPORT SUMMARY"))
        self.stdout.write("-" * 60)
        self.stdout.write(f"Total Files Scanned: {stats['processed']}")
        self.stdout.write(f"Matched to Variants: {stats['matched']}")
        self.stdout.write(f"Unique Products: {len(matched_products)}")
        
        if not dry_run:
            self.stdout.write(f"Links Created: {stats['created']}")
            self.stdout.write(f"Already Linked: {stats['already_linked']}")
            if stats['tif_converted'] > 0:
                self.stdout.write(f"TIF Converted: {stats['tif_converted']}")
            if stats['tif_skipped'] > 0:
                self.stdout.write(f"TIF Skipped: {stats['tif_skipped']}")
        
        # Unmatched summary
        unmatched_count = len(unmatched_files)
        if unmatched_count > 0:
            self.stdout.write("-" * 60)
            self.stdout.write(self.style.WARNING(f"Unmatched Files: {unmatched_count}"))
            
            if verbose:
                for file, code in unmatched_files[:50]:
                    self.stdout.write(f"  {file} (code: {code})")
                if unmatched_count > 50:
                    self.stdout.write(f"  ... and {unmatched_count - 50} more")
            
            # Group unmatched by prefix for analysis
            prefixes = {}
            for file, code in unmatched_files:
                prefix = ''
                for c in code.lower():
                    if c.isalpha():
                        prefix += c
                    else:
                        break
                if prefix:
                    prefixes[prefix] = prefixes.get(prefix, 0) + 1
            
            if prefixes:
                self.stdout.write("\nUnmatched by prefix:")
                for prefix, count in sorted(prefixes.items(), key=lambda x: -x[1]):
                    self.stdout.write(f"  {prefix}: {count} files")
        
        # Final message
        self.stdout.write("-" * 60)
        match_rate = (stats['matched'] / stats['processed'] * 100) if stats['processed'] > 0 else 0
        self.stdout.write(self.style.SUCCESS(f"Match Rate: {match_rate:.1f}%"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                "\nThis was a DRY RUN. Use --commit to actually import images."
            ))
