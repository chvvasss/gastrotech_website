"""Quick script to check DB status for images and PDFs."""
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from apps.catalog.models import Media, ProductMedia, Product, CategoryCatalog, Variant

print("=== DB STATUS ===")
print(f"Total Media: {Media.objects.count()}")
print(f"Image Media: {Media.objects.filter(kind='image').count()}")
print(f"Document Media: {Media.objects.filter(kind='document').count()}")

empty_bytes = 0
for m in Media.objects.all().only('id', 'bytes'):
    if not m.bytes or len(m.bytes) == 0:
        empty_bytes += 1
print(f"Empty bytes Media: {empty_bytes}")

print(f"Total Products: {Product.objects.count()}")
products_with_img = Product.objects.filter(product_media__isnull=False).distinct().count()
products_without_img = Product.objects.filter(product_media__isnull=True).distinct().count()
print(f"Products with images: {products_with_img}")
print(f"Products without images: {products_without_img}")
print(f"Total ProductMedia links: {ProductMedia.objects.count()}")
print(f"CategoryCatalog entries: {CategoryCatalog.objects.count()}")
print(f"Total Variants: {Variant.objects.count()}")

print("\n=== DOCUMENT MEDIA (PDFs) ===")
docs = Media.objects.filter(kind='document')
if docs.exists():
    for d in docs:
        blen = len(d.bytes) if d.bytes else 0
        print(f"  {d.filename}: bytes_len={blen}, size_bytes={d.size_bytes}")
else:
    print("  NO DOCUMENT MEDIA FOUND - PDFs are missing!")

print("\n=== CATEGORY CATALOGS ===")
for cc in CategoryCatalog.objects.select_related('category', 'media').all():
    media_status = "OK" if cc.media and cc.media.bytes and len(cc.media.bytes) > 0 else "BROKEN/MISSING"
    print(f"  {cc.title_tr} -> cat={cc.category.slug if cc.category else 'NONE'}, media={cc.media.filename if cc.media else 'NONE'} [{media_status}]")

print("\n=== PRODUCTS WITHOUT IMAGES (first 30) ===")
no_img = Product.objects.filter(product_media__isnull=True).values_list('name', 'slug')[:30]
for name, slug in no_img:
    print(f"  {name} (slug={slug})")
