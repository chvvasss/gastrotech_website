from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from apps.catalog.models import Category, Series, Brand, CategoryLogoGroup, LogoGroupSeries

class Command(BaseCommand):
    help = 'Seeds Soğutma Üniteleri > Soğutma Ekipmanları category structure'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Refrigeration Equipment...')
        
        with transaction.atomic():
            # 1. Ensure Parent Category Exists
            parent, _ = Category.objects.get_or_create(
                slug='sogutma-uniteleri',
                defaults={
                    'name': 'Soğutma Üniteleri',
                    'order': 20
                }
            )
            
            # 2. Create Subcategory: Soğutma Ekipmanları
            subcat, _ = Category.objects.get_or_create(
                slug='sogutma-ekipmanlari',
                defaults={
                    'name': 'Soğutma Ekipmanları',
                    'parent': parent,
                    'order': 20,
                    'description_short': 'Profesyonel soğutma dolapları ve soğuk oda sistemleri'
                }
            )
            
            # Update parent just in case
            if subcat.parent != parent:
                subcat.parent = parent
                subcat.save()

            # 3. Create Brands
            gtech_brand, _ = Brand.objects.get_or_create(
                slug='gtech',
                defaults={'name': 'Gtech', 'is_active': True, 'order': 10}
            )
            
            frenox_brand, _ = Brand.objects.get_or_create(
                slug='frenox',
                defaults={'name': 'FRENOX', 'is_active': True, 'order': 20}
            )

            # 4. Define Structures
            # Gtech Structure
            gtech_structure = [
                ("Soğutma Ekipmanları - Basic Seri", [
                    "Tezgah Tipi Buzdolapları",
                    "Tezgah Tipi Derin Dondurucular",
                    "Set Altı Buzdolapları",
                    "Pizza-Salata Hazırlık Buzdolapları",
                    "Make-up Üniteleri",
                    "Dik Tip Buzdolapları",
                    "Dik Tip Derin Dondurucular"
                ]),
                ("Şişe Soğutucular", [
                    "Bar Dipi Şişe Soğutucular",
                    "Paslanmaz Çelik Kasa Şişe Soğutucular",
                    "Dik Tip Şişe Soğutucular",
                    "Bar Altı Dondurucular"
                ]),
                ("Soğuk Odalar", [
                    "Soğuk Hava Depoları -5/+5 °C",
                    "Soğuk Hava Depoları -18/-22 °C"
                ])
            ]

            # Frenox Structure
            frenox_structure = [
                ("Soğutma Ekipmanları - Premium Seri", [
                    "Tezgah Tipi Buzdolapları",
                    "Tezgah Tipi Derin Dondurucular",
                    "Set Altı Buzdolapları",
                    "Pizza/Salata Hazırlık Buzdolapları",
                    "Pizza Hazırlık Buzdolapları",
                    "Make-Up Üniteleri",
                    "Dik Tip Buzdolapları",
                    "Dik Tip Kombinasyonlu Buzdolapları",
                    "Dik Tip Dry Age Buzdolapları",
                    "Şok Soğutucu/Dondurucular",
                    "Kokteyl Tezgahları"
                ])
            ]
            
            configs = [
                (gtech_brand, gtech_structure),
                (frenox_brand, frenox_structure)
            ]

            # 5. Process Each Brand
            for brand, structure in configs:
                # Create Logo Group
                logo_group, _ = CategoryLogoGroup.objects.get_or_create(
                    category=subcat,
                    brand=brand,
                    defaults={
                        'title': f'{brand.name} Soğutma Ekipmanları',
                        'order': brand.order
                    }
                )
                
                global_order = 10
                
                for heading, series_names in structure:
                    # Create Heading Series
                    # Ensure slug is unique by prefixing brand or heading context
                    heading_slug = slugify(f"{brand.slug}-{heading}")
                    
                    heading_series, _ = Series.objects.get_or_create(
                        slug=heading_slug,
                        defaults={
                            'name': heading,
                            'category': subcat,
                            'is_featured': False
                        }
                    )
                     # Ensure category consistency
                    if heading_series.category != subcat:
                        heading_series.category = subcat
                        heading_series.save()

                    # Link Heading
                    LogoGroupSeries.objects.get_or_create(
                        logo_group=logo_group,
                        series=heading_series,
                        defaults={'is_heading': True, 'order': global_order}
                    )
                    global_order += 10

                    # Create Child Series
                    for s_name in series_names:
                        # Append brand to slug to avoid collision between Gtech/Frenox same-named series
                        s_slug = slugify(f"{brand.slug}-{s_name}".replace(' & ', '-ve-').replace(' ', '-').replace('/', '-').replace('°', '').replace('+', 'plus'))
                        
                        series_obj, _ = Series.objects.get_or_create(
                            slug=s_slug,
                            defaults={
                                'name': s_name,
                                'category': subcat,
                                'is_featured': False
                            }
                        )
                        
                        if series_obj.category != subcat:
                             series_obj.category = subcat
                             series_obj.save()

                        # Link Child
                        lgs, created = LogoGroupSeries.objects.get_or_create(
                            logo_group=logo_group,
                            series=series_obj,
                            defaults={'is_heading': False, 'order': global_order}
                        )
                        if not created:
                             lgs.is_heading = False
                             lgs.order = global_order
                             lgs.save()
                        
                        global_order += 10

        self.stdout.write(self.style.SUCCESS('Successfully seeded Refrigeration Equipment'))
