"""
Reload media bytes from local image directory into existing Media records.

Matches files by filename and updates the bytes column.
Run from host (not Docker) since it needs the local filesystem.
"""

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ["DATABASE_URL"] = "postgres://postgres:postgres@localhost:5432/gastrotech"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from apps.catalog.models import Media, Product, Brand

# Directory Configuration
MUTAS_DIR = Path(r"D:\mutaş fotolar (1)")
FOTOLAR_DIR = Path(r"C:\Users\emir\Desktop\Fotolar")
PROJECT_PDF_DIR = Path(r"C:\Users\emir\Desktop\gastrotech_website-main\backend\fixtures\catalog_pdfs")
PROJECT_CATALOG_DIR = Path(r"C:\Users\emir\Desktop\gastrotech_website-main\frontend\public\catalogs")

IMAGE_DIRS = [
    MUTAS_DIR,
    FOTOLAR_DIR,
    PROJECT_PDF_DIR,
    PROJECT_CATALOG_DIR,
]

def normalize_filename_candidates(fn):
    """
    Generate candidate filenames to check on disk.
    1. Exact match
    2. Strip "N-" prefix (e.g., '7-VBY1500L.png' -> 'VBY1500L.png')
    """
    candidates = [fn]
    if '-' in fn:
        parts = fn.split('-', 1)
        if parts[0].isdigit():
            # e.g., "7-VBY1500L.png" -> "VBY1500L.png"
            candidates.append(parts[1])
    return candidates

def update_product_brand_to_vital(media_obj):
    """
    If media comes from Mutas folder, update associated products' brand to VITAL.
    """
    # Find all products ensuring this media is used (via ProductMedia or cover_media etc if applicable)
    # The primary join is usually Product -> ProductMedia -> Media
    # Check ProductMedia (related_name="media_products" from models.py)
    p_medias = media_obj.media_products.all()
    
    if not p_medias.exists():
        return
        
    vital_brand, _ = Brand.objects.get_or_create(name="VITAL", defaults={"slug": "vital"})
    
    count = 0
    for pm in p_medias:
        product = pm.product
        if product.brand != vital_brand:
            product.brand = vital_brand
            product.save(update_fields=["brand", "updated_at"])
            count += 1
            
    if count > 0:
        print(f"  -> Updated {count} product(s) to brand 'VITAL' for {media_obj.filename}")

def run():
    print("=== Reload Media Bytes (v4 - Case Insensitive) ===\n")
    
    # scan for files first
    print(f"Scanning directories...")
    file_map = {} # lowercase filename -> Path
    
    # Priority: We want to know SPECIFICALLY if it came from Mutas for the brand logic.
    # So we'll scan Mutas FIRST, then others. If duplicates exist, we might overwrite, 
    # but let's store source info.
    
    # We'll use a specific lookup for Mutas to trigger the brand update
    files_in_mutas = set() # lowercase filenames
    
    total_found = 0
    for d in IMAGE_DIRS:
        if not d.exists():
            print(f"[WARN] Directory not found: {d}")
            continue
            
        print(f"  Scanning {d}...")
        for f in d.rglob("*"):
            if f.is_file(): 
                key = f.name.lower()
                file_map[key] = f
                if d == MUTAS_DIR:
                    files_in_mutas.add(key)
                total_found += 1
                
    print(f"Total files indexed: {total_found} (Unique names: {len(file_map)})")

    # Get empty media - OR ALL MEDIA if we want to update brands even for existing bytes
    # The user instruction was "ALL IMAGE PRODUCTS TAKEN FROM THIS MUTAS FOLDER MUST BE BRAND VITAL"
    # So we should probably check ALL media that matches filenames in Mutas, not just empty ones.
    # But for now, focus on restoration. Let's check empty first.
    
    # Wait, if we want to update brand for ALREADY restored files, we need to check all media against Mutas list.
    # Let's do restoration for empty ones, AND brand update for ALL matching Mutas files.
    
    # Get all media records - usage of iterator and defer to avoid MemoryError
    # We use size_bytes to check if it's empty, instead of loading the bytes field.
    all_media = Media.objects.all().defer("bytes").iterator(chunk_size=100)
    total_count = Media.objects.count()
    print(f"Total media records: {total_count}")
    
    matched_restore = 0
    updated_brands = 0
    processed = 0
    
    for media_obj in all_media:
        processed += 1
        db_filename = media_obj.filename
        candidates = normalize_filename_candidates(db_filename)
        
        found_path = None
        found_key = None
        
        for cand in candidates:
            key = cand.lower()
            if key in file_map:
                found_path = file_map[key]
                found_key = key
                break
        
        # 1. Restore bytes if missing (check size_bytes to avoid loading bytes)
        # If size_bytes is None or 0, we assume it's empty.
        if (not media_obj.size_bytes) and found_path:
            try:
                with open(found_path, "rb") as f:
                    content = f.read()
                
                media_obj.bytes = content
                media_obj.size_bytes = len(content)
                media_obj.save(update_fields=["bytes", "size_bytes", "checksum_sha256", "updated_at"])
                matched_restore += 1
                if matched_restore % 50 == 0:
                    print(f"  ... reloaded bytes for {matched_restore}")
            except Exception as e:
                print(f"[ERROR] Failed to load {db_filename} from {found_path}: {e}")
        
        # 2. Update Brand if from Mutas (check normalized key against Mutas set)
        if found_key and found_key in files_in_mutas:
             # This checks if the file exists in Mutas folder (by name match)
             if update_product_brand_to_vital(media_obj):
                 updated_brands += 1
        
        if processed % 100 == 0:
             print(f"  Processed {processed}/{total_count} records...")

    print(f"\n=== Summary ===")
    print(f"Restored Bytes: {matched_restore}")
    print(f"Updated Brands: {updated_brands}")
    
    # helper for update_product_brand_to_vital to return bool
    
def update_product_brand_to_vital(media_obj):
    """
    If media comes from Mutas folder, update associated products' brand to VITAL.
    Returns True if any update occurred.
    """
    # Use media_products related name
    p_medias = media_obj.media_products.select_related('product').all()
    
    if not p_medias.exists():
        return False
        
    vital_brand, _ = Brand.objects.get_or_create(name="VITAL", defaults={"slug": "vital"})
    
    count = 0
    for pm in p_medias:
        product = pm.product
        if product.brand_id != vital_brand.id:
            product.brand = vital_brand
            product.save(update_fields=["brand", "updated_at"])
            count += 1
            
    if count > 0:
        # print(f"  -> Updated {count} product(s) to brand 'VITAL' for {media_obj.filename}")
        return True
    return False

if __name__ == "__main__":
    run()

if __name__ == "__main__":
    run()
