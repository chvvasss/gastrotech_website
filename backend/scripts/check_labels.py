import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import Category

def run():
    print(f"{'Slug':<30} | {'Name':<35} | {'Menu Label':<35}")
    print("-" * 105)
    
    for cat in Category.objects.all().order_by('slug'):
        print(f"{cat.slug:<30} | {cat.name:<35} | {str(cat.menu_label):<35}")

if __name__ == "__main__":
    run()
