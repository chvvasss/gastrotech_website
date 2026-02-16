"""
Full product import from Gastrotech_Tum_Veriler.xlsx.

Creates: Categories, Subcategories, Brands, Series, Products, Variants.
Preserves existing 8 root categories by slug matching.

Usage:
    cd backend
    python scripts/import_all_products.py
"""
import os
import sys
import re

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import django
django.setup()

import openpyxl
from django.db import transaction
from apps.catalog.models import Category, Series, Brand, BrandCategory, Product, Variant
from apps.common.slugify_tr import slugify_tr


# ── Category slug mapping (Excel name → existing DB slug) ──────────────────
CAT_SLUG_MAP = {
    "Pişirme Ekipmanları": "pisirme",
    "FIRINLAR":            "firinlar",
    "Fırınlar":            "firinlar",
    "HAZIRLIK":            "hazirlik",
    "KAFETERYA":           "kafeterya",
    "Kafeterya Ekipmanları": "kafeterya",
    "SOĞUTMA":             "sogutma",
    "Bulaşık Makineleri":  "bulasik",
    "Çamaşır Ekipmanları": "camasirhane",
    "Tamamlayıcı Ekipmanlar": "tamamlayici",
    "Aksesuarlar":         "aksesuarlar",
}

# ── Brand detection from series/product name ───────────────────────────────
KNOWN_BRANDS = {
    "KitchenAid": ["Kitchen Aid", "KitchenAid", "5K"],
    "Scotsman":   ["Scotsman"],
    "Rational":   ["Rational", "I Combi", "I Vario", "iCombi", "iVario"],
    "Cunill":     ["Cunill"],
    "Mahlkönig":  ["EK43", "EK 43"],
    "Fiorenzato": ["F64", "F83", "F71", "F6 DM", "F10", "F12"],
    "Faema":      ["Eagle", "FAEMA"],
    "La Cimbali":  ["M1", "M4", "M23", "S1", "MAGICA"],
    "Victoria Arduino": ["Eagle Dome", "Victoria"],
    "Acaia":      ["Acaia"],
    "Puqpress":   ["PUQ PRESS", "Puqpress"],
}

# Caches
_category_cache = {}
_series_cache = {}
_brand_cache = {}


def get_or_create_category(name, parent=None):
    """Get or create a root category, matching existing DB by slug."""
    cache_key = (name, parent.id if parent else None)
    if cache_key in _category_cache:
        return _category_cache[cache_key]

    slug = CAT_SLUG_MAP.get(name)
    if not slug:
        slug = slugify_tr(name)

    # Try slug match first (for existing categories)
    if parent is None:
        cat = Category.objects.filter(slug=slug, parent__isnull=True).first()
    else:
        cat = Category.objects.filter(slug=slug, parent=parent).first()

    if not cat:
        # Try name match
        if parent is None:
            cat = Category.objects.filter(name__iexact=name, parent__isnull=True).first()
        else:
            cat = Category.objects.filter(name__iexact=name, parent=parent).first()

    if not cat:
        order = Category.objects.filter(parent=parent).count() + 1
        cat = Category.objects.create(
            name=name,
            slug=slug,
            parent=parent,
            order=order,
            is_featured=parent is None,
        )
        print(f"  [+] Category created: {name} (slug={slug}, parent={parent})")

    _category_cache[cache_key] = cat
    return cat


def get_or_create_subcategory(name, parent_cat):
    """Get or create a subcategory under a parent."""
    cache_key = (name, parent_cat.id)
    if cache_key in _category_cache:
        return _category_cache[cache_key]

    slug = slugify_tr(name)

    cat = Category.objects.filter(slug=slug, parent=parent_cat).first()
    if not cat:
        cat = Category.objects.filter(name__iexact=name, parent=parent_cat).first()
    if not cat:
        # Also check globally to avoid duplicate slug issues
        existing = Category.objects.filter(slug=slug, parent__isnull=False).first()
        if existing and existing.parent == parent_cat:
            cat = existing

    if not cat:
        order = Category.objects.filter(parent=parent_cat).count() + 1
        cat = Category.objects.create(
            name=name,
            slug=slug,
            parent=parent_cat,
            order=order,
        )
        print(f"  [+] Subcategory created: {name} under {parent_cat.name}")

    _category_cache[cache_key] = cat
    return cat


def get_or_create_series(name, category):
    """Get or create a series. '-' or empty → 'Genel' series."""
    if not name or name.strip() in ("-", "None", ""):
        name = "Genel"

    cache_key = (name, category.id)
    if cache_key in _series_cache:
        return _series_cache[cache_key]

    slug = slugify_tr(name)
    if not slug:
        slug = "genel"

    # Make slug unique per category
    s = Series.objects.filter(slug=slug, category=category).first()
    if not s:
        s = Series.objects.filter(name__iexact=name, category=category).first()

    if not s:
        order = Series.objects.filter(category=category).count() + 1
        s = Series.objects.create(
            name=name,
            slug=slug,
            category=category,
            order=order,
        )
        print(f"  [+] Series created: {name} (slug={slug}) in {category.name}")

    _series_cache[cache_key] = s
    return s


def detect_brand(series_name, product_name):
    """Detect brand from series or product name. Default: Gastrotech."""
    text = f"{series_name or ''} {product_name or ''}"
    for brand_name, keywords in KNOWN_BRANDS.items():
        for kw in keywords:
            if kw.lower() in text.lower():
                return brand_name
    return "Gastrotech"


def get_or_create_brand(name, category=None):
    """Get or create a brand. Also links to category via BrandCategory."""
    if name in _brand_cache:
        brand = _brand_cache[name]
    else:
        slug = slugify_tr(name)
        brand = Brand.objects.filter(slug=slug).first()
        if not brand:
            brand = Brand.objects.filter(name__iexact=name).first()
        if not brand:
            brand = Brand.objects.create(
                name=name,
                slug=slug,
                is_active=True,
                order=0,
            )
            print(f"  [+] Brand created: {name}")
        _brand_cache[name] = brand

    # Link brand to category
    if category:
        root_cat = category
        while root_cat.parent:
            root_cat = root_cat.parent
        BrandCategory.objects.get_or_create(brand=brand, category=root_cat)

    return brand


def make_unique_slug(base_slug, existing_slugs):
    """Ensure slug is unique by appending counter if needed."""
    slug = base_slug
    counter = 1
    while slug in existing_slugs:
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def run():
    xlsx_path = os.path.join(os.path.dirname(__file__), "..", "Gastrotech_Tum_Veriler.xlsx")
    if not os.path.exists(xlsx_path):
        print(f"ERROR: Excel file not found at {xlsx_path}")
        sys.exit(1)

    print("=" * 60)
    print("GASTROTECH FULL PRODUCT IMPORT")
    print("=" * 60)

    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    ws = wb["Urunler"]

    # ── Phase 1: Parse all rows ────────────────────────────────────────────
    product_groups = {}
    skipped = 0
    total_rows = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        sira, urun_tr, urun_en, model_kodu, seri, kategori, alt_kategori = row[:7]

        if not urun_tr or not model_kodu:
            skipped += 1
            continue

        model_kodu = str(model_kodu).strip()
        if model_kodu == "-" or not model_kodu:
            skipped += 1
            continue

        total_rows += 1

        urun_tr = str(urun_tr).strip()
        urun_en = str(urun_en or "").strip()
        seri_str = str(seri or "").strip()
        kategori_str = str(kategori or "").strip()
        alt_kat_str = str(alt_kategori or "").strip()

        if not kategori_str or kategori_str == "None":
            skipped += 1
            continue

        # Product grouping: same product name + series + category = 1 product
        key = (urun_tr, seri_str, kategori_str)

        if key not in product_groups:
            product_groups[key] = {
                "name_tr": urun_tr,
                "name_en": urun_en,
                "series": seri_str,
                "category": kategori_str,
                "subcategory": alt_kat_str if alt_kat_str not in ("None", "-", "") else "",
                "variants": [],
            }

        product_groups[key]["variants"].append({
            "model_code": model_kodu,
            "name_tr": urun_tr,
            "name_en": urun_en,
        })

    wb.close()

    print(f"\nParsed {total_rows} rows into {len(product_groups)} product groups")
    print(f"Skipped {skipped} rows (header/empty/dash)")
    print("\nStarting import...\n")

    # ── Phase 2: Import ────────────────────────────────────────────────────
    stats = {
        "categories_created": 0,
        "series_created": 0,
        "brands_created": 0,
        "products_created": 0,
        "variants_created": 0,
        "errors": [],
    }

    # Pre-load existing slugs
    existing_product_slugs = set(Product.objects.values_list("slug", flat=True))

    with transaction.atomic():
        for key, group in product_groups.items():
            try:
                # 1. Category
                parent_cat = get_or_create_category(group["category"])

                # 2. Subcategory (if exists)
                target_cat = parent_cat
                if group["subcategory"]:
                    target_cat = get_or_create_subcategory(group["subcategory"], parent_cat)

                # 3. Series
                series = get_or_create_series(group["series"], target_cat)

                # 4. Brand
                brand_name = detect_brand(group["series"], group["name_tr"])
                brand = get_or_create_brand(brand_name, target_cat)

                # 5. Product
                base_slug = slugify_tr(group["name_tr"])
                if not base_slug:
                    base_slug = slugify_tr(group["variants"][0]["model_code"])

                # Make slug more specific with series
                if series.slug != "genel":
                    product_slug = f"{base_slug}-{series.slug}"
                else:
                    product_slug = base_slug

                if not product_slug:
                    product_slug = slugify_tr(group["variants"][0]["model_code"])

                product_slug = make_unique_slug(product_slug, existing_product_slugs)
                existing_product_slugs.add(product_slug)

                product = Product.objects.create(
                    name=group["name_tr"],
                    title_tr=group["name_tr"],
                    title_en=group["name_en"],
                    slug=product_slug,
                    series=series,
                    category=target_cat,
                    brand=brand,
                    status=Product.Status.ACTIVE,
                )
                stats["products_created"] += 1

                # 6. Variants
                for v in group["variants"]:
                    # Check if model code already exists
                    if Variant.objects.filter(model_code=v["model_code"]).exists():
                        continue

                    Variant.objects.create(
                        product=product,
                        model_code=v["model_code"],
                        name_tr=v["name_tr"],
                        name_en=v["name_en"],
                    )
                    stats["variants_created"] += 1

            except Exception as e:
                err = f"Error for {key}: {e}"
                stats["errors"].append(err)
                print(f"  [!] {err}")

    # ── Phase 3: Summary ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"Total rows processed:  {total_rows}")
    print(f"Product groups:        {len(product_groups)}")
    print(f"Products created:      {stats['products_created']}")
    print(f"Variants created:      {stats['variants_created']}")
    print(f"Categories (total):    {Category.objects.count()}")
    print(f"  Root categories:     {Category.objects.filter(parent__isnull=True).count()}")
    print(f"  Subcategories:       {Category.objects.filter(parent__isnull=False).count()}")
    print(f"Series (total):        {Series.objects.count()}")
    print(f"Brands (total):        {Brand.objects.count()}")
    print(f"Errors:                {len(stats['errors'])}")

    if stats["errors"]:
        print("\nFirst 10 errors:")
        for e in stats["errors"][:10]:
            print(f"  - {e}")


if __name__ == "__main__":
    run()
