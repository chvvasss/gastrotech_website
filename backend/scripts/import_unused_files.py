import os
import sys
from pathlib import Path
from django.db.models import Max

sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ["DATABASE_URL"] = "postgres://postgres:postgres@localhost:5432/gastrotech"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from apps.catalog.models import Media, Product, Variant, ProductMedia, Brand

MUTAS_DIR = Path(r"D:\mutaş fotolar (1)")
FOTOLAR_DIR = Path(r"C:\Users\emir\Desktop\Fotolar")

IMAGE_DIRS = [
    MUTAS_DIR,
    FOTOLAR_DIR,
]

def normalize_filename_for_matching(fn):
    """
    Return list of possible 'keys' to match against products using the filename.
    """
    stem = Path(fn).stem 
    candidates = set()
    candidates.add(stem.lower())
    
    # Strip Prefix (N-)
    if '-' in stem:
        parts = stem.split('-', 1)
        if parts[0].isdigit():
            candidates.add(parts[1].lower())
            
    # Strip Suffix (_2, _3)
    base_candidates = list(candidates)
    for c in base_candidates:
        if '_' in c:
            base, suffix = c.rsplit('_', 1)
            candidates.add(base)
            
    return candidates

def run():
    print("=== Importing Unused Files ===\n")
    
    # 1. Get all known Media filenames
    known_media_files = set(Media.objects.values_list('filename', flat=True))
    known_media_files_lower = {f.lower() for f in known_media_files}
    
    # 2. Scan disks
    found_files = {} # path -> filename
    files_in_mutas = set()
    
    for d in IMAGE_DIRS:
        if not d.exists(): continue
        print(f"Scanning {d}...")
        for f in d.rglob("*"):
            if f.is_file() and f.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}:
                found_files[f] = f.name
                if d == MUTAS_DIR:
                    files_in_mutas.add(f) # Store full path to check against later
                
    # 3. Identify Unused
    unused_files = []
    
    for fpath, fname in found_files.items():
        if fname.lower() in known_media_files_lower:
            continue
            
        candidates = []
        if '-' in fname:
            parts = fname.split('-', 1)
            if parts[0].isdigit():
                candidates.append(parts[1].lower())
                
        is_known = False
        for c in candidates:
             if c in known_media_files_lower:
                 is_known = True
                 break
        
        if is_known:
            continue
            
        unused_files.append((fpath, fname))

    print(f"Total Unused files: {len(unused_files)}")
    
    # 4. Attempt to match Unused to Products
    print("MATCHING...")
    products = Product.objects.values('id', 'slug', 'name')
    variants = Variant.objects.values('id', 'model_code', 'product_id')
    
    prod_lookup = {} 
    for p in products:
        prod_lookup[p['slug'].lower()] = p['id']
    for v in variants:
        if v['model_code']:
            prod_lookup[v['model_code'].lower()] = v['product_id']

    matches_found = []
    
    for fpath, fname in unused_files:
        candidates = normalize_filename_for_matching(fname)
        matched_pid = None
        
        for c in candidates:
            if c in prod_lookup:
                matched_pid = prod_lookup[c]
                break
        
        if matched_pid:
            matches_found.append({
                'file': fpath,
                'filename': fname,
                'product_id': matched_pid
            })
            
    print(f"Matches found to handle: {len(matches_found)}")
    
    if not matches_found:
        print("No matches to import.")
        return

    # 5. Import Matches
    vital_brand, _ = Brand.objects.get_or_create(name="VITAL", defaults={"slug": "vital"})
    
    imported_count = 0
    brand_updated_count = 0
    
    for m in matches_found:
        fpath = m['file']
        fname = m['filename']
        pid = m['product_id']
        
        try:
            # Create Media
            with open(fpath, "rb") as f:
                content = f.read()
                
            media = Media.objects.create(
                kind=Media.Kind.IMAGE,
                filename=fname,
                content_type="image/png" if fname.lower().endswith(".png") else "image/jpeg",
                bytes=content,
                size_bytes=len(content)
            )
            
            # Determine sort order
            max_order = ProductMedia.objects.filter(product_id=pid).aggregate(Max('sort_order'))['sort_order__max']
            new_order = (max_order or 0) + 1
            
            # Create ProductMedia
            ProductMedia.objects.create(
                product_id=pid,
                media=media,
                sort_order=new_order,
                is_primary=False # Always false for now, let user set primary manually if needed, or if it's the ONLY one?
            )
            
            # Brand Update Logic
            # Check if source file was in Mutas (we tracked paths in loop)
            # Actually we can just check if fpath starts with MUTAS_DIR
            # But MUTAS_DIR might be relative or differently cased.
            # Simple check:
            if str(MUTAS_DIR) in str(fpath):
                product = Product.objects.get(id=pid)
                if product.brand_id != vital_brand.id:
                    product.brand = vital_brand
                    product.save(update_fields=['brand', 'updated_at'])
                    brand_updated_count += 1
            
            imported_count += 1
            print(f"Imported {fname} -> Product {pid}")
            
        except Exception as e:
            print(f"[ERROR] Failed to import {fname}: {e}")
            
    print(f"\n=== Import Summary ===")
    print(f"Imported New Media: {imported_count}")
    print(f"Updated Brands to VITAL: {brand_updated_count}")
    
if __name__ == "__main__":
    run()
