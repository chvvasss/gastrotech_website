
import os
import sys
from pathlib import Path
from django.db.models import Q

sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ["DATABASE_URL"] = "postgres://postgres:postgres@localhost:5432/gastrotech"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from apps.catalog.models import Media

def run():
    total = Media.objects.count()
    # Check for non-empty bytes using regex or length if supported, but here we can just check if not null
    # BinaryField behavior depends on DB, but usually empty string or None.
    # We can use exclude(bytes=b'')
    
    with_bytes = Media.objects.exclude(bytes=b'').count()
    empty = total - with_bytes
    
    print(f"Total Media: {total}")
    print(f"With Bytes: {with_bytes}")
    print(f"Empty: {empty}")
    print(f"Progress: {with_bytes/total*100:.1f}%")

if __name__ == "__main__":
    run()
