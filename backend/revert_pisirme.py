from apps.catalog.models import Category
from django.db import transaction

def revert():
    print("Starting revert of Pişirme Ekipmanları...")
    try:
        pisirme = Category.objects.filter(slug='pisirme-ekipmanlari').first()
        if not pisirme:
            print("Category 'pisirme-ekipmanlari' not found. Nothing to revert?")
            return

        # Handle 'firinlar' specifically
        firinlar = Category.objects.filter(slug='firinlar').first()
        if firinlar and firinlar.parent_id == pisirme.id:
            print("Moving 'firinlar' back to root (parent=None)...")
            firinlar.parent = None
            firinlar.save()
        else:
            print(f"Notes on 'firinlar': Found={firinlar is not None}, Parent={firinlar.parent.slug if firinlar and firinlar.parent else 'None'}")

        # Delete 'pisirme-ekipmanlari' and remaining children
        # Children like 'pizza-firinlari' etc will be deleted by CASCADE or manually if needed?
        # Django ForeignKey defaults to CASCADE usually.
        # But let's check children explicitly to be sure.
        children = pisirme.children.all()
        for c in children:
            print(f"Deleting child category: {c.name} ({c.slug})")
            c.delete()

        print("Deleting 'pisirme-ekipmanlari' category...")
        pisirme.delete()
        print("Revert complete.")

    except Exception as e:
        print(f"Error during revert: {e}")

revert()
