from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from apps.catalog.models import Category, Series, Brand, CategoryLogoGroup, LogoGroupSeries

class Command(BaseCommand):
    help = 'Seeds Pisirme Ekipmanlari structure'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Cooking Equipment...')
        
        with transaction.atomic():
            # 1. Ensure Parent Category Exists
            parent, _ = Category.objects.get_or_create(
                slug='pisirme-ekipmanlari',
                defaults={
                    'name': 'Pişirme Ekipmanları',
                    'order': 10
                }
            )

            # 1b. Ensure Firinlar is a ROOT category (not under pisirme-ekipmanlari)
            firinlar_root, _ = Category.objects.get_or_create(
                slug='firinlar',
                defaults={
                    'name': 'Firinlar',
                    'order': 20
                }
            )
            if firinlar_root.parent is not None:
                firinlar_root.parent = None
                firinlar_root.save(update_fields=['parent'])

            # 2. Define Brands
            # Check/Create Brands
            brands_data = [
                ('salva', 'Salva', 30),
                ('vital', 'VITAL', 40),
                ('asterm', 'Asterm', 50),
                ('mychef', 'Mychef', 60),
                ('electrolux', 'Electrolux', 70),
            ]
            
            brand_objs = {}
            for slug, name, order in brands_data:
                b, _ = Brand.objects.get_or_create(
                    slug=slug,
                    defaults={'name': name, 'is_active': True, 'order': order}
                )
                brand_objs[slug] = b

            # 3. Structure Definition
            # Format: (Category Name, slug, [ (BrandSlug, [Series List]) ])
            
            structures = [
                (
                    "Fırınlar", "firinlar",
                    [
                        ('salva', [
                            "KWIK-CO Serisi Konvelsiyonel Fırınlar",
                            "KWIK-E Serisi Pro Wash Fırınlar",
                            "Elektrikli Fırınlar",
                            "Taş Tabanlı Bakery Fırınlar"
                        ])
                    ]
                ),
                (
                    "Pizza Fırınları", "pizza-firinlari",
                    [
                        ('vital', [
                            "Pizza Fırınları",
                            "Tek Katlı Pizza Fırınları",
                            "Çift Katlı Pizza Fırınları",
                            "Taş Tabanlı Gazlı Pizza Fırınları"
                        ]),
                         ('asterm', [
                            "Pizza Fırınları",
                            "Gazlı Döner Tabanlı Pizza Fırınları",
                            "Gazlı ve Odunlu Döner Tabanlı Pizza Fırınları"
                        ])
                    ]
                ),
                (
                    "Mayalama Kabinleri", "mayalama-kabinleri",
                    [
                        ('vital', ["Mayalama Kabinleri"]),
                        ('salva', ["Mayalama Kabinleri"])
                    ]
                ),
                (
                     "Hızlı Pişirme Fırınları", "hizli-pisirme-firinlari",
                     [
                         ('mychef', ["Hızlı Pişirme Fırınları"])
                     ]
                ),
                (
                    "Mikrodalgalar", "mikrodalgalar",
                    [
                        ('electrolux', ["Mikrodalga Fırınlar"])
                    ]
                )
            ]

            # 4. Process Structures
            cat_order = 10
            for cat_name, cat_slug, brand_configs in structures:
                # Determine correct parent
                if cat_slug == 'firinlar':
                    subcat = firinlar_root
                    if subcat.name != cat_name:
                        subcat.name = cat_name
                        subcat.save(update_fields=['name'])
                else:
                    target_parent = firinlar_root if cat_slug in [
                        'pizza-firinlari',
                        'hizli-pisirme-firinlari',
                        'mikrodalgalar',
                    ] else parent

                    # Create Subcategory
                    subcat, created = Category.objects.get_or_create(
                        slug=cat_slug,
                        defaults={
                            'name': cat_name,
                            'parent': target_parent,
                            'order': cat_order
                        }
                    )
                    if subcat.parent != target_parent:
                        subcat.parent = target_parent
                        subcat.save()
                
                cat_order += 10
                
                # Process Brands for this Category
                for b_slug, series_list in brand_configs:
                    brand = brand_objs[b_slug]
                    
                    # Create Logo Group
                    logo_group, _ = CategoryLogoGroup.objects.get_or_create(
                        category=subcat,
                        brand=brand,
                        defaults={
                            'title': f'{brand.name} {cat_name}',
                            'order': brand.order
                        }
                    )

                    # Create Series
                    series_order = 10
                    for s_name in series_list:
                         # Unique slug: brand-series-category context if needed
                         # But sticking to brand-series is usually enough.
                         # Need to handle "Pizza Fırınları" series appearing in multiple places? Use brand prefix.
                         
                         base_slug = f"{brand.slug}-{s_name}"
                         s_slug = slugify(base_slug.replace(' & ', '-ve-').replace('/', '-'))
                         
                         series_obj, _ = Series.objects.get_or_create(
                            slug=s_slug,
                            defaults={
                                'name': s_name,
                                'category': subcat,
                                'is_featured': False
                            }
                        )
                         # Ensure category
                         if series_obj.category != subcat:
                             # If it exists but in another category, we might have a problem if slug is same.
                             # But slug includes brand, so likely unique unless brand has same series in 2 categories.
                             # E.g. Vital -> Pizza Fırınları vs Vital -> Mayalama Kabinleri.
                             # Series names are different ("Pizza Fırınları" vs "Mayalama Kabinleri").
                             # Warning: "Pizza Fırınları" is a series name.
                             # If Vital has "Pizza Fırınları" series in "Pizza Fırınları" category...
                             series_obj.category = subcat
                             series_obj.save()

                         # Link to Logo Group
                         LogoGroupSeries.objects.get_or_create(
                            logo_group=logo_group,
                            series=series_obj,
                            defaults={'is_heading': False, 'order': series_order}
                        )
                         series_order += 10

        self.stdout.write(self.style.SUCCESS('Successfully seeded Cooking Equipment'))
