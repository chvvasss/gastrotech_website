#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.catalog.models import Brand, Media

# Check VITAL brand
try:
    vital = Brand.objects.get(slug='vital')
    print(f"VITAL Brand found: {vital.name}")
    print(f"Logo media ID: {vital.logo_media_id}")
    
    if vital.logo_media_id:
        # Get media with bytes
        media = Media.objects.get(id=vital.logo_media_id)
        print(f"Media ID: {media.id}")
        print(f"Media filename: {media.filename}")
        print(f"Media kind: {media.kind}")
        print(f"Media content_type: {media.content_type}")
        print(f"Media size_bytes: {media.size_bytes}")
        print(f"Has bytes: {media.bytes is not None}")
        print(f"Bytes length: {len(media.bytes) if media.bytes else 0}")
    else:
        print("No logo_media_id associated with VITAL brand")
except Brand.DoesNotExist:
    print("VITAL brand not found!")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error: {e}")
