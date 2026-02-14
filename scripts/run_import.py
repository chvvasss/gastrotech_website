#!/usr/bin/env python
"""
Product Import CLI Script

Usage:
    python scripts/run_import.py <file_path> [--mode {smart,strict}] [--commit] [--no-input]

Example:
    python scripts/run_import.py catalog.xlsx --mode smart --commit
"""

import os
import sys
import argparse
import time
from pathlib import Path
from decimal import Decimal

# Setup Django environment
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent / "backend"
sys.path.insert(0, str(backend_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django
django.setup()

from django.db import transaction
from apps.ops.services.unified_import import UnifiedImportService
from apps.ops.models import ImportJob
from apps.catalog.models import Media

class Color:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Color.BOLD}{Color.BLUE}{'='*60}{Color.END}")
    print(f"{Color.BOLD}{Color.BLUE}{text:^60}{Color.END}")
    print(f"{Color.BOLD}{Color.BLUE}{'='*60}{Color.END}\n")

def print_success(text):
    print(f"{Color.GREEN}[OK] {text}{Color.END}")

def print_error(text):
    print(f"{Color.RED}[ERR] {text}{Color.END}")

def print_warning(text):
    print(f"{Color.YELLOW}[WARN] {text}{Color.END}")

def print_info(text):
    print(f"{Color.BLUE}[INFO] {text}{Color.END}")

def sanitize_for_json(obj):
    """Convert Decimals to strings for JSON serialization."""
    if isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    return obj

def main():
    parser = argparse.ArgumentParser(description="Import products from Excel/CSV file.")
    parser.add_argument("file_path", type=str, help="Path to the Excel/CSV file to import")
    parser.add_argument("--mode", type=str, choices=["smart", "strict"], default="smart", help="Import mode (smart: create candidates, strict: fail on missing)")
    parser.add_argument("--commit", action="store_true", help="Execute the commit phase (write to DB)")
    parser.add_argument("--no-input", action="store_true", help="Skip confirmation prompts")
    
    args = parser.parse_args()
    
    file_path = Path(args.file_path)
    if not file_path.exists():
        print_error(f"File not found: {file_path}")
        sys.exit(1)
        
    print_header("GASTROTECH IMPORT SYSTEM")
    print_info(f"File: {file_path}")
    print_info(f"Mode: {args.mode}")
    print_info(f"Action: {'COMMIT' if args.commit else 'VALIDATE ONLY'}")
    
    # Read file
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        print_success(f"Read {len(file_bytes)} bytes")
    except Exception as e:
        print_error(f"Failed to read file: {e}")
        sys.exit(1)

    # Initialize Service
    service = UnifiedImportService(mode=args.mode)
    
    # Phase 1: Validate
    print_header("PHASE 1: VALIDATION")
    
    try:
        start_time = time.time()
        report = service.validate(file_bytes, file_path.name)
        duration = time.time() - start_time
        
        counts = report.get('counts', {})
        candidates = report.get('candidates', {})
        
        print(f"Status: {report['status']}")
        print(f"Time:   {duration:.2f}s")
        print("-" * 30)
        print(f"Total Rows:   {counts.get('total_rows', 0)}")
        print(f"Valid Rows:   {counts.get('valid_rows', 0)}")
        print(f"Error Rows:   {counts.get('error_rows', 0)}")
        print(f"Warning Rows: {counts.get('warning_rows', 0)}")
        
        if candidates:
            print("-" * 30)
            print("CANDIDATES (to be created):")
            print(f"  Categories: {len(candidates.get('categories', []))}")
            print(f"  Brands:     {len(candidates.get('brands', []))}")
            print(f"  Series:     {len(candidates.get('series', []))}")
            print(f"  Products:   {len(candidates.get('products', []))}")
        
        if report['status'] != 'validation_passed':
            print_header("VALIDATION FAILED")
            errors = [i for i in report.get('issues', []) if i.get('severity') == 'error']
            for err in errors[:10]: # Limit output
                print_error(f"Row {err.get('row', '?')}: {err.get('message')}")
            
            if len(errors) > 10:
                print_warning(f"... and {len(errors) - 10} more errors.")
                
            sys.exit(1)
            
        print_success("Validation Passeed!")

    except Exception as e:
        print_error(f"Validation Exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Check if commit requested
    if not args.commit:
        print_info("Dry-run complete. Use --commit to apply changes.")
        sys.exit(0)
        
    # Confirmation
    if not args.no_input:
        print_warning("You are about to write changes to the database.")
        response = input("Do you want to continue? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print_info("Operation cancelled.")
            sys.exit(0)

    # Phase 2: Commit
    print_header("PHASE 2: COMMIT")
    
    try:
        # Create ImportJob record (required for commit)
        snapshot_info = report.get('snapshot')
        if not snapshot_info:
            print_error("No snapshot found in validation report. Cannot commit.")
            sys.exit(1)
            
        snapshot_media = Media.objects.get(id=snapshot_info['media_id'])
        sanitized_report = sanitize_for_json(report)
        
        job = ImportJob.objects.create(
            kind='catalog_import',
            mode=args.mode,
            report_json=sanitized_report,
            snapshot_file=snapshot_media,
            snapshot_hash=snapshot_info['hash'],
            status='pending',
            created_by_email='cli@gastrotech.local' # Placeholder
        )
        print_info(f"Created ImportJob ID: {job.id}")
        
        # Execute Commit
        start_time = time.time()
        result = service.commit(str(job.id), allow_partial=False)
        duration = time.time() - start_time
        
        if result['status'] == 'success':
            print_success(f"Commit Successful! ({duration:.2f}s)")
            commit_counts = result.get('counts', {})
            print("-" * 30)
            print(f"Products Created: {commit_counts.get('products_created', 0)}")
            print(f"Products Updated: {commit_counts.get('products_updated', 0)}")
            print(f"Variants Created: {commit_counts.get('variants_created', 0)}")
            print(f"Variants Updated: {commit_counts.get('variants_updated', 0)}")
        else:
            print_error(f"Commit Failed: {result['status']}")
            
    except Exception as e:
        print_error(f"Commit Exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
