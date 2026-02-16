import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ["DATABASE_URL"] = "postgres://postgres:postgres@localhost:5432/gastrotech"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from apps.catalog.models import Media

def run():
    print("=== Verifying Media Bytes ===\n")
    
    # Check a file we know was restored/imported
    target_filename = "VBY3600R_2.png"
    media = Media.objects.filter(filename=target_filename).first()
    
    if media:
        print(f"File: {media.filename}")
        print(f"ID: {media.id}")
        size = len(media.bytes) if media.bytes else 0
        print(f"Bytes Length: {size}")
        print(f"Content Type: {media.content_type}")
        
        if size > 0:
            print("Bytes found! dumping first 20 bytes:")
            print(media.bytes[:20])
        else:
            print("ERROR: No bytes found in DB!")
    else:
        print(f"Media '{target_filename}' not found in DB.")

    # Check random restored file from Mutas
    print("\n--- Checking random restored file ---")
    random_media = Media.objects.exclude(bytes=b'').first()
    if random_media:
        print(f"File: {random_media.filename}")
        print(f"Size: {len(random_media.bytes)}")
    else:
        print("No media with bytes found.")

if __name__ == "__main__":
    run()
