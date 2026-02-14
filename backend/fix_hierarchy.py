
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

def fix_hierarchy():
    try:
        firinlar = Category.objects.get(slug='firinlar')
        if firinlar.parent:
            print(f"Detaching '{firinlar.name}' from parent '{firinlar.parent.name}'...")
            firinlar.parent = None
            firinlar.save()
            print("Successfully updated. 'Fırınlar' is now a root category.")
        else:
            print("'Fırınlar' is already a root category.")
            
    except Category.DoesNotExist:
        print("Category 'firinlar' not found.")

if __name__ == "__main__":
    fix_hierarchy()
