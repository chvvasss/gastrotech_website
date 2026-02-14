
import os
import sys
import django

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Media

def check_orphans():
    print("--- Checking Remaining Orphan Images ---")
    
    # Filter for media that has NO relationship in ProductMedia
    # Note: We should filter for 'image' kind to be specific, though user said "visuals"
    orphans = Media.objects.filter(
        media_products__isnull=True, 
        kind='image'
    )
    
    count = orphans.count()
    print(f"Total Orphan Images: {count}")
    
    if count > 0:
        print("\nSample Orphan Files (First 50):")
        print("-" * 50)
        for m in orphans.order_by('-created_at')[:50]:
            print(f"- {m.filename} (Created: {m.created_at.strftime('%Y-%m-%d %H:%M')})")
        
        if count > 50:
            print(f"\n... and {count - 50} more.")

if __name__ == "__main__":
    check_orphans()
