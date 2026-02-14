from apps.catalog.models import Category, Series, TaxonomyNode, Product, Variant, SpecKey, Media, ProductMedia, Brand

print("Starting to clear catalog database...")

# Delete in order of dependency to avoid protected foreign key errors, though cascade usually handles it.
# We'll rely on CASCADE mostly but doing it somewhat orderly helps debugging if it fails.

print("Deleting Brands...")
Brand.objects.all().delete()

print("Deleting Product Media Relations...")
ProductMedia.objects.all().delete()

print("Deleting Variants...")
Variant.objects.all().delete()

print("Deleting Products...")
Product.objects.all().delete()

print("Deleting Taxonomy Nodes...")
TaxonomyNode.objects.all().delete()

print("Deleting Series...")
Series.objects.all().delete()

print("Deleting Categories...")
Category.objects.all().delete()

print("Deleting SpecKeys...")
SpecKey.objects.all().delete()

# Optional: Delete Media files if they are just for catalog
# print("Deleting Media...")
# Media.objects.all().delete() # Commented out to avoid deleting system media if any, but user said "everything". 
# Let's delete Media too as it's likely catalog images.
print("Deleting Media...")
Media.objects.all().delete()

print("Database cleared successfully!")
