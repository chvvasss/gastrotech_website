
import os
import sys
import django

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Category, Product

def debug_hazirlik():
    slug = 'hazirlik-ekipmanlari'
    try:
        cat = Category.objects.get(slug=slug)
    except Category.DoesNotExist:
        print(f"Category '{slug}' not found!")
        return

    print(f"--- Category: {cat.name} ({cat.slug}) ---")
    print(f"ID: {cat.id}")
    print(f"Parent: {cat.parent}")

    # Inspect descendants
    # Try to determine if get_descendants returns a list or queryset
    if hasattr(cat, 'get_descendants'):
        descendants = cat.get_descendants(include_self=True)
        is_queryset = hasattr(descendants, 'count') and callable(getattr(descendants, 'count')) and not isinstance(descendants, list)
        
        if is_queryset:
            count = descendants.count()
            print(f"Descendants (QuerySet): {count}")
            descendant_ids = list(descendants.values_list('id', flat=True))
        else:
            # It is likely a list
            count = len(descendants)
            print(f"Descendants (List): {count}")
            descendant_ids = [d.id for d in descendants]
            
        # Print subcategory names
        for d in descendants:
            if d.id != cat.id:
                print(f"  - Subcat: {d.name} ({d.slug}) [Products: {d.products.count() if hasattr(d, 'products') else '?'}]")
    else:
        print("No get_descendants method found. Using recursive search or direct children if necessary.")
        descendant_ids = [cat.id]

    print("\n--- Product Counts ---")
    
    # Products directly in these categories
    all_products = Product.objects.filter(category__id__in=descendant_ids)
    print(f"Total Products in hierarchy: {all_products.count()}")
    
    # Breakdown by status
    print("Status Breakdown:")
    statuses = all_products.values('status').annotate(count=django.db.models.Count('status'))
    for s in statuses:
        print(f"  {s['status']}: {s['count']}")

    # Check for products linked via Series in these categories
    print("\n--- Series Products ---")
    series_products = Product.objects.filter(series__category__id__in=descendant_ids)
    print(f"Products linked via Series in hierarchy: {series_products.count()}")
    
    series_statuses = series_products.values('status').annotate(count=django.db.models.Count('status'))
    for s in series_statuses:
        print(f"  {s['status']}: {s['count']}")

if __name__ == "__main__":
    debug_hazirlik()
