import os
import sys
from pathlib import Path
from django.db.models import Q

sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ["DATABASE_URL"] = "postgres://postgres:postgres@localhost:5432/gastrotech"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from apps.catalog.models import Media, Product, Variant

IMAGE_DIRS = [
    Path(r"D:\mutaş fotolar (1)"),
    Path(r"C:\Users\emir\Desktop\Fotolar"),
]

def normalize_filename_for_matching(fn):
    """
    Return list of possible 'keys' to match against products using the filename.
    e.g. 
    '7-VBY1500L.png' -> matches Product 'VBY1500L'
    'VBY1500L_2.png' -> matches Product 'VBY1500L'
    """
    # Remove extension
    stem = Path(fn).stem # 7-VBY1500L
    
    candidates = set()
    candidates.add(stem.lower())
    
    # Strip Prefix (N-)
    if '-' in stem:
        parts = stem.split('-', 1)
        if parts[0].isdigit():
            candidates.add(parts[1].lower()) # VBY1500L
            
    # Strip Suffix (_2, _3) - usually variation images
    # We want to match them to the MAIN product
    # e.g. VBY1500L_2 -> VBY1500L
    
    # We process the candidates generated so far
    base_candidates = list(candidates)
    for c in base_candidates:
        if '_' in c:
            # check for _digit suffix or just _something
            base, suffix = c.rsplit('_', 1)
            # if suffix.isdigit() or len(suffix) < 5: # heuristic
            candidates.add(base)
            
    return candidates

def run():
    print("=== Analyzing Unused Files ===\n")
    
    # 1. Get all known Media filenames
    # We use a set of lower-case filenames for case-insensitive check
    known_media_files = set(Media.objects.values_list('filename', flat=True))
    known_media_files_lower = {f.lower() for f in known_media_files}
    
    print(f"Known Media in DB: {len(known_media_files)}")
    
    # 2. Scan disks
    found_files = {} # path -> filename
    
    for d in IMAGE_DIRS:
        if not d.exists(): continue
        print(f"Scanning {d}...")
        for f in d.rglob("*"):
            if f.is_file() and f.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}:
                found_files[f] = f.name
                
    print(f"Total files on disk: {len(found_files)}")
    
    # 3. Identify Unused
    unused_files = []
    processed_count = 0
    
    for fpath, fname in found_files.items():
        # Check if matched in DB (handling prefix/suffix normalization is ALREADY done by the previous script? 
        # No, previous script used normalization to LOOKUP the file for a DB record.
        # Here we do the reverse: Does this file correspond to ANY DB record?)
        
        # We need to be careful. If DB has "7-VBY.png" and file is "7-VBY.png", it's a match.
        # If DB has "VBY.png" and file is "7-VBY.png", it WAS matched by the script.
        
        # To be precise: strict match first
        if fname.lower() in known_media_files_lower:
            continue
            
        # Check normalized version (strip prefix) against DB
        # e.g. file 7-VBY.png -> VBY.png
        # Does DB have VBY.png?
        
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
            
        # truly unused
        unused_files.append((fpath, fname))

    print(f"Unused files (not linked to any Media record): {len(unused_files)}")
    
    # 4. Attempt to match Unused to Products
    # We load all Product slugs/model codes
    print("Loading Product info...")
    products = Product.objects.values('id', 'slug', 'name')
    variants = Variant.objects.values('id', 'model_code', 'product_id')
    
    # Build lookups
    prod_lookup = {} # slug/code -> product_id
    for p in products:
        prod_lookup[p['slug'].lower()] = p['id']
        # Maybe use name? no, name is descriptive
        
    for v in variants:
        if v['model_code']:
            prod_lookup[v['model_code'].lower()] = v['product_id']

    matches_found = []
    
    print("Matching unused files to Products...")
    for fpath, fname in unused_files:
        # Generate candidates: "7-VBY_2.png" -> ["vby_2", "vby"]
        candidates = normalize_filename_for_matching(fname)
        
        matched_pid = None
        matched_str = None
        
        for c in candidates:
            if c in prod_lookup:
                matched_pid = prod_lookup[c]
                matched_str = c
                break
        
        if matched_pid:
            matches_found.append({
                'file': fpath,
                'match': matched_str,
                'product_id': matched_pid
            })
            
    print(f"\nResults:")
    print(f"Total Unused: {len(unused_files)}")
    print(f"  -> Match Existing Products: {len(matches_found)}")
    print(f"  -> No Match: {len(unused_files) - len(matches_found)}")
    
    if matches_found:
        print("\nSample Matches:")
        for m in matches_found[:10]:
            print(f"  {m['file'].name} -> Product Match: '{m['match']}'")

if __name__ == "__main__":
    run()
