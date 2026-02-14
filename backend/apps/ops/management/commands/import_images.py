"""
Django management command for importing product images.
Run inside Docker: docker exec -it backend-web-1 python manage.py import_images /path/to/images
"""
import os
import hashlib
import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Variant, Media, ProductMedia


logger = logging.getLogger(__name__)


# Smart Mappings: File prefix -> DB model_code
# These handle cases where file naming conventions differ from DB conventions
SMART_MAPPINGS = {
    # GPI (file) → GPT (db) for 700 series (Gazlı Pleyt Izgara)
    'gpi7010r': 'GPT7010R',
    'gpi7010s': 'GPT7010S',
    'gpi7020r': 'GPT7020R',
    'gpi7020s': 'GPT7020S',
    'gpi7020sr': 'GPT7020SR',
    'gpi7030r': 'GPT7030R',
    'gpi7030s': 'GPT7030S',
    'gpi7030sr': 'GPT7030SR',
    
    # GPI (file) → GP1 (db) for 900 series
    'gpi9010r': 'GP19010R',
    'gpi9010s': 'GP19010S',
    'gpi9020r': 'GP19020R',
    'gpi9020s': 'GP19020S',
    'gpi9020sr': 'GP19020SR',
    'gpi9030r': 'GP19030R',
    'gpi9030s': 'GP19030S',
    'gpi9030sr': 'GP19030SR',
    
    # GPI (file) → GP1 (db) for 600 series
    'gpi6010r': 'GP16010R',
    'gpi6010s': 'GP16010S',
    'gpi6020r': 'GP16020R',
    'gpi6020s': 'GP16020S',
    'gpi6020sr': 'GP16020SR',
    'gpi6030r': 'GP16030R',
    'gpi6030s': 'GP16030S',
    'gpi6030sr': 'GP16030SR',
    
    # VBY files -> VBY500C/D variants (Bulaşık Makineleri)
    'vby500': 'VBY500C',
    'vby500d': 'VBY500D',
    
    # ECO variants often have matching non-ECO versions
    # These will be handled by fuzzy matching below
}


def try_fuzzy_match(model_code_input, Variant):
    """
    Try various fuzzy matching strategies if direct match fails.
    Returns matched variant or None.
    """
    code = model_code_input.lower()
    
    # Fuzzy matching disabled due to high error rate (mismatched products)
    return None, None
    
    # Original logic commented out for reference:
    # # Strategy 1: Try without 'eco' suffix (gkf100eco -> gkf100)
    # if code.endswith('eco'):
    # ...
    
    # Strategy 2: Try adding 'eco' suffix (gkf100 -> gkf100eco might exist)
    if not code.endswith('eco'):
        v = Variant.objects.filter(model_code__iexact=code + 'eco').select_related('product').first()
        if v:
            return v, f"{code} -> {code}eco (added 'eco')"
    
    # Strategy 3: Case variations and common typos
    # Try uppercase
    v = Variant.objects.filter(model_code__iexact=code.upper()).select_related('product').first()
    if v:
        return v, f"{code} -> {code.upper()} (uppercase)"
    
    # Strategy 4: For VBY, try with suffix C/D
    if code.startswith('vby') and not code.endswith(('c', 'd')):
        for suffix in ['C', 'D']:
            v = Variant.objects.filter(model_code__iexact=code + suffix).select_related('product').first()
            if v:
                return v, f"{code} -> {code}{suffix} (added suffix)"
    
    # Strategy 5: For EKT/GKT/EDT/GDT patterns with dashes
    if '-' in code:
        # ekt400-500 -> try EKT400 or EKT500
        clean = code.replace('-', '')
        v = Variant.objects.filter(model_code__iexact=clean).select_related('product').first()
        if v:
            return v, f"{code} -> {clean} (removed dash)"
    
    return None, None



def compute_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_model_code_from_filename(filename):
    """
    Extracts model code from filename.
    Examples:
        gko7010.png -> gko7010
        gko7010_2.png -> gko7010
        gko7010 (2).png -> gko7010
    """
    stem = Path(filename).stem
    # Remove _ digit suffixes
    parts = stem.split('_')
    base = parts[0]
    
    # Handle parens like "kwik (1)" -> "kwik"
    if '(' in base:
        base = base.split('(')[0]
        
    return base.strip()


class Command(BaseCommand):
    help = 'Import product images from a directory, matching by variant model code'

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
            help='Show detailed output for unmatched files'
        )

    def handle(self, *args, **options):
        directory = options['directory']
        dry_run = not options['commit']
        verbose = options['verbose']
        
        if not os.path.isdir(directory):
            raise CommandError(f"Directory does not exist: {directory}")
        
        self.stdout.write(f"Scanning directory: {directory}")
        if dry_run:
            self.stdout.write(self.style.WARNING("Running in DRY RUN mode. Use --commit to apply changes."))
        
        count_processed = 0
        count_matched = 0
        count_created = 0
        unmatched_files = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    count_processed += 1
                    file_path = os.path.join(root, file)
                    model_code_input = get_model_code_from_filename(file)
                    
                    # Determine sort order from filename
                    sort_order = 0
                    stem = Path(file).stem
                    if '_' in stem:
                        try:
                            suffix = stem.split('_')[-1]
                            if suffix.isdigit():
                                sort_order = int(suffix) - 1
                                if sort_order < 0:
                                    sort_order = 1
                        except ValueError:
                            pass
                    
                    # Find variant - first try direct match, then smart mapping, then fuzzy
                    variant = None
                    try:
                        variant = Variant.objects.filter(
                            model_code__iexact=model_code_input
                        ).select_related('product').first()
                        
                        # If no direct match, try smart mapping
                        if not variant:
                            mapped_code = SMART_MAPPINGS.get(model_code_input.lower())
                            if mapped_code:
                                variant = Variant.objects.filter(
                                    model_code__iexact=mapped_code
                                ).select_related('product').first()
                                if variant:
                                    self.stdout.write(
                                        self.style.SUCCESS(f"[SMART MAP] {model_code_input} -> {mapped_code}")
                                    )
                        
                        # If still no match, try fuzzy matching
                        if not variant:
                            variant, match_reason = try_fuzzy_match(model_code_input, Variant)
                            if variant and match_reason:
                                self.stdout.write(
                                    self.style.SUCCESS(f"[FUZZY] {match_reason}")
                                )
                    except Exception as e:
                        self.stderr.write(f"Error querying variant for {model_code_input}: {e}")
                        continue
                    
                    if not variant:
                        unmatched_files.append((file, model_code_input))
                        continue
                    
                    count_matched += 1
                    product = variant.product
                    
                    self.stdout.write(
                        f"[MATCH] {file} -> {variant.model_code} -> {product.name}"
                    )
                    
                    if dry_run:
                        continue
                    
                    # Process file
                    try:
                        checksum = compute_sha256(file_path)
                        
                        # Get or create Media
                        media = Media.objects.filter(checksum_sha256=checksum).first()
                        if not media:
                            with open(file_path, 'rb') as f:
                                content = f.read()
                            
                            media = Media.objects.create(
                                kind=Media.Kind.IMAGE,
                                filename=file,
                                content_type=f"image/{Path(file).suffix.lstrip('.')}",
                                bytes=content,
                                size_bytes=len(content),
                                checksum_sha256=checksum
                            )
                            self.stdout.write(f"   Created new Media: {media.id}")
                        else:
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
                                alt=f"{product.name} - {variant.model_code}"
                            )
                            self.stdout.write(
                                f"   Linked to Product: {product.id} (Primary: {is_primary})"
                            )
                            count_created += 1
                        else:
                            self.stdout.write("   Already linked.")
                    
                    except Exception as e:
                        self.stderr.write(f"Failed to process {file}: {e}")
        
        # Summary
        self.stdout.write("-" * 50)
        self.stdout.write(f"Total Files Scanned: {count_processed}")
        self.stdout.write(f"Total Matches Found: {count_matched}")
        
        if not dry_run:
            self.stdout.write(f"Total Links Created: {count_created}")
        
        if unmatched_files and verbose:
            self.stdout.write("-" * 50)
            self.stdout.write(self.style.WARNING(f"Unmatched Files ({len(unmatched_files)}):"))
            for file, code in unmatched_files[:50]:
                self.stdout.write(f"  {file} (code: {code})")
            if len(unmatched_files) > 50:
                self.stdout.write(f"  ... and {len(unmatched_files) - 50} more")
        
        # Group unmatched by prefix for analysis
        if unmatched_files:
            self.stdout.write("-" * 50)
            prefixes = {}
            for file, code in unmatched_files:
                # Extract prefix (letters before numbers)
                prefix = ''
                for c in code.lower():
                    if c.isalpha():
                        prefix += c
                    else:
                        break
                if prefix:
                    prefixes[prefix] = prefixes.get(prefix, 0) + 1
            
            self.stdout.write(self.style.WARNING("Unmatched file prefixes:"))
            for prefix, count in sorted(prefixes.items(), key=lambda x: -x[1]):
                self.stdout.write(f"  {prefix}: {count} files")
