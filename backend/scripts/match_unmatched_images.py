# Match unmatched images by analyzing folder page ranges vs product pdf_ref,
# product names, and variant model codes with fuzzy/partial strategies.

import os
import sys
import hashlib
import mimetypes
import re
from pathlib import Path
from difflib import SequenceMatcher

sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from django.db.models import Max
from apps.catalog.models import Media, Product, ProductMedia, Variant

FOTOLAR_DIR = Path(r"C:\Users\emir\Desktop\Fotolar")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SKIP_FILENAMES = {"liste.png", "liste.jpg"}


def get_image_dimensions(filepath):
    try:
        from PIL import Image as PILImage
        with PILImage.open(filepath) as img:
            return img.width, img.height
    except Exception:
        return None, None


def build_page_to_products():
    """Build a map from page numbers to products using pdf_ref."""
    page_map = {}  # page_number -> [product_ids]
    for p in Product.objects.exclude(pdf_ref__isnull=True).exclude(pdf_ref="").values("id", "pdf_ref", "name"):
        ref = p["pdf_ref"].strip().lower()
        # Extract page number from pdf_ref like "p43", "43", "p043"
        m = re.match(r"^p?0*(\d+)$", ref)
        if m:
            page_num = int(m.group(1))
            if page_num not in page_map:
                page_map[page_num] = []
            page_map[page_num].append({"id": p["id"], "name": p["name"]})
    return page_map


def get_pages_from_folder(folder_name):
    """Extract page numbers from folder name like '009-010' or '207.208'."""
    parts = re.split(r"[-.]", folder_name)
    pages = []
    for part in parts:
        part = part.strip()
        if part.isdigit():
            pages.append(int(part))
    return pages


def find_best_product_for_file(filename_stem, folder_name, page_map, variant_lookup, product_name_lookup):
    """Try all strategies to find a matching product."""
    stem_lower = filename_stem.lower().strip()
    
    # 1. Direct variant lookup
    if stem_lower in variant_lookup:
        v = variant_lookup[stem_lower]
        return v["product_id"], v.get("variant_id"), "variant_exact"
    
    # 2. Variant with spaces/dashes normalized
    normalized = re.sub(r"[\s_-]+", "", stem_lower)
    for code, v in variant_lookup.items():
        code_norm = re.sub(r"[\s_-]+", "", code)
        if code_norm == normalized:
            return v["product_id"], v.get("variant_id"), "variant_normalized"
    
    # 3. Product name contains or matches the stem
    if stem_lower in product_name_lookup:
        return product_name_lookup[stem_lower], None, "name_exact"
    
    # 4. Fuzzy name match (stem is part of product name or vice versa)
    for pname, pid in product_name_lookup.items():
        if len(stem_lower) >= 4 and (stem_lower in pname or pname in stem_lower):
            return pid, None, "name_partial"
    
    # 5. Page-based matching: if folder maps to specific pages, 
    #    and there's a single product on that page spread
    folder_pages = get_pages_from_folder(folder_name)
    candidate_products = set()
    for page in folder_pages:
        if page in page_map:
            for prod_info in page_map[page]:
                candidate_products.add((prod_info["id"], prod_info["name"]))
    
    if len(candidate_products) == 1:
        pid, pname = list(candidate_products)[0]
        return pid, None, f"page_single({folder_name})"
    
    # If multiple products on the page, try fuzzy matching stem against product names
    if candidate_products:
        best_ratio = 0
        best_pid = None
        for pid, pname in candidate_products:
            ratio = SequenceMatcher(None, stem_lower, pname.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_pid = pid
        if best_ratio >= 0.4:
            return best_pid, None, f"page_fuzzy({best_ratio:.2f})"
    
    # 6. Sequence matcher against all product names
    best_ratio = 0
    best_pid = None
    for pname, pid in product_name_lookup.items():
        ratio = SequenceMatcher(None, stem_lower, pname).ratio()
        if ratio > best_ratio and ratio >= 0.7:
            best_ratio = ratio
            best_pid = pid
    if best_pid:
        return best_pid, None, f"fuzzy_global({best_ratio:.2f})"
    
    return None, None, None


def import_file(img_file, product_id, variant_id=None):
    """Import a single image file."""
    file_bytes = img_file.read_bytes()
    content_type = mimetypes.guess_type(img_file.name)[0] or "image/png"
    width, height = get_image_dimensions(img_file)
    checksum = hashlib.sha256(file_bytes).hexdigest()
    
    existing_media = Media.objects.filter(checksum_sha256=checksum).first()
    if existing_media:
        media = existing_media
    else:
        media = Media.objects.create(
            kind=Media.Kind.IMAGE,
            filename=img_file.name,
            content_type=content_type,
            bytes=file_bytes,
            size_bytes=len(file_bytes),
            width=width,
            height=height,
            checksum_sha256=checksum,
        )
    
    if not ProductMedia.objects.filter(product_id=product_id, media=media).exists():
        max_order = ProductMedia.objects.filter(
            product_id=product_id
        ).aggregate(Max("sort_order"))["sort_order__max"]
        sort_order = (max_order or 0) + 1
        
        has_primary = ProductMedia.objects.filter(
            product_id=product_id, is_primary=True
        ).exists()
        
        pm_kwargs = {
            "product_id": product_id,
            "media": media,
            "alt": "",
            "sort_order": sort_order,
            "is_primary": not has_primary,
        }
        if variant_id:
            pm_kwargs["variant_id"] = variant_id
        
        ProductMedia.objects.create(**pm_kwargs)
        return True
    return False


def run():
    print("=" * 60)
    print("ENHANCED IMAGE MATCHING")
    print("=" * 60)
    
    # Build lookups
    page_map = build_page_to_products()
    
    variant_lookup = {}
    for v in Variant.objects.values("model_code", "product_id", "id"):
        if v["model_code"]:
            variant_lookup[v["model_code"].lower().strip()] = {
                "product_id": v["product_id"],
                "variant_id": v["id"],
            }
    
    product_name_lookup = {}
    for p in Product.objects.values("id", "slug", "name"):
        if p["name"]:
            product_name_lookup[p["name"].lower().strip()] = p["id"]
        if p["slug"]:
            product_name_lookup[p["slug"].lower().strip()] = p["id"]
    
    # Existing media filenames
    existing_filenames_lower = {
        f.lower() for f in Media.objects.values_list("filename", flat=True)
    }
    
    stats = {"scanned": 0, "already_imported": 0, "skipped": 0,
             "matched": 0, "imported": 0, "no_match": 0, "errors": 0,
             "methods": {}}
    still_unmatched = []
    
    for folder in sorted(FOTOLAR_DIR.iterdir()):
        if not folder.is_dir():
            continue
        for img_file in sorted(folder.iterdir()):
            if not img_file.is_file():
                continue
            if img_file.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            
            stats["scanned"] += 1
            rel = f"{folder.name}/{img_file.name}"
            
            if img_file.name.lower() in SKIP_FILENAMES:
                stats["skipped"] += 1
                continue
            
            if img_file.name.lower() in existing_filenames_lower:
                stats["already_imported"] += 1
                continue
            
            product_id, variant_id, method = find_best_product_for_file(
                img_file.stem, folder.name, page_map, variant_lookup, product_name_lookup
            )
            
            if product_id is None:
                stats["no_match"] += 1
                still_unmatched.append(rel)
                continue
            
            stats["matched"] += 1
            stats["methods"][method] = stats["methods"].get(method, 0) + 1
            
            try:
                linked = import_file(img_file, product_id, variant_id)
                if linked:
                    stats["imported"] += 1
                    pname = Product.objects.filter(id=product_id).values_list("name", flat=True).first()
                    print(f"  IMPORTED: {rel} -> {pname} [{method}]")
            except Exception as e:
                stats["errors"] += 1
                print(f"  ERROR: {rel}: {e}")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"  Scanned:          {stats['scanned']}")
    print(f"  Already imported: {stats['already_imported']}")
    print(f"  Skipped:          {stats['skipped']}")
    print(f"  Matched:          {stats['matched']}")
    print(f"  Imported:         {stats['imported']}")
    print(f"  Still unmatched:  {stats['no_match']}")
    print(f"  Errors:           {stats['errors']}")
    print(f"  Methods:          {stats['methods']}")
    
    if still_unmatched:
        print(f"\n  --- STILL UNMATCHED ({len(still_unmatched)}) ---")
        for u in still_unmatched:
            print(f"  {u}")
    
    # Final DB status
    total_products = Product.objects.count()
    products_with_images = Product.objects.filter(product_media__isnull=False).distinct().count()
    print(f"\n  Final: {products_with_images}/{total_products} products have images")


if __name__ == "__main__":
    run()
