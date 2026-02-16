import os
import sys
from pathlib import Path
from django.db.models import Q, Count, F, Func, Value, IntegerField

sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ["DATABASE_URL"] = "postgres://postgres:postgres@localhost:5432/gastrotech"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from apps.catalog.models import Media, Product, ProductMedia

def run():
    print("=== Media Health Analysis ===\n")
    
    # 1. Count Media with empty bytes
    empty_media_count = Media.objects.filter(Q(bytes=None) | Q(bytes=b'')).count()
    total_media = Media.objects.count()
    print(f"Total Media: {total_media}")
    print(f"Empty Media (Missing Bytes): {empty_media_count}")
    
    # 2. Count Active Products with Empty Primary Image
    print("\nAnalyzing Active Products...")
    
    # Identify empty media IDs first (efficient)
    empty_media_qs = Media.objects.filter(Q(bytes=None) | Q(bytes=b''))
    
    # Find ProductMedia items that rely on these empty media
    # We want to know which Active Products have a *Primary* image that is empty.
    
    # Approach: 
    # Find ProductMedia where:
    # - media is in empty_media_qs
    # - is_primary = True
    # - product is active
    
    broken_primary_pms = ProductMedia.objects.filter(
        media__in=empty_media_qs,
        is_primary=True,
        product__status='active'
    ).select_related('product', 'media').defer('media__bytes')
    
    count = broken_primary_pms.count()
    print(f"Active Products with BROKEN Primary Image: {count}")
    
    if count > 0:
        print("\nTop 10 Affected Products:")
        for pm in broken_primary_pms[:10]:
             print(f"- {pm.product.title_tr} ({pm.product.slug}) -> Media: {pm.media.filename}")
            
    # 3. Suggest Fix
    print("\nRecommendation:")
    print("These empty media files cause broken images on the frontend.")
    print("Action: Unlink these empty media objects from Products so they fall back to 'No Image' or secondary images.")

if __name__ == "__main__":
    run()
