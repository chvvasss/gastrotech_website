"""
Check if media IDs from error exist in database.
"""

import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.catalog.models import Media


def check_media():
    """Check if specific media IDs exist."""
    
    # IDs from the error log
    missing_ids = [
        '39174945-00fa-4190-bf1f-b9d87dea5e59',
        '84df2363-4316-46af-8f44-64b234675c27',
        '8ed798a2-675d-4adb-8282-fcd10146ded0',
    ]
    
    print("\n" + "="*60)
    print("CHECKING MEDIA IDS FROM 404 ERRORS")
    print("="*60 + "\n")
    
    for media_id in missing_ids:
        try:
            media = Media.objects.get(id=media_id)
            print(f"[OK] {media_id}: FOUND")
            print(f"  Filename: {media.filename}")
            print(f"  Kind: {media.kind}")
            print(f"  Size: {media.size_bytes} bytes")
            print(f"  Has bytes: {media.bytes is not None and len(media.bytes) > 0}")
            print()
        except Media.DoesNotExist:
            print(f"[FAIL] {media_id}: NOT FOUND IN DATABASE")
            print()
    
    # Also check total media count
    total = Media.objects.count()
    images = Media.objects.filter(kind='image').count()
    print(f"Total media in DB: {total}")
    print(f"  Images: {images}")
    print()


if __name__ == '__main__':
    check_media()
