
import os
import sys
import django

# Add backend to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
try:
    django.setup()
except Exception as e:
    print(f"Setup failed: {e}")
    sys.exit(1)

from apps.catalog.models import Category

def inspect_hierarchy():
    try:
        firinlar = Category.objects.get(slug='firinlar')
        print(f"Category: {firinlar.name} ({firinlar.slug})")
        print(f"  Parent: {firinlar.parent.name if firinlar.parent else 'None'}")
        
        if firinlar.parent:
            parent = firinlar.parent
            print(f"  Parent Slug: {parent.slug}")
            siblings = Category.objects.filter(parent=parent).exclude(id=firinlar.id)
            print(f"  Siblings ({len(siblings)}):")
            for s in siblings:
                print(f"    - {s.name} ({s.slug})")

        print(f"-" * 20)
        
        # Check 'pisirme-ekipmanlari' children
        try:
            pisirme = Category.objects.get(slug='pisirme-ekipmanlari')
            children = Category.objects.filter(parent=pisirme)
            print(f"Category: {pisirme.name} ({pisirme.slug})")
            print(f"  Children ({len(children)}):")
            for c in children:
                print(f"    - {c.name} ({c.slug})")
        except Category.DoesNotExist:
            print("Category 'pisirme-ekipmanlari' not found.")
            
    except Category.DoesNotExist:
        print("Category 'firinlar' not found.")

if __name__ == "__main__":
    inspect_hierarchy()
