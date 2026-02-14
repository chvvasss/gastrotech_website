
import os
import sys
import django
import shutil
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ["DATABASE_URL"] = "postgres://postgres:postgres@localhost:5432/gastrotech"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import Category, CategoryCatalog, Media

# Path to catalogs
# Path to catalogs
CATALOGS_DIR = Path(r"C:\Users\emir\Desktop\gastrotech_website-main\frontend\public\catalogs")

# Rename Mapping: (substr1, substr2, clean_filename, category_slug, category_title_tr)
RENAME_MAP = [
    ("electrolux", "700", "pisirme-electrolux-700.pdf", "pisirme", "Pişirme"),
    ("electrolux", "900", "pisirme-electrolux-900.pdf", "pisirme", "Pişirme"),
    ("600", None, "pisirme-600.pdf", "pisirme", "Pişirme"),
    ("700", None, "pisirme-700.pdf", "pisirme", "Pişirme"),
    ("900", None, "pisirme-900.pdf", "pisirme", "Pişirme"),
    ("drop", None, "pisirme-dropin.pdf", "pisirme", "Pişirme"),
    ("di", "er", "pisirme-diger.pdf", "pisirme", "Pişirme"),
    ("bula", None, "bulasik-yikama.pdf", "bulasik", "Bulaşık"),
    ("fir", None, "firinlar.pdf", "firinlar", "Fırınlar"),
    ("haz", None, "hazirlik-ekipmanlari.pdf", "hazirlik", "Hazırlık"),
    ("kaf", None, "kafeterya.pdf", "kafeterya", "Kafeterya"),
    ("so", "utma", "sogutma.pdf", "sogutma", "Soğutma"),
    ("tam", None, "tamamlayici.pdf", "tamamlayici", "Tamamlayıcı"),
    # Camasir must be last as it's tricky
    ("ama", "r", "camasir.pdf", "camasirhane", "Çamaşırhane"),
]

def find_category_by_slug(slug_part):
    return Category.objects.filter(slug__icontains=slug_part).first()

def run():
    print(f"Scanning {CATALOGS_DIR}...")
    if not CATALOGS_DIR.exists():
        print("Catalogs directory not found!")
        return

    files = list(CATALOGS_DIR.glob("*.pdf"))
    print(f"Found {len(files)} files.")

    processed_count = 0
    
    for file_path in files:
        original_name = file_path.name
        fname_lower = original_name.lower()
        
        new_name = None
        target_slug = None
        target_title = None
        
        matched = False
        for entry in RENAME_MAP:
            # handle tuple size 4 or 5
            if len(entry) == 5:
                k1, k2, clean_name, slug, title = entry
            else:
                k1, k2, clean_name, slug = entry
                title = slug.replace("-", " ").title()

            if k1 in fname_lower:
                if k2:
                    if k2 in fname_lower:
                        new_name, target_slug, target_title = clean_name, slug, title
                        matched = True
                        break
                else:
                    new_name, target_slug, target_title = clean_name, slug, title
                    matched = True
                    break
        
        # Fallbacks
        if not matched and fname_lower.startswith('f'):
            new_name, target_slug, target_title = "firinlar.pdf", "firinlar", "Fırınlar"
            matched = True
            
        if not matched and 'ama' in fname_lower:
             new_name, target_slug, target_title = "camasir.pdf", "camasirhane", "Çamaşırhane"
             matched = True

        if not matched:
            print(f"[SKIP] Unknown file: {original_name}")
            continue

        # 1. Rename logic
        final_path = file_path
        if new_name and new_name != original_name:
            final_path = CATALOGS_DIR / new_name
            try:
                if not final_path.exists():
                     shutil.move(str(file_path), str(final_path))
                     print(f"[RENAME] {original_name} -> {new_name}")
                else:
                     final_path = CATALOGS_DIR / new_name # Use existing renamed file
            except Exception as e:
                print(f"[ERROR] Renaming {original_name}: {e}")
                continue
        
        # 2. Category Logic
        category = Category.objects.filter(slug=target_slug).first()
        if not category:
            print(f"  [CREATE] Category {target_title} ({target_slug})")
            category = Category.objects.create(
                slug=target_slug,
                name=target_title,
                is_featured=True
            )
        
        # 3. Create Media & Catalog
        try:
            with open(final_path, "rb") as f:
                content = f.read()
            
            # Check existing media by filename to avoid dupes?
            # For now, just create new to ensure update.
            media = Media.objects.create(
                kind=Media.Kind.PDF,
                filename=new_name,
                content_type="application/pdf",
                bytes=content
            )
            
            # Display Title
            display_title = new_name.replace(".pdf", "").replace("-", " ").title()
            
            exists = CategoryCatalog.objects.filter(category=category, title_tr=display_title).first()
            if exists:
                exists.media = media
                exists.published = True
                exists.save()
                print(f"  [UPDATE] Catalog for {category.slug}")
            else:
                CategoryCatalog.objects.create(
                    category=category,
                    title_tr=display_title,
                    media=media,
                    published=True
                )
                print(f"  [LINK] Catalog linked to {category.slug}")
                
            processed_count += 1
            
        except Exception as e:
            print(f"  [ERROR] DB Error: {e}")

    print(f"\nDone. Processed {processed_count}.")

if __name__ == "__main__":
    run()
