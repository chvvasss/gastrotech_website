from apps.catalog.models import Product, Category

# Find firinlar category
firinlar = Category.objects.get(slug='firinlar')

# Count products
count = Product.objects.filter(category=firinlar, status='active').count()
print(f'\nFirinlar category products: {count}')

# Show sample slugs
products = Product.objects.filter(category=firinlar, status='active')[:10]
if products.exists():
    print('\nSample product slugs:')
    for p in products:
        print(f'  - {p.slug}')
else:
    print('\nNo products found in firinlar category')
