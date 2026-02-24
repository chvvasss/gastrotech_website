import django
import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
try:
    django.setup()
except Exception as e:
    print(f"Setup Error: {e}")
    sys.exit(1)

from django.contrib.contenttypes.models import ContentType

print(f"Django Version: {django.get_version()}")
try:
    fields = [f.name for f in ContentType._meta.get_fields()]
    print(f"ContentType Fields: {fields}")
    
    print(f"Query SQL: {ContentType.objects.all().query}")
    print(f"Count: {ContentType.objects.count()}")
    
    print("Attempting to create all content types...")
    from django.contrib.contenttypes.management import create_contenttypes
    from django.apps import apps
    
    for app_config in apps.get_app_configs():
        create_contenttypes(app_config, verbosity=0, interactive=False)
    
    print(f"Count after all: {ContentType.objects.count()}")
except Exception as e:
    print(f"Field/Query Error: {e}")


