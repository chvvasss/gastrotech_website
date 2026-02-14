from apps.catalog.models import Category

def check():
    print("=== VERIFICATION ===")
    
    # 1. Fırınlar
    try:
        f = Category.objects.get(slug='firinlar')
        print(f"✅ Fırınlar found (Children: {f.children.count()})")
        for c in f.children.all():
            print(f"  - {c.name} ({c.logo_groups.count()} logo groups)")
    except Category.DoesNotExist:
        print("❌ Fırınlar NOT found")

    # 2. Soğutma
    try:
        s = Category.objects.get(slug='sogutma-uniteleri')
        print(f"\n✅ Soğutma Üniteleri found (Children: {s.children.count()})")
        for c in s.children.all():
            print(f"  - {c.name} ({c.logo_groups.count()} logo groups)")
    except:
        print("❌ Soğutma NOT found")

    # 3. Hazırlık
    try:
        h = Category.objects.get(slug='hazirlik-ekipmanlari')
        print(f"\n✅ Hazırlık Ekipmanları found (Children: {h.children.count()})")
        for c in h.children.all():
            print(f"  - {c.name} ({c.logo_groups.count()} logo groups)")
    except:
        print("❌ Hazırlık NOT found")

check()
