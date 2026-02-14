import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from rest_framework.test import APIRequestFactory
from apps.catalog.models import Category
from apps.catalog.admin_viewsets import AdminCategoryViewSet
from apps.catalog.admin_serializers import AdminCategorySerializer

def reproduce():
    print("Setting up reproduction data...")
    # Clean up
    Category.objects.filter(slug__startswith="repro-").delete()
    
    # Create Parent Category
    parent = Category.objects.create(name="Repro Parent", slug="repro-parent")
    
    # Create Category A (will be the target)
    cat_a = Category.objects.create(name="Repro Cat A", slug="repro-cat-a", parent=parent)
    
    # Create Category B (conflict source)
    # Scenario: Moving Cat A to root, but "repro-cat-a" might theoretically exist at root?
    # Or just invalid parent.
    
    print(f"Created category: {cat_a}")
    
    # Try updating via Serializer to simulate API
    print("Attempting update via Serializer...")
    
    # payload = {"name": "Repro Cat A Updated", "parent_slug": None} 
    # This matches the user scenario of updating a category. The user didn't specify what they updated, 
    # but let's assume standard update.
    
    # We need to simulate the request context because ViewSet expects it
    factory = APIRequestFactory()
    request = factory.patch(f'/admin/categories/{cat_a.slug}/')
    request.user = None # Mock user if needed, or skip permission checks if testing serializer directly
    
    # Let's test Serializer validation directly first, as that's where validation logic lives
    # Case 1: Simple update
    data = {
        "name": "Repro Cat A Updated",
        # "slug": "repro-cat-a" # client usually sends slug back, or maybe not
    }
    
    serializer = AdminCategorySerializer(cat_a, data=data, partial=True)
    if serializer.is_valid():
        print("Serializer is valid.")
        try:
            serializer.save()
            print("Save successful.")
        except Exception as e:
            print(f"Caught exception during save: {type(e).__name__}: {e}")
    else:
        print(f"Serializer errors: {serializer.errors}")

    # Case 2: Trigger Unique Constraint Violation
    print("\nCase 2: Attempting to trigger unique constraint violation...")
    # Create another root category with same slug "repro-cat-a" (if possible? No, unique constraint)
    # Create "repro-cat-a" at root
    cat_root = Category.objects.create(name="Repro Cat A Root", slug="repro-cat-a-root")
    
    # Try to rename cat_a (which is under parent) to "repro-cat-a-root"
    data_conflict = {
        "slug": "repro-cat-a-root"
    }
    
    serializer_conflict = AdminCategorySerializer(cat_a, data=data_conflict, partial=True)
    if serializer_conflict.is_valid():
        print("Conflict Serializer is valid (Unexpected IF DRF handles it).")
        try:
            serializer_conflict.save()
            print("Conflict Save successful.")
        except Exception as e:
            print(f"Caught exception during Conflict save: {type(e).__name__}: {e}")
    else:
        print(f"Conflict Serializer errors: {serializer_conflict.errors}")

if __name__ == "__main__":
    try:
        reproduce()
    except Exception as e:
        print(f"Script failed: {e}")
