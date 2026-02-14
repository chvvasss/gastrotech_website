from apps.catalog.models import Product, Category

# Get coffee products
products = Product.objects.filter(
    category__slug__in=['kahve-makineleri', 'kahve-degirmenleri', 'kahve-ekipmanlari', 'icecek-hazirlik']
)[:10]

print(f"First 10 coffee products:")
print("=" * 80)
for p in products:
    print(f"Name: {p.name}")
    print(f"  Brand: {p.brand.name if p.brand else 'NO BRAND'}")
    print(f"  Images: {p.product_media.count()}")
    print(f"  Category: {p.category.name if p.category else 'NO CATEGORY'}")
    print()
