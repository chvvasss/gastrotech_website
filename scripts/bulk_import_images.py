import os
import sys
import django
import hashlib
import logging
from pathlib import Path
from django.db import transaction

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import Variant, Media, ProductMedia

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
}

# Configuration
IMAGE_DIR = r"C:\gastrotech.com.tr.0101\gastrotech.com_cursor\fotolar1"
DRY_RUN = True  # Default to True for safety

# Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

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
    
    # Handle parens like "kwik (1)" -> "kwik" although not expected per user provided examples
    if '(' in base:
         base = base.split('(')[0]
         
    return base.strip()

def process_images(directory):
    count_processed = 0
    count_matched = 0
    count_created = 0

    logger.info(f"Scanning directory: {directory}")
    if DRY_RUN:
        logger.info("Running in DRY RUN mode. No database changes will be made.")

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                count_processed += 1
                file_path = os.path.join(root, file)
                model_code_input = get_model_code_from_filename(file)
                
                # Check suffix for sort order (naive approach)
                # gko7010.png -> order 0
                # gko7010_2.png -> order 1
                sort_order = 0
                stem = Path(file).stem
                if '_' in stem:
                    try:
                        suffix = stem.split('_')[-1]
                        if suffix.isdigit():
                            sort_order = int(suffix) - 1 # _2 -> 1
                            if sort_order < 0: sort_order = 1 # fallback
                    except ValueError:
                        pass

                # Find Variant - first try direct match, then smart mapping
                try:
                    variant = Variant.objects.filter(model_code__iexact=model_code_input).select_related('product').first()
                    
                    # If no direct match, try smart mapping
                    if not variant:
                        mapped_code = SMART_MAPPINGS.get(model_code_input.lower())
                        if mapped_code:
                            variant = Variant.objects.filter(model_code__iexact=mapped_code).select_related('product').first()
                            if variant:
                                logger.info(f"[SMART MAP] {model_code_input} -> {mapped_code}")
                except Exception as e:
                    logger.error(f"Error querying variant for {model_code_input}: {e}")
                    continue

                if not variant:
                    # logger.warning(f"No match found for file: {file} (Model Code: {model_code_input})")
                    continue
                
                count_matched += 1
                product = variant.product
                
                logger.info(f"[MATCH] File: {file} -> Variant: {variant.model_code} -> Product: {product.name}")

                if DRY_RUN:
                    continue

                # Process File
                try:
                    file_size = os.path.getsize(file_path)
                    checksum = compute_sha256(file_path)
                    
                    # 1. Get or Create Media
                    media = Media.objects.filter(checksum_sha256=checksum).first()
                    if not media:
                        with open(file_path, 'rb') as f:
                            content = f.read()
                        
                        media = Media.objects.create(
                            kind=Media.Kind.IMAGE,
                            filename=file,
                            content_type=f"image/{Path(file).suffix.lstrip('.')}", # simplistic
                            bytes=content,
                            size_bytes=len(content), # Let the model handle this ideally, but passing explicit checks
                            checksum_sha256=checksum # Let model handle? Model computes in save() if bytes provided
                        )
                        logger.info(f"   Created new Media: {media.id}")
                    else:
                        logger.info(f"   Found existing Media: {media.id}")

                    # 2. Link to Product
                    # Check if this exact linkage exists
                    pm_exists = ProductMedia.objects.filter(product=product, media=media).exists()
                    if not pm_exists:
                        # Determine primary status
                        # If product has no images, make this primary if sort_order is 0
                        has_primary = ProductMedia.objects.filter(product=product, is_primary=True).exists()
                        is_primary = (not has_primary) and (sort_order == 0)

                        ProductMedia.objects.create(
                            product=product,
                            media=media,
                            sort_order=sort_order,
                            is_primary=is_primary,
                            alt=f"{product.name} - {variant.model_code}"
                        )
                        logger.info(f"   Linked to Product: {product.id} (Primary: {is_primary})")
                        count_created += 1
                    else:
                        logger.info("   Already linked.")

                except Exception as e:
                    logger.error(f"Failed to process file {file}: {e}")

    logger.info("-" * 30)
    logger.info(f"Total Files Scanned: {count_processed}")
    logger.info(f"Total Matches Found: {count_matched}")
    if not DRY_RUN:
        logger.info(f"Total Links Created: {count_created}")

if __name__ == "__main__":
    # Check for --commit arg
    if "--commit" in sys.argv:
        DRY_RUN = False
    
    process_images(IMAGE_DIR)
