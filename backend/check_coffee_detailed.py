from apps.catalog.models import Product

# Get all coffee products
products = Product.objects.filter(
    category__slug__in=['kahve-makineleri', 'kahve-degirmenleri', 'kahve-ekipmanlari', 'icecek-hazirlik']
).select_related('brand', 'category').prefetch_related('product_media')

print(f"Total coffee products: {products.count()}")
print("=" * 100)

for p in products:
    print(f"\nProduct: {p.name}")
    print(f"  Slug: {p.slug}")
    print(f"  Brand: {p.brand.name if p.brand else 'NO BRAND'}")
    print(f"  Category: {p.category.name if p.category else 'NO CATEGORY'}")
    print(f"  Images: {p.product_media.count()}")
    if p.product_media.exists():
        for pm in p.product_media.all()[:2]:
            print(f"    - {pm.media.filename if pm.media else 'NO MEDIA'}")
    
    # Check for encoding issues
    if any(c in p.name for c in ['??', '�', '\ufffd']):
        print(f"  ⚠️  ENCODING ISSUE DETECTED IN NAME!")
