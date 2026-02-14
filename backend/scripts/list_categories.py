
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
    cats = Category.objects.all().order_by('slug')
    print(f"Found {cats.count()} categories:")
    for c in cats:
        print(f"  {c.slug} | {c.name}")

if __name__ == "__main__":
    run()
