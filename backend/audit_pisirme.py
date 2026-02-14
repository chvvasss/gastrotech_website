from apps.catalog.models import Category, CategoryLogoGroup

def audit():
    try:
        root = Category.objects.get(slug='pisirme-ekipmanlari')
        print(f'Root: {root.name} ({root.slug})')
        children = root.children.all().order_by('order')
        print(f'Children Count: {children.count()}')
        for c in children:
            print(f' - {c.name} ({c.slug}) [Order: {c.order}]')
            lgs = c.logo_groups.all()
            for lg in lgs:
                print(f'   -> Brand: {lg.brand.name} ({lg.brand.slug})')
                series = lg.series_set.all().order_by('order')
                for s in series:
                    print(f'      * {s.series.name} (Heading: {s.is_heading})')
    except Category.DoesNotExist:
        print("Root category 'pisirme-ekipmanlari' NOT FOUND.")

audit()
