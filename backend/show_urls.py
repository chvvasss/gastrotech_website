import os
import sys
import django
from django.urls import get_resolver

# Add project root to sys.path
sys.path.append('/app')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

def show_urls(patterns, prefix=""):
    for pattern in patterns:
        if hasattr(pattern, 'url_patterns'):
            # Include
            new_prefix = prefix + str(pattern.pattern)
            show_urls(pattern.url_patterns, new_prefix)
        else:
            # Pattern
            full_url = prefix + str(pattern.pattern)
            if 'import-jobs' in full_url:
                print(f"{full_url}  -> {pattern.name}")

show_urls(get_resolver().url_patterns)
