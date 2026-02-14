
import os
import sys
import django
import json
from django.db import transaction

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.catalog.models import Product, Variant, ProductMedia, Series, Category

PLAN_FILE = '/app/700_series_merge_plan.json'

def run_merge():
    # Load plan (assuming it's copied to /app/ inside docker or mounted)
    # For this execution, I'll write the plan content directly or read from a known location
    # Since I cannot easily pipe the artifact file into the container's filesystem in one go without a copy step
    # I will assume the plan data is available. 
    # To make this script self-contained for the user, I will read from a file path passed as arg or hardcoded.
    
    if not os.path.exists(PLAN_FILE):
        print(f"Plan file not found at {PLAN_FILE}")
        return

    with open(PLAN_FILE, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    # Cache series/category for 700 series (assuming all are consistent)
    # We'll take the first item's metadata to create the parent
    
    with transaction.atomic():
        for group in plan:
            print(f"Processing group: {group['proposed_name']}")
            items = group['items'] # list of {slug, model_code}
            
            if not items:
                continue

            # 1. Get the first product to use as a "template" for the new parent
            first_slug = items[0]['slug']
            template_product = Product.objects.filter(slug=first_slug).first()
            
            if not template_product:
                print(f"  Template product {first_slug} not found, skipping.")
                continue

            # 2. Create the new Parent Product
            # We append "-master" or similar to slug to avoid collision if named same as one of the children?
            # actually proposed_name is different usually.
            
            from django.utils.text import slugify
            new_slug = slugify(group['proposed_name'].replace('700 Serisi', '700 Serisi').replace('(', '').replace(')', '').replace('/', '-'))
            # Ensure slug uniqueness? 
            # If slug exists (rerun?), get it.
            
            parent_product, created = Product.objects.update_or_create(
                slug=new_slug,
                defaults={
                    "name": group['proposed_name'],
                    "title_tr": group['proposed_name'],
                    "series": template_product.series,
                    "category": template_product.category,
                    "brand": template_product.brand,
                    "primary_node": template_product.primary_node,
                    "status": template_product.status,
                    "is_featured": template_product.is_featured,
                    "general_features": template_product.general_features, # Inherit from first
                    "short_specs": template_product.short_specs,
                    "long_description": template_product.long_description,
                    "seo_title": template_product.seo_title, # Should update to generic
                    "seo_description": template_product.seo_description,
                }
            )
            print(f"  {'Created' if created else 'Updated'} parent: {parent_product.name}")

            # 3. Move Variants and ProductMedia
            for item in items:
                child_slug = item['slug']
                child_product = Product.objects.filter(slug=child_slug).first()
                
                if not child_product:
                    print(f"  Child {child_slug} not found.")
                    continue
                
                # Move Variants
                # Each child currently has 1 variant (usually)
                for variant in child_product.variants.all():
                    variant.product = parent_product
                    variant.save()
                    print(f"    Moved variant {variant.model_code}")

                # Move/Link Media
                # The child product has media. We want to move this media to the parent
                # AND link it to the specific variants we just moved.
                # Since we just moved *all* variants of this child, we can link to *all* of them?
                # Usually 1 variant per child product in this flat structure.
                
                child_variants = list(parent_product.variants.filter(model_code=item['model_code'])) 
                # Note: we just moved them, so we filter by model_code to be precise
                
                target_variant = child_variants[0] if child_variants else None

                for pm in child_product.product_media.all():
                    # Move relationship to new product
                    pm.product = parent_product
                    # Link to the variant
                    if target_variant:
                         pm.variant = target_variant
                    pm.save()
                    print(f"    Moved media {pm.media.filename} -> Link to {target_variant.model_code if target_variant else 'None'}")
            
            # 4. Clean up old child products (which correspond to the split items)
            # CAREFUL: Only delete if they are effectively empty now (no variants)
            for item in items:
                child_slug = item['slug']
                child_product = Product.objects.filter(slug=child_slug).first()
                if child_product and child_product.id != parent_product.id:
                    child_product.delete()
                    print(f"  Deleted empty child {child_slug}")

if __name__ == "__main__":
    run_merge()
