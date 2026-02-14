
import os
import sys
import django
from django.db.models import Q

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Product, Category

def find_products():
    keywords = ["Sebze", "Et", "Vakum", "Hamur", "Kurutucu"]
    print(f"Searching for products containing: {keywords}")
    
    for kw in keywords:
        # Based on FieldError, Product likely has title_tr/title_en or just name
        products = Product.objects.filter(Q(title_tr__icontains=kw) | Q(title_en__icontains=kw))
        count = products.count()
        print(f"\nKeyword '{kw}': {count} products found")
        
        if count > 0:
            for p in products[:5]:
                cat_name = p.category.name if p.category else "None"
                series_name = p.series.name if p.series else "None"
                series_cat = p.series.category.name if p.series and p.series.category else "None"
                print(f"  - {p.name} (Status: {p.status})")
                print(f"    Category: {cat_name}")
                print(f"    Series: {series_name} -> Series Cat: {series_cat}")

if __name__ == "__main__":
    find_products()
