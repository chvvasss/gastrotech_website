"""
Management command to fix product categories based on JSON source files.

Usage:
    python manage.py fix_product_categories --json-file=../ceysonlar/catalog_bundle_final_v1.json --target-categories=firinlar --dry-run
    python manage.py fix_product_categories --json-file=../ceysonlar/catalog_bundle_final_v1.json --target-categories=firinlar --execute
"""

import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.catalog.models import Product, Category, Series
from apps.catalog.cache_keys import clear_nav_cache


class Command(BaseCommand):
    help = 'Fix product categories based on JSON source files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json-file',
            type=str,
            required=True,
            help='Path to JSON source file'
        )
        parser.add_argument(
            '--target-categories',
            type=str,
            default='firinlar',
            help='Comma-separated list of categories to fix (default: firinlar)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show changes without applying them'
        )
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Execute the changes'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']
        target_categories = [cat.strip() for cat in options['target_categories'].split(',')]
        dry_run = options['dry_run']
        execute = options['execute']

        if not dry_run and not execute:
            raise CommandError('You must specify either --dry-run or --execute')

        if dry_run and execute:
            raise CommandError('Cannot use both --dry-run and --execute')

        # Read JSON file
        if not os.path.exists(json_file):
            raise CommandError(f'JSON file not found: {json_file}')

        self.stdout.write('=' * 80)
        self.stdout.write(f'Reading JSON file: {json_file}')
        
        with open(json_file, 'r', encoding='utf-8') as f:
            products_json = json.load(f)

        self.stdout.write(f'Loaded {len(products_json)} products from JSON')
        self.stdout.write(f'Target categories: {", ".join(target_categories)}')
        self.stdout.write('=' * 80)

        # Collect changes
        changes = []
        errors = []
        
        target_category_count = 0  # DEBUG: Track how many JSON products match target categories

        for product_data in products_json:
            json_category = product_data.get('category', '').strip()
            
            if not json_category or json_category not in target_categories:
                continue
            
            target_category_count += 1  # DEBUG: Increment counter

            slug = product_data.get('slug')
            if not slug:
                errors.append(f'Product missing slug: {product_data.get("name", "UNKNOWN")}')
                continue

            # Find product in database
            try:
                product = Product.objects.select_related('category', 'series', 'series__category').get(slug=slug)
            except Product.DoesNotExist:
                errors.append(f'Product not found in database: {slug}')
                continue

            # Find target category
            try:
                target_cat = Category.objects.get(slug=json_category)
            except Category.DoesNotExist:
                errors.append(f'Category not found: {json_category}')
                continue

            # Check if product needs update
            product_needs_update = product.category_id != target_cat.id
            series_needs_update = product.series and product.series.category_id != target_cat.id

            if product_needs_update or series_needs_update:
                changes.append({
                    'product': product,
                    'slug': slug,
                    'name': product.title_tr or product.name,
                    'current_category': product.category.slug if product.category else 'NULL',
                    'target_category': target_cat.slug,
                    'product_needs_update': product_needs_update,
                    'series': product.series,
                    'series_current_category': product.series.category.slug if product.series and product.series.category else 'NULL',
                    'series_needs_update': series_needs_update,
                    'target_cat_obj': target_cat,
                })

        # Display results
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(f'DEBUG: Found {target_category_count} products in JSON matching target categories')
        self.stdout.write(f'DEBUG: Errors encountered: {len(errors)}')
        self.stdout.write(f'DEBUG: Changes to apply: {len(changes)}')
        self.stdout.write('=' * 80)
        
        if errors:
            self.stdout.write(self.style.WARNING(f'ERRORS ({len(errors)}):'))
            for error in errors[:10]:  # Show first 10 errors only
                self.stdout.write(self.style.WARNING(f'  - {error}'))
            if len(errors) > 10:
                self.stdout.write(self.style.WARNING(f'  ... and {len(errors) - 10} more errors'))
            self.stdout.write('')

        if not changes:
            self.stdout.write(self.style.SUCCESS('No changes needed!'))
            self.stdout.write('=' * 80)
            return

        self.stdout.write(self.style.WARNING(f'CHANGES TO APPLY ({len(changes)}):'))
        self.stdout.write('')

        for idx, change in enumerate(changes, 1):
            self.stdout.write(f'{idx}. {change["name"]} ({change["slug"]})')
            if change['product_needs_update']:
                self.stdout.write(f'   Product category: {change["current_category"]} -> {change["target_category"]}')
            if change['series_needs_update']:
                series_name = change['series'].name if change['series'] else 'UNKNOWN'
                self.stdout.write(f'   Series category: {series_name} ({change["series_current_category"]} -> {change["target_category"]})')

        self.stdout.write('\n' + '=' * 80)

        if dry_run:
            self.stdout.write(self.style.SUCCESS('DRY RUN - No changes applied'))
            self.stdout.write('To apply changes, run with --execute')
        else:
            # Execute changes
            self.stdout.write(self.style.WARNING('EXECUTING CHANGES...'))
            
            with transaction.atomic():
                updated_products = 0
                updated_series = set()

                for change in changes:
                    if change['product_needs_update']:
                        change['product'].category = change['target_cat_obj']
                        change['product'].save(update_fields=['category'])
                        updated_products += 1

                    if change['series_needs_update']:
                        change['series'].category = change['target_cat_obj']
                        change['series'].save(update_fields=['category'])
                        updated_series.add(change['series'].id)

            self.stdout.write(self.style.SUCCESS(f'Updated {updated_products} products'))
            self.stdout.write(self.style.SUCCESS(f'Updated {len(updated_series)} series'))

            # Clear navigation cache
            self.stdout.write('Clearing navigation cache...')
            clear_nav_cache()
            
            self.stdout.write(self.style.SUCCESS('CHANGES APPLIED SUCCESSFULLY!'))

        self.stdout.write('=' * 80)
