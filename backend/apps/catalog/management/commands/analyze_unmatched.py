"""
Analyze unmatched image files: dump full list and try to find partial matches.
"""
from django.core.management.base import BaseCommand
from apps.catalog.models import Product, Variant
from pathlib import Path


class Command(BaseCommand):
    help = "Analyze unmatched image files"

    def handle(self, *args, **options):
        photos_dir = Path(r"C:\Users\emir\Desktop\Fotolar")
        image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
        skip_filenames = {"liste.png", "liste.jpg", "thumbs.db", "desktop.ini"}

        # Build variant lookup
        variant_codes = set()
        for v in Variant.objects.all().values_list("model_code", flat=True):
            if v:
                variant_codes.add(v.upper())

        # Product slugs and names
        product_slugs = set()
        product_names = set()
        for p in Product.objects.all().values_list("slug", "name"):
            product_slugs.add(p[0].upper())
            product_names.add(p[1].upper())

        self.stdout.write(f"Variant codes in DB: {len(variant_codes)}")
        self.stdout.write(f"Product slugs in DB: {len(product_slugs)}")

        # Find all unmatched
        unmatched = []
        matched = []
        for folder in sorted(photos_dir.iterdir()):
            if not folder.is_dir():
                continue
            for img_file in sorted(folder.iterdir()):
                if not img_file.is_file():
                    continue
                if img_file.suffix.lower() not in image_extensions:
                    continue
                if img_file.name.lower() in skip_filenames:
                    continue

                stem = img_file.stem.upper()

                if stem in variant_codes:
                    matched.append(img_file)
                elif stem == "0":
                    # pdf_ref match - check
                    parts = folder.name.replace(".", "-").split("-")
                    found = False
                    for part in parts:
                        part = part.strip()
                        if part.isdigit():
                            num = int(part)
                            for ref in [f"p{num}", f"p{part}", part]:
                                if Product.objects.filter(pdf_ref=ref).exists():
                                    found = True
                                    break
                        if found:
                            break
                    if found:
                        matched.append(img_file)
                    else:
                        unmatched.append(img_file)
                elif stem in product_slugs or stem in product_names:
                    matched.append(img_file)
                else:
                    unmatched.append(img_file)

        self.stdout.write(f"\nMatched: {len(matched)}")
        self.stdout.write(f"Unmatched: {len(unmatched)}")

        # Group unmatched by folder
        folder_groups = {}
        for f in unmatched:
            folder = f.parent.name
            if folder not in folder_groups:
                folder_groups[folder] = []
            folder_groups[folder].append(f.stem)

        self.stdout.write("\n=== ALL UNMATCHED BY FOLDER ===")
        for folder in sorted(folder_groups.keys()):
            stems = folder_groups[folder]
            self.stdout.write(f"\n  [{folder}] ({len(stems)} files)")
            for s in stems:
                # Try to find closest variant
                close = [v for v in variant_codes if s.upper().startswith(v[:3])]
                hint = f"  (close: {', '.join(sorted(close)[:3])})" if close else ""
                self.stdout.write(f"    {s}{hint}")

        # Sample: show what variant codes look like
        self.stdout.write("\n=== SAMPLE VARIANT CODES (first 30) ===")
        sample = sorted(variant_codes)[:30]
        for v in sample:
            self.stdout.write(f"  {v}")
