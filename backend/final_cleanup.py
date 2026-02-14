"""Final Cleanup: Delete orphaned Pişirme Ekipmanları"""
from apps.catalog.models import Category

cat = Category.objects.filter(slug='pisirme-ekipmanlari').first()
if cat:
    if cat.children.count() == 0:
        print(f"Deleting empty category: {cat.name} ({cat.slug})")
        cat.delete()
        print("Deleted!")
    else:
        print(f"Category has {cat.children.count()} children, skipping delete")
else:
    print("Category 'pisirme-ekipmanlari' not found")
