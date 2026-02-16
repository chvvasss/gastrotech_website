# Analyze unmatched files and products on same pages to find linkable matches
import os, sys, re
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from apps.catalog.models import Product, Variant

FOTOLAR_DIR = Path(r"C:\Users\emir\Desktop\Fotolar")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SKIP_FILENAMES = {"liste.png", "liste.jpg"}

# Build variant lookup
variant_codes = set()
for v in Variant.objects.values_list("model_code", flat=True):
    if v:
        variant_codes.add(v.lower().strip())

# Build page_map
page_map = {}
for p in Product.objects.exclude(pdf_ref__isnull=True).exclude(pdf_ref="").values("id", "pdf_ref", "name"):
    ref = p["pdf_ref"].strip().lower()
    m = re.match(r"^p?0*(\d+)$", ref)
    if m:
        page_num = int(m.group(1))
        if page_num not in page_map:
            page_map[page_num] = []
        page_map[page_num].append(p)

# Get existing media
from apps.catalog.models import Media
existing_filenames_lower = {f.lower() for f in Media.objects.values_list("filename", flat=True)}

# Gather unmatched
unmatched_by_folder = {}
for folder in sorted(FOTOLAR_DIR.iterdir()):
    if not folder.is_dir():
        continue
    for img_file in sorted(folder.iterdir()):
        if not img_file.is_file():
            continue
        if img_file.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if img_file.name.lower() in SKIP_FILENAMES:
            continue
        if img_file.name.lower() in existing_filenames_lower:
            continue
        
        stem = img_file.stem.lower().strip()
        # Check variant match
        if stem in variant_codes:
            continue
        # Check normalized
        normalized = re.sub(r"[\s_-]+", "", stem)
        found = False
        for vc in variant_codes:
            if re.sub(r"[\s_-]+", "", vc) == normalized:
                found = True
                break
        if found:
            continue
        
        # Still unmatched
        fn = folder.name
        if fn not in unmatched_by_folder:
            unmatched_by_folder[fn] = []
        unmatched_by_folder[fn].append(img_file.name)

# Report by folder with products on those pages
print(f"{'='*80}")
print(f"UNMATCHED FILES ANALYSIS (by folder/page)")
print(f"{'='*80}")

total_unmatched = 0
for folder_name in sorted(unmatched_by_folder.keys()):
    files = unmatched_by_folder[folder_name]
    total_unmatched += len(files)
    
    # Get pages
    parts = re.split(r"[-.]", folder_name)
    pages = [int(p.strip()) for p in parts if p.strip().isdigit()]
    
    # Get products on those pages
    products_on_page = []
    for pg in pages:
        if pg in page_map:
            products_on_page.extend(page_map[pg])
    
    # Get all variants for those products
    product_ids = [p["id"] for p in products_on_page]
    variants_on_page = list(
        Variant.objects.filter(product_id__in=product_ids).values("model_code", "product__name")
    )
    
    print(f"\n--- Folder: {folder_name} (pages {pages}) ---")
    print(f"  Files ({len(files)}):")
    for f in files:
        print(f"    {f}")
    
    if products_on_page:
        print(f"  Products on page ({len(products_on_page)}):")
        for p in products_on_page:
            print(f"    [{p['id']}] {p['name']}")
        if variants_on_page:
            print(f"  Variants:")
            for v in variants_on_page[:20]:
                print(f"    {v['model_code']} -> {v['product__name']}")
    else:
        print(f"  No products found for pages {pages}")

print(f"\nTotal unmatched: {total_unmatched}")
