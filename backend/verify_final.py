from apps.catalog.models import Category

def check_category(slug, expected_children):
    try:
        cat = Category.objects.get(slug=slug)
        children_count = cat.children.count()
        print(f"CATEGORY: {cat.name} ({slug})")
        print(f"  Children count: {children_count}")
        
        children = list(cat.children.all())
        found_children = [c.name for c in children]
        print(f"  Found children: {found_children}")
        
        for child in children:
            lgs = child.logo_groups.count()
            print(f"    - {child.name}: {lgs} logo groups")
            
    except Category.DoesNotExist:
        print(f"ERROR: Category {slug} NOT FOUND")

print("--- FINAL VERIFICATION ---")
check_category('firinlar', 5)
check_category('sogutma-uniteleri', 2)
check_category('hazirlik-ekipmanlari', 5)
print("--- END ---")
