from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from apps.catalog.models import Category, Series, Brand, CategoryLogoGroup, LogoGroupSeries

class Command(BaseCommand):
    help = 'Seeds Soğutma Üniteleri > Buz Makineleri category structure'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Ice Machines...')
        
        with transaction.atomic():
            # 1. Ensure Parent Category Exists
            parent, _ = Category.objects.get_or_create(
                slug='sogutma-uniteleri',
                defaults={
                    'name': 'Soğutma Üniteleri',
                    'order': 20
                }
            )
            
            # 2. Create Subcategory: Buz Makineleri
            subcat, _ = Category.objects.get_or_create(
                slug='buz-makineleri',
                defaults={
                    'name': 'Buz Makineleri',
                    'parent': parent,
                    'order': 10,
                    'description_short': 'Endüstriyel buz makineleri ve depolama çözümleri'
                }
            )
            
            # Update parent just in case
            if subcat.parent != parent:
                subcat.parent = parent
                subcat.save()

            # 3. Create Brand: Scotsman (Main Brand) & BK (Local Brand)
            scotsman, _ = Brand.objects.get_or_create(
                slug='scotsman',
                defaults={
                    'name': 'Scotsman',
                    'is_active': True,
                    'order': 10
                }
            )
            
            # 4. Create Logo Group for Scotsman in Buz Makineleri
            logo_group, _ = CategoryLogoGroup.objects.get_or_create(
                category=subcat,
                brand=scotsman,
                defaults={
                    'title': 'Scotsman Buz Makineleri',
                    'order': 1
                }
            )

            # 5. Define Hierarchy
            # Format: (Heading, [Series List])
            structure = [
                ("Gurme Buz Makineleri", ["EC Serisi", "AC Serisi", "Barline B Serisi", "Legacy"]),
                ("Haznesiz Gurme Buz Makineleri", ["MXG Serisi"]),
                ("DICE ICE Buz Makineleri", ["NU Serisi"]),
                ("Haznesiz DICE ICE Buz Makineleri", ["NW Serisi"]),
                ("Kar Buz Makineleri", ["AF Serisi"]),
                ("Haznesiz Buz Makineleri", ["MF Serisi", "MXF Serisi"]),
                ("Dispenserli Buz & Buzlu Su Makineleri", ["DXN Serisi", "DXG Serisi"]),
                ("Buz Saklama Sistemleri", ["SB Serisi"]),
                ("Yerli Saklama Sistemleri", ["BK Serisi"]),
            ]

            global_order = 10
            
            for heading, series_names in structure:
                # 1. Create and Link Heading Series
                heading_slug = slugify(heading.replace(' & ', '-ve-').replace(' ', '-'))
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

                LogoGroupSeries.objects.get_or_create(
                    logo_group=logo_group,
                    series=heading_series,
                    defaults={
                        'is_heading': True,
                        'order': global_order
                    }
                )
                global_order += 10

                # 2. Create and Link Child Series
                for s_name in series_names:
                    s_slug = slugify(s_name.replace(' & ', '-ve-').replace(' ', '-'))
                    
                    series_obj, _ = Series.objects.get_or_create(
                        slug=s_slug,
                        defaults={
                            'name': s_name,
                            'category': subcat,
                            'is_featured': False
                        }
                    )
                    
                    # Ensure category consistency
                    if series_obj.category != subcat:
                         series_obj.category = subcat
                         series_obj.save()

                    # Link to LogoGroup
                    lgs, created = LogoGroupSeries.objects.get_or_create(
                        logo_group=logo_group,
                        series=series_obj,
                        defaults={
                            'is_heading': False,
                            'order': global_order
                        }
                    )
                    
                    if not created:
                        lgs.is_heading = False
                        lgs.order = global_order
                        lgs.save()
                    
                    global_order += 10

        self.stdout.write(self.style.SUCCESS('Successfully seeded Ice Machines'))
