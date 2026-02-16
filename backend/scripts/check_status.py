"""Check DB status - run via: Get-Content scripts/check_status.py | python manage.py shell"""
from apps.catalog.models import Media, ProductMedia, Product, CategoryCatalog, Variant

print("=== DB STATUS ===")
print(f"Total Media: {Media.objects.count()}")
print(f"Image Media: {Media.objects.filter(kind='image').count()}")
print(f"Document Media: {Media.objects.filter(kind='document').count()}")
print(f"Products: {Product.objects.count()}")
print(f"Variants: {Variant.objects.count()}")
print(f"ProductMedia links: {ProductMedia.objects.count()}")
print(f"CategoryCatalog links: {CategoryCatalog.objects.count()}")

prods_with_img = Product.objects.filter(product_media__media__kind='image').distinct().count()
prods_total = Product.objects.count()
print(f"Products WITH images: {prods_with_img}")
print(f"Products WITHOUT images: {prods_total - prods_with_img}")

# Check PDF status
print("\n=== CATALOG PDFs ===")
cats = CategoryCatalog.objects.select_related('media', 'category').all()
for c in cats:
    if c.media:
        blob_size = len(c.media.bytes) if c.media.bytes else 0
        media_info = f"{c.media.filename} ({blob_size} bytes)"
    else:
        media_info = "NO MEDIA"
    cat_name = c.category.name if c.category else "NO CAT"
    print(f"  CC#{c.id}: category='{cat_name}' media='{media_info}'")

# Check for document media blobs
print("\n=== DOCUMENT MEDIA BLOB CHECK ===")
doc_media = Media.objects.filter(kind='document')
for m in doc_media:
    blob_size = len(m.bytes) if m.bytes else 0
    print(f"  Media#{m.id}: {m.filename} | blob_size={blob_size}")

# Show products without images (first 20)
print("\n=== PRODUCTS WITHOUT IMAGES (first 20) ===")
prods_no_img = Product.objects.exclude(product_media__media__kind='image')[:20]
for p in prods_no_img:
    variants = list(p.variants.values_list('model_code', flat=True))
    print(f"  Product#{p.id}: '{p.name}' | variants={variants}")

# Count source files
import os
src_dir = r"C:\Users\emir\Desktop\Fotolar"
total_files = 0
for root, dirs, files in os.walk(src_dir):
    total_files += len([f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
print(f"\n=== SOURCE FILES ===")
print(f"Total image files in Fotolar: {total_files}")
