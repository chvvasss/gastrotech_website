from django.core.management.base import BaseCommand
from apps.catalog.models import Product, Variant, SpecKey
from apps.common.slugify_tr import slugify_tr

class Command(BaseCommand):
    help = 'Syncs existing Spec Keys from JSON data to SpecKey table'

    def handle(self, *args, **options):
        # 1. Collect all used keys from Product.spec_layout
        layout_keys = set()
        for p in Product.objects.all():
            if p.spec_layout:
                layout_keys.update(p.spec_layout)
        
        # 2. Collect all used keys from Variant.specs
        variant_keys = set()
        for v in Variant.objects.iterator():
            if v.specs:
                variant_keys.update(v.specs.keys())
        
        all_slugs = layout_keys.union(variant_keys)
        self.stdout.write(f"Found {len(all_slugs)} unique keys in existing data.")
        
        created_count = 0
        for slug in all_slugs:
            # Skip empty or invalid slugs
            if not slug or not slug.strip():
                continue
                
            # Try to infer a nice label from the slug
            # e.g. 'electric_power' -> 'Electric Power' (approximate)
            # Better: if we had a mapping... but we don't.
            # We will use the slug as label initially, user can edit later.
            label = slug.replace('_', ' ').replace('-', ' ').title()
            
            # Create if not exists
            obj, created = SpecKey.objects.get_or_create(
                slug=slug,
                defaults={
                    'label_tr': label,
                    'value_type': 'text', # Default to text
                    'sort_order': 999
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"Created SpecKey: {slug} ({label})")
        
        self.stdout.write(self.style.SUCCESS(f"Done. Created {created_count} new SpecKeys."))
