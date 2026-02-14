
import os
import sys
import django

# Setup Django
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.catalog.models import Variant, ProductMedia

def verify_variant(code):
    print(f"Checking {code}...")
    v = Variant.objects.filter(model_code=code).first()
    if v:
        print(f"  Variant Found: {v.model_code}")
        print(f"  Product: {v.product.name} (ID: {v.product.id})")
        pms = ProductMedia.objects.filter(product=v.product)
        print(f"  Media Count: {pms.count()}")
        for pm in pms:
            print(f"    - {pm.media.filename} | Primary: {pm.is_primary} | Sort: {pm.sort_order}")
    else:
        print(f"  Variant {code} NOT FOUND")

if __name__ == "__main__":
    verify_variant('VBY500C')
    verify_variant('ESI7030')
