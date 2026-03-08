"""
PDF Katalog Görsel Çıkarma & Yeniden İsimlendirme Script'i

Kullanım:
    # Adım 1: PDF'den tüm görselleri çıkar
    python scripts/catalog_digitize.py extract <pdf_path> [--output-dir images/]

    # Adım 2: Worker eşleştirme verisine göre yeniden isimlendir
    python scripts/catalog_digitize.py rename <image_commands.json> [--source-dir images/raw/ --target-dir images/]

    # Adım 3: Tek seferde (extract + rename)
    python scripts/catalog_digitize.py pipeline <pdf_path> <image_commands.json> [--output-dir images/]
"""

import sys
import os
import json
import shutil
import argparse
from pathlib import Path


def check_pymupdf():
    """Check if pymupdf is installed, provide install instructions if not."""
    try:
        import fitz  # noqa: F401
        return True
    except ImportError:
        print("ERROR: pymupdf is not installed.")
        print("Install it with: pip install pymupdf")
        sys.exit(1)


def extract_images(pdf_path: str, output_dir: str, min_width: int = 100, min_height: int = 100):
    """
    Extract all images from a PDF file.

    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save extracted images
        min_width: Minimum image width to extract (filters out icons/logos)
        min_height: Minimum image height to extract

    Returns:
        List of extracted image metadata
    """
    import fitz

    pdf_path = Path(pdf_path)
    raw_dir = Path(output_dir) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(1)

    doc = fitz.open(str(pdf_path))
    metadata = []
    img_counter = 0

    print(f"Processing {pdf_path.name} ({doc.page_count} pages)...")

    for page_num in range(doc.page_count):
        page = doc[page_num]
        image_list = page.get_images(full=True)

        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]

            try:
                base_image = doc.extract_image(xref)
            except Exception:
                continue

            if not base_image:
                continue

            width = base_image.get("width", 0)
            height = base_image.get("height", 0)

            # Filter out small images (icons, bullets, decorations)
            if width < min_width or height < min_height:
                continue

            image_bytes = base_image["image"]
            ext = base_image.get("ext", "jpg")
            if ext == "jpeg":
                ext = "jpg"

            filename = f"page{page_num + 1}_img{img_index}.{ext}"
            filepath = raw_dir / filename

            with open(filepath, "wb") as f:
                f.write(image_bytes)

            img_meta = {
                "filename": filename,
                "page": page_num + 1,
                "index": img_index,
                "width": width,
                "height": height,
                "size_bytes": len(image_bytes),
                "format": ext,
            }
            metadata.append(img_meta)
            img_counter += 1

    doc.close()

    # Save metadata
    meta_path = Path(output_dir) / "extraction_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "pdf": str(pdf_path),
            "total_pages": doc.page_count,
            "total_images_extracted": img_counter,
            "min_filter": f"{min_width}x{min_height}",
            "images": metadata,
        }, f, indent=2, ensure_ascii=False)

    print(f"Extracted {img_counter} images to {raw_dir}/")
    print(f"Metadata saved to {meta_path}")
    return metadata


def rename_images(commands_path: str, source_dir: str = None, target_dir: str = None):
    """
    Rename extracted images based on worker matching data.

    Args:
        commands_path: Path to image_commands.json from merger
        source_dir: Directory with raw extracted images (default: images/raw/)
        target_dir: Directory for renamed images (default: images/)
    """
    commands_path = Path(commands_path)
    if not commands_path.exists():
        print(f"ERROR: Commands file not found: {commands_path}")
        sys.exit(1)

    with open(commands_path, "r", encoding="utf-8") as f:
        commands = json.load(f)

    if source_dir is None:
        source_dir = Path("images") / "raw"
    else:
        source_dir = Path(source_dir)

    if target_dir is None:
        target_dir = Path("images")
    else:
        target_dir = Path(target_dir)

    target_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    failed = 0

    for cmd in commands:
        src = source_dir / cmd["source"]
        tgt = target_dir / cmd["target"]

        if not src.exists():
            print(f"  SKIP: {cmd['source']} not found")
            failed += 1
            continue

        shutil.copy2(src, tgt)
        success += 1
        primary_tag = " [PRIMARY]" if cmd.get("is_primary") else ""
        print(f"  OK: {cmd['source']} → {cmd['target']}{primary_tag}")

    print(f"\nRenamed {success}/{success + failed} images")
    if failed > 0:
        print(f"WARNING: {failed} images could not be found")


def pipeline(pdf_path: str, commands_path: str, output_dir: str = "images"):
    """Run full pipeline: extract then rename."""
    print("=" * 50)
    print("  ADIM 1: PDF'den Görselleri Çıkar")
    print("=" * 50)
    extract_images(pdf_path, output_dir)

    print()
    print("=" * 50)
    print("  ADIM 2: Görselleri Yeniden İsimlendir")
    print("=" * 50)
    rename_images(
        commands_path,
        source_dir=os.path.join(output_dir, "raw"),
        target_dir=output_dir,
    )
    print()
    print("Pipeline complete!")


def main():
    parser = argparse.ArgumentParser(
        description="PDF Katalog Görsel Çıkarma & Yeniden İsimlendirme"
    )
    subparsers = parser.add_subparsers(dest="command", help="Komut")

    # extract
    p_extract = subparsers.add_parser("extract", help="PDF'den görselleri çıkar")
    p_extract.add_argument("pdf_path", help="PDF dosya yolu")
    p_extract.add_argument("--output-dir", default="images", help="Çıktı klasörü (default: images/)")
    p_extract.add_argument("--min-width", type=int, default=100, help="Min genişlik px (default: 100)")
    p_extract.add_argument("--min-height", type=int, default=100, help="Min yükseklik px (default: 100)")

    # rename
    p_rename = subparsers.add_parser("rename", help="Görselleri eşleştirmeye göre yeniden isimlendir")
    p_rename.add_argument("commands_path", help="image_commands.json dosya yolu")
    p_rename.add_argument("--source-dir", default=None, help="Kaynak klasör (default: images/raw/)")
    p_rename.add_argument("--target-dir", default=None, help="Hedef klasör (default: images/)")

    # pipeline
    p_pipeline = subparsers.add_parser("pipeline", help="Tam pipeline: extract + rename")
    p_pipeline.add_argument("pdf_path", help="PDF dosya yolu")
    p_pipeline.add_argument("commands_path", help="image_commands.json dosya yolu")
    p_pipeline.add_argument("--output-dir", default="images", help="Çıktı klasörü (default: images/)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    check_pymupdf()

    if args.command == "extract":
        extract_images(args.pdf_path, args.output_dir, args.min_width, args.min_height)
    elif args.command == "rename":
        rename_images(args.commands_path, args.source_dir, args.target_dir)
    elif args.command == "pipeline":
        pipeline(args.pdf_path, args.commands_path, args.output_dir)


if __name__ == "__main__":
    main()
