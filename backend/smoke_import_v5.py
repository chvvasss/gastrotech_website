#!/usr/bin/env python
"""
V5 Import System Smoke Test Script

This script performs an automated end-to-end smoke test of the V5 import system:
1. Validates fixture can be parsed
2. Runs validate phase
3. Runs commit phase
4. Verifies DB entities were created
5. Generates smoke test report

Usage:
    python scripts/smoke_import_v5.py

Requirements:
    - Django environment configured
    - Database running and migrated
    - Fixture file exists: backend/apps/ops/tests/fixtures/import_v5_smoke.xlsx
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path - detect container vs host
if Path('/app/manage.py').exists():
    # Running in Docker container
    backend_path = Path('/app')
else:
    # Running from host scripts folder
    backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from apps.catalog.models import Category, Series, Brand, Product, Variant
from apps.ops.services.unified_import import UnifiedImportService
from apps.ops.models import ImportJob


class Color:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Print section header."""
    print(f"\n{Color.BOLD}{Color.BLUE}{'='*60}{Color.END}")
    print(f"{Color.BOLD}{Color.BLUE}{text:^60}{Color.END}")
    print(f"{Color.BOLD}{Color.BLUE}{'='*60}{Color.END}\n")


def print_pass(text):
    """Print PASS message."""
    print(f"{Color.GREEN}✓ PASS:{Color.END} {text}")


def print_fail(text):
    """Print FAIL message."""
    print(f"{Color.RED}✗ FAIL:{Color.END} {text}")


def print_info(text):
    """Print INFO message."""
    print(f"{Color.YELLOW}ℹ INFO:{Color.END} {text}")


def run_smoke_test():
    """Execute V5 import smoke test."""
    print_header("V5 IMPORT SYSTEM SMOKE TEST")

    # Test metadata
    start_time = datetime.now()
    results = {
        'timestamp': start_time.isoformat(),
        'tests_run': 0,
        'tests_passed': 0,
        'tests_failed': 0,
        'errors': [],
    }

    # Step 1: Load fixture
    print_header("STEP 1: Load Fixture")
    fixture_path = backend_path / "apps" / "ops" / "tests" / "fixtures" / "import_v5_smoke.xlsx"

    if not fixture_path.exists():
        print_fail(f"Fixture not found: {fixture_path}")
        results['tests_failed'] += 1
        results['errors'].append("Fixture file missing")
        return results

    print_pass(f"Fixture found: {fixture_path}")
    results['tests_run'] += 1
    results['tests_passed'] += 1

    with open(fixture_path, 'rb') as f:
        file_bytes = f.read()

    print_info(f"Fixture size: {len(file_bytes)} bytes")

    # Step 2: Clean database (order matters - respects FK constraints)
    print_header("STEP 2: Clean Database")
    # Delete in reverse dependency order: Variant -> Product -> Series -> Brand -> Category
    Variant.objects.filter(model_code__contains='SMOKE').delete()
    Product.objects.filter(slug__contains='smoke').delete()
    Series.objects.filter(slug__contains='smoke').delete()
    Brand.objects.filter(slug__contains='smoke').delete()
    Category.objects.filter(slug__contains='smoke').delete()
    print_pass("Database cleaned (removed any existing smoke test data)")

    # Step 3: Validate phase
    print_header("STEP 3: Validate Phase (SMART Mode)")
    results['tests_run'] += 1

    service = UnifiedImportService(mode='smart')
    try:
        report = service.validate(file_bytes, 'import_v5_smoke.xlsx')

        if report['status'] != 'validation_passed':
            print_fail(f"Validation failed: {report['status']}")
            results['tests_failed'] += 1
            results['errors'].append(f"Validation status: {report['status']}")

            # Show errors
            errors = [i for i in report.get('issues', []) if i.get('severity') == 'error']
            for err in errors[:5]:  # Show first 5 errors
                print_fail(f"  Row {err.get('row')}, {err.get('column')}: {err.get('message')}")
            return results

        print_pass(f"Validation status: {report['status']}")
        results['tests_passed'] += 1

        # Check counts
        counts = report.get('counts', {})
        print_info(f"Total product rows: {counts.get('total_product_rows', 0)}")
        print_info(f"Total variant rows: {counts.get('total_variant_rows', 0)}")
        print_info(f"Valid product rows: {counts.get('valid_product_rows', 0)}")
        print_info(f"Valid variant rows: {counts.get('valid_variant_rows', 0)}")

        # Check candidates
        candidates = report.get('candidates', {})
        cat_count = len(candidates.get('categories', []))
        brand_count = len(candidates.get('brands', []))
        series_count = len(candidates.get('series', []))

        print_info(f"Candidates: {cat_count} categories, {brand_count} brands, {series_count} series")

        # Snapshot check
        results['tests_run'] += 1
        if 'snapshot' in report:
            print_pass(f"Snapshot created: {report['snapshot']['hash'][:16]}...")
            results['tests_passed'] += 1
        else:
            print_fail("Snapshot not created")
            results['tests_failed'] += 1
            results['errors'].append("Missing snapshot")

    except Exception as e:
        print_fail(f"Validation exception: {e}")
        results['tests_failed'] += 1
        results['errors'].append(f"Validation exception: {str(e)}")
        return results

    # Step 4: Create ImportJob and commit
    print_header("STEP 4: Commit Phase")
    results['tests_run'] += 1

    try:
        # Create ImportJob with snapshot
        from apps.catalog.models import Media
        from decimal import Decimal
        import json
        snapshot_info = report['snapshot']
        snapshot_media = Media.objects.get(id=snapshot_info['media_id'])

        # Sanitize report for JSONField (convert Decimals to strings)
        def sanitize_for_json(obj):
            if isinstance(obj, Decimal):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: sanitize_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize_for_json(item) for item in obj]
            return obj

        sanitized_report = sanitize_for_json(report)

        job = ImportJob.objects.create(
            kind='catalog_import',
            mode='smart',
            report_json=sanitized_report,
            snapshot_file=snapshot_media,
            snapshot_hash=snapshot_info['hash'],
            status='pending',
        )

        print_info(f"ImportJob created: {job.id}")

        # Commit
        commit_result = service.commit(str(job.id), allow_partial=False)

        if commit_result['status'] != 'success':
            print_fail(f"Commit failed: {commit_result['status']}")
            results['tests_failed'] += 1
            results['errors'].append(f"Commit status: {commit_result['status']}")
            return results

        print_pass(f"Commit status: {commit_result['status']}")
        results['tests_passed'] += 1

        # Check counts
        commit_counts = commit_result.get('counts', {})
        print_info(f"Categories created: {commit_counts.get('categories_created', 0)}")
        print_info(f"Brands created: {commit_counts.get('brands_created', 0)}")
        print_info(f"Series created: {commit_counts.get('series_created', 0)}")
        print_info(f"Products created: {commit_counts.get('products_created', 0)}")
        print_info(f"Variants created: {commit_counts.get('variants_created', 0)}")

        # Check db_verify
        results['tests_run'] += 1
        db_verify = commit_result.get('db_verify', {})

        if not db_verify:
            print_fail("db_verify missing from commit response")
            results['tests_failed'] += 1
            results['errors'].append("db_verify missing")
            return results

        if not db_verify.get('created_entities_found_in_db'):
            print_fail("db_verify.created_entities_found_in_db is FALSE")
            results['tests_failed'] += 1
            results['errors'].append("DB verification failed")

            # Show verification details
            details = db_verify.get('verification_details', {})
            for entity_type, verified in details.items():
                status = "✓" if verified else "✗"
                print(f"  {status} {entity_type}")
            return results

        print_pass("db_verify.created_entities_found_in_db is TRUE")
        results['tests_passed'] += 1

    except Exception as e:
        print_fail(f"Commit exception: {e}")
        results['tests_failed'] += 1
        results['errors'].append(f"Commit exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return results

    # Step 5: Verify DB entities
    print_header("STEP 5: Verify DB Entities")

    # Check category
    results['tests_run'] += 1
    try:
        category = Category.objects.get(slug='electronics-smoke')
        print_pass(f"Category found: {category.slug} (name={category.name})")
        results['tests_passed'] += 1
    except Category.DoesNotExist:
        print_fail("Category 'electronics-smoke' not found in DB")
        results['tests_failed'] += 1
        results['errors'].append("Category not in DB")

    # Check brand
    results['tests_run'] += 1
    try:
        brand = Brand.objects.get(slug='acme-smoke')
        print_pass(f"Brand found: {brand.slug} (name={brand.name})")
        results['tests_passed'] += 1
    except Brand.DoesNotExist:
        print_fail("Brand 'acme-smoke' not found in DB")
        results['tests_failed'] += 1
        results['errors'].append("Brand not in DB")

    # Check series
    results['tests_run'] += 1
    try:
        series = Series.objects.get(slug='test-series-smoke')
        print_pass(f"Series found: {series.slug} (name={series.name}, category={series.category.slug})")
        results['tests_passed'] += 1
    except Series.DoesNotExist:
        print_fail("Series 'test-series-smoke' not found in DB")
        results['tests_failed'] += 1
        results['errors'].append("Series not in DB")

    # Check product
    results['tests_run'] += 1
    try:
        product = Product.objects.get(slug='smoke-test-product')
        print_pass(f"Product found: {product.slug} (name={product.name}, status={product.status})")
        results['tests_passed'] += 1

        # Verify status default
        results['tests_run'] += 1
        if product.status == 'active':
            print_pass(f"Product status is 'active' (correct V5 default)")
            results['tests_passed'] += 1
        else:
            print_fail(f"Product status is '{product.status}' (expected 'active')")
            results['tests_failed'] += 1
            results['errors'].append(f"Status not 'active': {product.status}")

    except Product.DoesNotExist:
        print_fail("Product 'smoke-test-product' not found in DB")
        results['tests_failed'] += 1
        results['errors'].append("Product not in DB")

    # Check variant
    results['tests_run'] += 1
    try:
        variant = Variant.objects.get(model_code='SMOKE-001')
        print_pass(f"Variant found: {variant.model_code} (name_tr={variant.name_tr})")
        results['tests_passed'] += 1

        # Verify variant name default
        results['tests_run'] += 1
        if variant.name_tr == 'Smoke Test Ürün':
            print_pass(f"Variant name_tr defaulted to Product.title_tr (V5 contract)")
            results['tests_passed'] += 1
        else:
            print_fail(f"Variant name_tr is '{variant.name_tr}' (expected 'Smoke Test Ürün')")
            results['tests_failed'] += 1
            results['errors'].append(f"Variant name_tr incorrect: {variant.name_tr}")

    except Variant.DoesNotExist:
        print_fail("Variant 'SMOKE-001' not found in DB")
        results['tests_failed'] += 1
        results['errors'].append("Variant not in DB")

    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print_header("SMOKE TEST SUMMARY")
    print(f"Tests Run:    {results['tests_run']}")
    print(f"Tests Passed: {Color.GREEN}{results['tests_passed']}{Color.END}")
    print(f"Tests Failed: {Color.RED if results['tests_failed'] > 0 else Color.GREEN}{results['tests_failed']}{Color.END}")
    print(f"Duration:     {duration:.2f}s")

    if results['tests_failed'] == 0:
        print(f"\n{Color.GREEN}{Color.BOLD}✓✓✓ ALL TESTS PASSED ✓✓✓{Color.END}")
        results['overall_status'] = 'PASS'
    else:
        print(f"\n{Color.RED}{Color.BOLD}✗✗✗ TESTS FAILED ✗✗✗{Color.END}")
        print(f"\nErrors:")
        for err in results['errors']:
            print(f"  - {err}")
        results['overall_status'] = 'FAIL'

    return results


if __name__ == '__main__':
    try:
        results = run_smoke_test()

        # Write report
        report_path = backend_path / "SMOKE_TEST_REPORT.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# V5 Import Smoke Test Report\n\n")
            f.write(f"**Timestamp**: {results['timestamp']}\n")
            f.write(f"**Overall Status**: {results['overall_status']}\n\n")
            f.write(f"## Results\n\n")
            f.write(f"- Tests Run: {results['tests_run']}\n")
            f.write(f"- Tests Passed: {results['tests_passed']}\n")
            f.write(f"- Tests Failed: {results['tests_failed']}\n\n")

            if results['errors']:
                f.write(f"## Errors\n\n")
                for err in results['errors']:
                    f.write(f"- {err}\n")

            f.write(f"\n---\n\n")
            f.write(f"Generated by: `scripts/smoke_import_v5.py`\n")

        print(f"\nReport written to: {report_path}")

        # Exit code
        sys.exit(0 if results['tests_failed'] == 0 else 1)

    except Exception as e:
        print_fail(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
