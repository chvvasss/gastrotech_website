
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.catalog.models import Category

def create_initial_categories():
    categories = [
        "Pişirme Ekipmanları",
        "Fırınlar",
        "Soğutma Üniteleri",
        "Hazırlık Ekipmanları",
        "Kafeterya Ekipmanları",
        "Çamaşırhane",
        "Tamamlayıcı Ekipmanlar",
        "Bulaşıkhane"
    ]

    print("Creating initial categories...")
    
    for index, name in enumerate(categories, 1):
        category, created = Category.objects.get_or_create(
            name=name,
            defaults={
                'order': index,
                'is_featured': True  # Make them visible by default
            }
        )
        
        if created:
            print(f"Created: {name} (Order: {index})")
        else:
            print(f"Already exists: {name}")

    print(f"\nTotal Categories: {Category.objects.count()}")

if __name__ == '__main__':
    create_initial_categories()
