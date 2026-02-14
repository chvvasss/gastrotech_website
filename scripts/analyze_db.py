
import os
import sys
import django
from django.db.models import Count, F
from collections import defaultdict

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import Category, Series, Product, Brand, TaxonomyNode
from apps.common.slugify_tr import slugify_tr

def analyze():
    print("--- STARTING ANALYSIS ---\n")

    # 1. Series with 0 or 1 Product
    print("\n--- 1. SERIES PRODUCT COUNTS ---")
    series_qs = Series.objects.annotate(
        real_product_count=Count('products')
    )
    
    empty_series = []
    single_product_series = []
    
    for s in series_qs:
        if s.real_product_count == 0:
            empty_series.append(s)
        elif s.real_product_count == 1:
            single_product_series.append(s)

    print(f"Total Series: {series_qs.count()}")
    print(f"Empty Series (0 products): {len(empty_series)}")
    for s in empty_series:
        print(f"  - [EMPTY] {s.category.name} > {s.name} (Slug: {s.slug})")

    print(f"Single Product Series (1 product): {len(single_product_series)}")
    for s in single_product_series:
        prod = s.products.first()
        print(f"  - [SINGLE] {s.category.name} > {s.name} (Slug: {s.slug}) -> Product: {prod.name} (Slug: {prod.slug})")

    # 2. Slug Consistency
    print("\n--- 2. SLUG CONSISTENCY CHECKS ---")
    
    def check_slug(model, obj, name_field='name'):
        name_val = getattr(obj, name_field)
        expected = slugify_tr(name_val)
        if obj.slug != expected:
            # Sometimes slugs have -1, -2 etc. or are customized. We just report mismatches.
            return f"Mismatch: {obj} (ID: {obj.id})\n    Name: {name_val}\n    Slug: {obj.slug}\n    Expected: {expected}"
        return None

    mismatches = []
    for c in Category.objects.all():
        err = check_slug(Category, c)
        if err: mismatches.append(err)
    
    for s in Series.objects.all():
        err = check_slug(Series, s)
        if err: mismatches.append(err)
        
    for p in Product.objects.all():
        err = check_slug(Product, p)
        # Products can have custom slugs more often, but worth checking
        if err and not p.slug.startswith(slugify_tr(p.name)): # gentle check
             mismatches.append(err)

    if mismatches:
        print(f"Found {len(mismatches)} potential slug inconsistencies (showing first 10):")
        for m in mismatches[:10]:
            print(m)
    else:
        print("No obvious slug inconsistencies found.")

    # 3. Relationship Integrity
    print("\n--- 3. RELATIONSHIP INTEGRITY ---")
    # Check if Product.primary_node.series == Product.series
    
    node_mismatches = []
    for p in Product.objects.select_related('series', 'primary_node', 'primary_node__series'):
        if p.primary_node:
            if p.primary_node.series_id != p.series_id:
                node_mismatches.append(
                    f"Product {p.slug} has Series '{p.series.name}' but Primary Node '{p.primary_node.name}' belongs to Series '{p.primary_node.series.name}'"
                )
    
    if node_mismatches:
        print(f"Found {len(node_mismatches)} Product-Node-Series mismatches:")
        for m in node_mismatches:
            print(m)
    else:
        print("Product -> Primary Node -> Series relationships are consistent.")

    # 4. Check for Duplicate Slugs (Global collision check usually enforced by DB, but logic check)
    print("\n--- 4. DUPLICATE SLUG CHECK ---")
    # Series slugs are unique per Category.
    # Products are globally unique.
    
    dup_slugs = Product.objects.values('slug').annotate(count=Count('id')).filter(count__gt=1)
    if dup_slugs.exists():
        print(f"CRITICAL: Found duplicate product slugs: {list(dup_slugs)}")
    else:
        print("No duplicate product slugs found.")

    print("\n--- END ANALYSIS ---")

if __name__ == "__main__":
    analyze()
