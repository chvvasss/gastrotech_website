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
    print("=== Verification of Media Fix ===\n")
    empty_count = Media.objects.filter(Q(bytes=None) | Q(bytes=b'')).count()
    print(f"Remaining Empty Media: {empty_count}")
    
    if empty_count == 0:
        print("SUCCESS: All broken media records are gone.")
    else:
        print(f"FAILURE: {empty_count} broken media records remain.")

if __name__ == "__main__":
    run()
