"""
Image import script - matches image filenames to product slugs/names.

Strategy:
1. Extract base model code from filename (strip extension, _2 suffix)
2. Normalize both image code and product slug/name to comparable format
3. Match image -> product using normalized codes
4. Create Media + ProductMedia records in database
"""

import os
import sys
import re
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ["DATABASE_URL"] = "postgres://postgres:postgres@localhost:5432/gastrotech"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import Product, Media, ProductMedia

# Image directories
IMAGE_DIRS = [
    Path(r"D:\mutaş fotolar (1)"),
    Path(r"C:\Users\emir\Desktop\Fotolar"),
]

def normalize(text):
    """Normalize text for comparison - lowercase, strip special chars."""
    text = text.lower()
    text = text.replace("-", "").replace("_", "").replace(" ", "").replace(".", "")
    # Remove common Turkish chars for matching
    text = text.replace("ı", "i").replace("ö", "o").replace("ü", "u")
    text = text.replace("ç", "c").replace("ş", "s").replace("ğ", "g")
    return text

def extract_code(filename):
    """Extract model code from filename, stripping _2, _3 suffixes."""
    stem = Path(filename).stem
    # Remove trailing _2, _3 etc (secondary image indicators)
    base = re.sub(r'_\d+$', '', stem)
    return base

def get_sort_order(filename):
    """Determine sort order: base image = 0, _2 = 1, _3 = 2, etc."""
    stem = Path(filename).stem
    match = re.search(r'_(\d+)$', stem)
    if match:
        return int(match.group(1))
    return 0

def find_all_images():
    """Scan all image directories recursively."""
    extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
    images = []
    for base_dir in IMAGE_DIRS:
        if not base_dir.exists():
            print(f"[WARN] Directory not found: {base_dir}")
            continue
        for img_path in base_dir.rglob("*"):
            if img_path.suffix.lower() in extensions and img_path.is_file():
                images.append(img_path)
    return images

def build_product_index():
    """Build lookup index from normalized codes to products."""
    index = {}
    products = Product.objects.all()
    for p in products:
        # Extract model code from product name (first word or code pattern)
        name = p.name
        slug = p.slug

        # Method 1: Use the slug directly
        norm_slug = normalize(slug)
        index[norm_slug] = p

        # Method 2: Extract model code from name
        # Product names like "GKO7010 Gazlı Ocak 2 Gözlü" -> code is GKO7010
        parts = name.split()
        if parts:
            first_word = parts[0]
            norm_code = normalize(first_word)
            if norm_code not in index:
                index[norm_code] = p

            # Also try first two words combined (for codes like "VBY FT3000")
            if len(parts) >= 2:
                two_word = parts[0] + parts[1]
                norm_two = normalize(two_word)
                if norm_two not in index:
                    index[norm_two] = p

        # Method 3: Extract specific model patterns from name
        # Match patterns like GKO7010, VBY1000D, 5K45SSEOB, RTR120, etc.
        codes = re.findall(r'[A-Z0-9][A-Za-z0-9\-]{2,}', name)
        for code in codes:
            norm_c = normalize(code)
            if norm_c not in index:
                index[norm_c] = p

    return index

def match_image_to_product(img_path, product_index):
    """Try to match an image file to a product."""
    filename = img_path.name
    code = extract_code(filename)
    norm_code = normalize(code)

    # Direct match
    if norm_code in product_index:
        return product_index[norm_code]

    # Try partial match - check if code is contained in any product key
    for key, product in product_index.items():
        if len(norm_code) >= 4 and norm_code in key:
            return product
        if len(key) >= 4 and key.startswith(norm_code):
            return product

    # Try even more flexible: check if image code is a substring of product name
    norm_code_upper = code.upper()
    for product in Product.objects.all():
        if norm_code_upper in product.name.upper().replace(" ", "").replace("-", ""):
            return product

    return None

def get_content_type(path):
    """Determine MIME type from file extension."""
    ext = path.suffix.lower()
    types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
    }
    return types.get(ext, 'application/octet-stream')

def run():
    print("=== Image Import Script ===\n")

    # Scan images
    images = find_all_images()
    print(f"Found {len(images)} images across all directories.\n")

    # Build product index
    product_index = build_product_index()
    print(f"Built product index with {len(product_index)} normalized keys.\n")

    # Match and import
    matched = 0
    unmatched = []
    skipped = 0

    for img_path in sorted(images):
        product = match_image_to_product(img_path, product_index)

        if not product:
            unmatched.append(str(img_path))
            continue

        # Check if already imported (by filename)
        existing = ProductMedia.objects.filter(
            product=product,
            media__filename=img_path.name
        ).first()
        if existing:
            skipped += 1
            continue

        # Read file and create Media
        try:
            with open(img_path, "rb") as f:
                content = f.read()

            media = Media.objects.create(
                kind=Media.Kind.IMAGE,
                filename=img_path.name,
                content_type=get_content_type(img_path),
                bytes=content,
            )

            sort_order = get_sort_order(img_path.name)
            is_primary = (sort_order == 0)

            # Check if product already has a primary
            if is_primary:
                existing_primary = ProductMedia.objects.filter(
                    product=product, is_primary=True
                ).exists()
                if existing_primary:
                    is_primary = False

            ProductMedia.objects.create(
                product=product,
                media=media,
                alt=product.name,
                sort_order=sort_order,
                is_primary=is_primary,
            )

            matched += 1
            marker = " [PRIMARY]" if is_primary else ""
            print(f"[OK] {img_path.name:40s} -> {product.slug}{marker}")

        except Exception as e:
            print(f"[ERROR] {img_path.name}: {e}")

    print(f"\n=== Summary ===")
    print(f"Matched & imported: {matched}")
    print(f"Skipped (already exists): {skipped}")
    print(f"Unmatched: {len(unmatched)}")

    if unmatched:
        print(f"\n--- Unmatched files ({len(unmatched)}) ---")
        for u in unmatched:
            print(f"  {u}")

if __name__ == "__main__":
    run()
