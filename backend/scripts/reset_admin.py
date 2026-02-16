
import os
import sys
from pathlib import Path
from django.contrib.auth import get_user_model

sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ["DATABASE_URL"] = "postgres://postgres:postgres@localhost:5432/gastrotech"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

User = get_user_model()

def run():
    print("=== Resetting Admin Users ===\n")
    
    # 1. Delete existing superusers
    admins = User.objects.filter(is_superuser=True)
    count = admins.count()
    if count > 0:
        print(f"Deleting {count} existing superuser(s)...")
        admins.delete()
    else:
        print("No existing superusers found.")
        
    # 2. Create new superuser
    print("Creating new superuser...")
    try:
        # Create user with default creds
        # Using create_superuser helper
        admin = User.objects.create_superuser(
            email='admin@gastrotech.com',
            password='gastrotech_admin',
            first_name='Admin',
            last_name='User'
        )
        print("\nSUCCESS!")
        print(f"Email: {admin.email}")
        print(f"Password: gastrotech_admin")
    except Exception as e:
        print(f"\n[ERROR] Failed to create superuser: {e}")

if __name__ == "__main__":
    run()
