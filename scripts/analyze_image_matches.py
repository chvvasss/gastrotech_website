#!/usr/bin/env python
"""
Analyze product images for database matching potential.

This script analyzes the Gastrotech2025_Final_Dogru_PS folder
and checks how many images can be matched to database variants.
"""

import os
import sys
import re
from pathlib import Path
from collections import defaultdict

# Add backend to path for Django models
BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from apps.catalog.models import Variant, Product, ProductMedia


def extract_code_from_filename(filename: str) -> tuple[str, str]:
    """
    Extract model code from filename.
    
    Examples:
        217780_Kombi_Konveksiyonel_Firin_6xGN11.jpg -> ('217780', 'Kombi Konveksiyonel Fırın 6xGN11')
        5K45SSEOB_Classic_Stand_Mikser_-_Siyah_43_Lt.jpg -> ('5K45SSEOB', 'Classic Stand Mikser - Siyah 4.3 Lt')
        STD7010_Alt_Stant_Kapaksiz.jpg -> ('STD7010', 'Alt Stant Kapaksız')
        206350_Alt_Stand_icin_Kapak_1.jpg -> ('206350', 'Alt Stand icin Kapak') [index variant]
    """
    stem = Path(filename).stem
    parts = stem.split('_', 1)  # Split on first underscore only
    
    if len(parts) >= 2:
        code = parts[0]
        name = parts[1].replace('_', ' ')
        return code, name
    else:
        return stem, ""


def check_variant_exists(model_code: str) -> tuple[bool, Variant | None]:
    """Check if variant exists with given model code."""
    variant = Variant.objects.filter(model_code__iexact=model_code).select_related('product').first()
    return variant is not None, variant


def analyze_images(image_dir: str) -> dict:
    """
    Analyze all images in directory for database matching.
    """
    results = {
        'total': 0,
        'matched': [],
        'unmatched': [],
        'duplicate_codes': defaultdict(list),  # code -> list of files
        'by_match_type': defaultdict(int),
        'products_with_images': set(),
    }
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff'}
    
    for file in os.listdir(image_dir):
        ext = Path(file).suffix.lower()
        if ext not in image_extensions:
            continue
            
        results['total'] += 1
        code, name = extract_code_from_filename(file)
        
        # Track duplicates
        results['duplicate_codes'][code].append(file)
        
        # Check database
        exists, variant = check_variant_exists(code)
        
        if exists:
            results['matched'].append({
                'file': file,
                'code': code,
                'name': name,
                'variant_id': str(variant.id),
                'product_id': str(variant.product.id) if variant.product else None,
                'product_title': variant.product.title_tr if variant.product else None,
            })
            if variant.product:
                results['products_with_images'].add(str(variant.product.id))
            results['by_match_type']['exact'] += 1
        else:
            results['unmatched'].append({
                'file': file,
                'code': code,
                'name': name,
            })
            results['by_match_type']['unmatched'] += 1
    
    return results


def print_report(results: dict):
    """Print analysis report."""
    print("=" * 60)
    print("GÖRSEL EŞLEŞME ANALİZİ")
    print("=" * 60)
    
    total = results['total']
    matched_count = len(results['matched'])
    unmatched_count = len(results['unmatched'])
    
    print(f"\nToplam Görsel: {total}")
    print(f"Eşleşen: {matched_count} ({matched_count/total*100:.1f}%)")
    print(f"Eşleşmeyen: {unmatched_count} ({unmatched_count/total*100:.1f}%)")
    print(f"Benzersiz Ürünler: {len(results['products_with_images'])}")
    
    # Duplicates (same code, multiple images)
    duplicates = {k: v for k, v in results['duplicate_codes'].items() if len(v) > 1}
    if duplicates:
        print(f"\nBirden fazla görsel: {len(duplicates)} ürün kodu")
        for code, files in list(duplicates.items())[:10]:
            print(f"  {code}: {len(files)} dosya")
    
    # Unmatched codes
    if results['unmatched']:
        print(f"\n{'='*60}")
        print("EŞLEŞMEYEN DOSYALAR (ilk 50):")
        print("=" * 60)
        for item in results['unmatched'][:50]:
            print(f"  Dosya: {item['file']}")
            print(f"    Kod: {item['code']}, İsim: {item['name']}")
        if len(results['unmatched']) > 50:
            print(f"  ... ve {len(results['unmatched']) - 50} dosya daha")
    
    # Sample matched
    print(f"\n{'='*60}")
    print("EŞLEŞEN ÖRNEKLER (ilk 20):")
    print("=" * 60)
    for item in results['matched'][:20]:
        print(f"  {item['file']}")
        print(f"    -> {item['code']} -> {item['product_title']}")
    
    return results


def main():
    # Default image directory
    image_dir = r"C:\Users\emir\Desktop\Gastrotech2025_Final_Dogru_PS"
    
    if not os.path.isdir(image_dir):
        print(f"Dizin bulunamadı: {image_dir}")
        return
    
    print(f"Analiz ediliyor: {image_dir}")
    results = analyze_images(image_dir)
    print_report(results)
    
    # Save detailed results as JSON
    import json
    output_file = Path(__file__).parent / "image_analysis_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        # Convert sets to lists for JSON serialization
        results_copy = dict(results)
        results_copy['products_with_images'] = list(results['products_with_images'])
        results_copy['duplicate_codes'] = dict(results['duplicate_codes'])
        json.dump(results_copy, f, ensure_ascii=False, indent=2)
    print(f"\nDetaylı sonuçlar kaydedildi: {output_file}")


if __name__ == "__main__":
    main()
