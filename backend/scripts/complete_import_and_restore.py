# Complete import & restore script:
# 1. Check current DB status (images, PDFs)
# 2. Re-import any errored images (fix 'order' -> 'sort_order' issue)
# 3. Attempt to match previously unmatched files with expanded strategies
# 4. Restore catalog PDFs
import os
import sys
import hashlib
import mimetypes
import re
from pathlib import Path
from unicodedata import normalize as unicode_normalize

sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from django.db.models import Max, Count
from apps.catalog.models import (
    Media, Product, ProductMedia, Variant, Category, CategoryCatalog
)

FOTOLAR_DIR = Path(r"C:\Users\emir\Desktop\Fotolar")
PDF_DIR = Path(r"C:\Users\emir\Desktop\pdfler")
FIXTURES_PDF_DIR = Path(r"C:\Users\emir\Desktop\gastrotech_website-main\backend\fixtures\catalog_pdfs")

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SKIP_FILENAMES = {"liste.png", "liste.jpg"}

# ──────────────────────────────────────────────
# STEP 0: DB Status
# ──────────────────────────────────────────────
def check_status():
    print("=" * 60)
    print("STEP 0: Current DB Status")
    print("=" * 60)
    
    total_media = Media.objects.count()
    image_media = Media.objects.filter(kind="image").count()
    doc_media = Media.objects.filter(kind="document").count()
    total_pm = ProductMedia.objects.count()
    total_products = Product.objects.count()
    products_with_images = Product.objects.filter(product_media__isnull=False).distinct().count()
    products_without_images = total_products - products_with_images
    total_variants = Variant.objects.count()
    total_catalogs = CategoryCatalog.objects.count()
    
    # Check PDFs
    pdf_media = Media.objects.filter(kind="document", content_type="application/pdf")
    pdf_count = pdf_media.count()
    pdf_with_bytes = pdf_media.exclude(bytes=b"").exclude(bytes__isnull=True).count()
    
    print(f"  Total Media records:        {total_media}")
    print(f"  Image Media:                {image_media}")
    print(f"  Document Media:             {doc_media}")
    print(f"  Total ProductMedia links:   {total_pm}")
    print(f"  Total Products:             {total_products}")
    print(f"  Products WITH images:       {products_with_images}")
    print(f"  Products WITHOUT images:    {products_without_images}")
    print(f"  Total Variants:             {total_variants}")
    print(f"  PDF Media records:          {pdf_count}")
    print(f"  PDFs with actual bytes:     {pdf_with_bytes}")
    print(f"  CategoryCatalog entries:    {total_catalogs}")
    
    # List catalogs
    print("\n  Catalog PDF Details:")
    for cc in CategoryCatalog.objects.select_related("media", "category").all():
        media = cc.media
        has_bytes = bool(media.bytes) if media else False
        sz = media.size_bytes if media else 0
        cat_name = cc.category.name if cc.category else "N/A"
        fname = media.filename if media else "N/A"
        print(f"    [{cat_name:30s}] {fname:30s} bytes={'YES' if has_bytes else 'NO':3s}  size={sz}")
    
    return products_without_images


# ──────────────────────────────────────────────
# STEP 1: Scan & Import Missing Images
# ──────────────────────────────────────────────
def get_image_dimensions(filepath):
    try:
        from PIL import Image as PILImage
        with PILImage.open(filepath) as img:
            return img.width, img.height
    except Exception:
        return None, None


def build_lookup():
    """Build comprehensive lookup maps for matching."""
    # Variant model_code -> product_id
    variant_map = {}
    for v in Variant.objects.values("model_code", "product_id", "id"):
        if v["model_code"]:
            variant_map[v["model_code"].lower()] = {
                "product_id": v["product_id"],
                "variant_id": v["id"],
            }
    
    # Product slug -> product_id
    slug_map = {}
    for p in Product.objects.values("id", "slug", "name", "pdf_ref"):
        if p["slug"]:
            slug_map[p["slug"].lower()] = p["id"]
        if p["name"]:
            slug_map[p["name"].lower()] = p["id"]
    
    # pdf_ref -> product_id
    pdf_ref_map = {}
    for p in Product.objects.exclude(pdf_ref__isnull=True).exclude(pdf_ref="").values("id", "pdf_ref"):
        pdf_ref_map[p["pdf_ref"].lower()] = p["id"]
    
    return variant_map, slug_map, pdf_ref_map


def normalize_stem(stem):
    """Normalize a filename stem for fuzzy matching."""
    s = stem.strip()
    # Replace common separators
    s = s.replace("_", " ").replace("-", " ")
    # Remove extra spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s.lower()


def find_product_for_image(filename_stem, folder_name, variant_map, slug_map, pdf_ref_map):
    """Enhanced product finder with more matching strategies."""
    stem_lower = filename_stem.lower().strip()
    
    # 1. Exact variant match
    if stem_lower in variant_map:
        v = variant_map[stem_lower]
        return v["product_id"], v["variant_id"], "exact"
    
    # 2. Normalized variant match (strip spaces, dashes, underscores)
    normalized = normalize_stem(filename_stem)
    for code, v in variant_map.items():
        if normalize_stem(code) == normalized:
            return v["product_id"], v["variant_id"], "normalized"
    
    # 3. Partial variant match (filename contains or is contained in model_code)
    for code, v in variant_map.items():
        code_norm = code.lower().strip()
        if len(stem_lower) >= 4 and (stem_lower in code_norm or code_norm in stem_lower):
            return v["product_id"], v["variant_id"], "partial"
    
    # 4. Slug/Name match
    if stem_lower in slug_map:
        return slug_map[stem_lower], None, "name"
    
    # 5. For "0" files, use pdf_ref
    if filename_stem.strip() in ("0", "1", "2", "3"):
        parts = folder_name.replace(".", "-").split("-")
        for part in parts:
            part = part.strip()
            if part.isdigit():
                num = int(part)
                for ref in [f"p{num}", f"p{part}", part, str(num)]:
                    if ref.lower() in pdf_ref_map:
                        return pdf_ref_map[ref.lower()], None, "pdf_ref"
    
    return None, None, None


def import_images():
    print("\n" + "=" * 60)
    print("STEP 1: Scan and Import Missing Images")
    print("=" * 60)
    
    if not FOTOLAR_DIR.exists():
        print(f"  ERROR: {FOTOLAR_DIR} not found!")
        return
    
    variant_map, slug_map, pdf_ref_map = build_lookup()
    
    # Get all existing media filenames and checksums
    existing_filenames = set(
        Media.objects.values_list("filename", flat=True)
    )
    existing_filenames_lower = {f.lower() for f in existing_filenames}
    
    # Get existing ProductMedia links
    existing_links = set()
    for pm in ProductMedia.objects.values_list("product_id", "media__filename"):
        existing_links.add((pm[0], pm[1].lower() if pm[1] else ""))
    
    stats = {
        "scanned": 0,
        "already_imported": 0,
        "skipped_non_product": 0,
        "no_match": 0,
        "imported": 0,
        "linked": 0,
        "errors": 0,
        "methods": {},
    }
    unmatched_list = []
    
    for folder in sorted(FOTOLAR_DIR.iterdir()):
        if not folder.is_dir():
            continue
        
        for img_file in sorted(folder.iterdir()):
            if not img_file.is_file():
                continue
            if img_file.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            
            stats["scanned"] += 1
            rel_path = f"{folder.name}/{img_file.name}"
            
            if img_file.name.lower() in SKIP_FILENAMES:
                stats["skipped_non_product"] += 1
                continue
            
            # Check if already in DB by filename
            if img_file.name.lower() in existing_filenames_lower:
                stats["already_imported"] += 1
                continue
            
            filename_stem = img_file.stem
            folder_name = folder.name
            
            product_id, variant_id, method = find_product_for_image(
                filename_stem, folder_name, variant_map, slug_map, pdf_ref_map
            )
            
            if product_id is None:
                stats["no_match"] += 1
                unmatched_list.append(rel_path)
                continue
            
            # Import it
            try:
                file_bytes = img_file.read_bytes()
                content_type = mimetypes.guess_type(img_file.name)[0] or "image/png"
                width, height = get_image_dimensions(img_file)
                checksum = hashlib.sha256(file_bytes).hexdigest()
                
                # Check for duplicate by checksum
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
                    stats["imported"] += 1
                
                # Create ProductMedia link
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
                    stats["linked"] += 1
                
                stats["methods"][method] = stats["methods"].get(method, 0) + 1
                
                if (stats["imported"] + stats["linked"]) % 20 == 0:
                    print(f"  Progress: {stats['imported']} imported, {stats['linked']} linked...")
            
            except Exception as e:
                stats["errors"] += 1
                print(f"  ERROR: {rel_path}: {e}")
    
    print(f"\n  === IMAGE IMPORT SUMMARY ===")
    print(f"  Total files scanned: {stats['scanned']}")
    print(f"  Already imported (skipped): {stats['already_imported']}")
    print(f"  Non-product files (skipped): {stats['skipped_non_product']}")
    print(f"  No match found: {stats['no_match']}")
    print(f"  Successfully imported: {stats['imported']}")
    print(f"  New ProductMedia links: {stats['linked']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Match methods: {stats['methods']}")
    
    if unmatched_list:
        print(f"\n  --- UNMATCHED FILES ({len(unmatched_list)}) ---")
        for u in unmatched_list:
            print(f"  NO MATCH: {u}")


# ──────────────────────────────────────────────
# STEP 2: Restore Catalog PDFs
# ──────────────────────────────────────────────

# Mapping from Turkish PDF filenames to fixture slug names
PDF_MAPPING = {
    "bulaşık.pdf": "bulasik-yikama.pdf",
    "fırınlar.pdf": "firinlar.pdf",
    "hazırlık ekipmanları.pdf": "hazirlik-ekipmanlari.pdf",
    "kafeterya.pdf": "kafeterya.pdf",
    "pişirme 600 serisi.pdf": "pisirme-600.pdf",
    "pişirme 700 serisi.pdf": "pisirme-700.pdf",
    "pişirme 900 serisi.pdf": "pisirme-900.pdf",
    "pişirme diğer serisi.pdf": "pisirme-diger.pdf",
    "pişirme drop-in serisi.pdf": "pisirme-dropin.pdf",
    "pişirme electrolux 700 serisi.pdf": "pisirme-electrolux-700.pdf",
    "pişirme electrolux 900 serisi.pdf": "pisirme-electrolux-900.pdf",
    "soğutma.pdf": "sogutma.pdf",
    "tamamlayıcı.pdf": "tamamlayici.pdf",
    "çamaşır.pdf": "camasir.pdf",
}


def restore_pdfs():
    print("\n" + "=" * 60)
    print("STEP 2: Restore Catalog PDFs")
    print("=" * 60)
    
    if not PDF_DIR.exists():
        print(f"  ERROR: {PDF_DIR} not found!")
        return
    
    # Check which PDFs need restoration
    pdf_media_list = Media.objects.filter(
        kind="document", content_type="application/pdf"
    )
    
    restored_count = 0
    already_ok_count = 0
    fixture_restored = 0
    
    for media in pdf_media_list:
        has_bytes = bool(media.bytes) and len(media.bytes) > 0
        if has_bytes and media.size_bytes > 0:
            already_ok_count += 1
            print(f"  OK: {media.filename} ({media.size_bytes} bytes)")
            continue
        
        # Try to find source PDF
        source_path = None
        
        # 1. Check fixtures directory first (by slug filename)
        fixture_path = FIXTURES_PDF_DIR / media.filename
        if fixture_path.exists():
            source_path = fixture_path
            print(f"  RESTORING from fixtures: {media.filename}")
        else:
            # 2. Check Turkish-named PDFs
            for turkish_name, slug_name in PDF_MAPPING.items():
                if slug_name == media.filename:
                    turkish_path = PDF_DIR / turkish_name
                    if turkish_path.exists():
                        source_path = turkish_path
                        print(f"  RESTORING from pdfler: {turkish_name} -> {media.filename}")
                        break
        
        if source_path:
            try:
                pdf_bytes = source_path.read_bytes()
                media.bytes = pdf_bytes
                media.size_bytes = len(pdf_bytes)
                media.save(update_fields=["bytes", "size_bytes"])
                restored_count += 1
            except Exception as e:
                print(f"  ERROR restoring {media.filename}: {e}")
        else:
            print(f"  WARNING: No source found for {media.filename}")
    
    # Also check if any PDFs are completely missing from DB
    for turkish_name, slug_name in PDF_MAPPING.items():
        if not Media.objects.filter(filename=slug_name).exists():
            source = PDF_DIR / turkish_name
            if source.exists():
                print(f"  CREATING missing PDF: {slug_name} (from {turkish_name})")
                try:
                    pdf_bytes = source.read_bytes()
                    Media.objects.create(
                        kind="document",
                        filename=slug_name,
                        content_type="application/pdf",
                        bytes=pdf_bytes,
                        size_bytes=len(pdf_bytes),
                    )
                    restored_count += 1
                except Exception as e:
                    print(f"  ERROR creating {slug_name}: {e}")
    
    # Also copy into fixtures if not there
    if FIXTURES_PDF_DIR.exists():
        for turkish_name, slug_name in PDF_MAPPING.items():
            fixture_path = FIXTURES_PDF_DIR / slug_name
            turkish_path = PDF_DIR / turkish_name
            if not fixture_path.exists() and turkish_path.exists():
                import shutil
                shutil.copy2(turkish_path, fixture_path)
                fixture_restored += 1
                print(f"  COPIED to fixtures: {slug_name}")
    
    print(f"\n  === PDF RESTORE SUMMARY ===")
    print(f"  Already OK: {already_ok_count}")
    print(f"  Restored: {restored_count}")
    print(f"  Copied to fixtures: {fixture_restored}")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def run():
    check_status()
    import_images()
    restore_pdfs()
    
    # Final status
    print("\n" + "=" * 60)
    print("FINAL STATUS CHECK")
    print("=" * 60)
    check_status()


if __name__ == "__main__":
    run()
