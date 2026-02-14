"""
Master Seed Script - Complete Category Hierarchy
=================================================
Implements the full hierarchy from user images:
1. Fırınlar (Salva, VITAL, AS TERM, Mychef, Electrolux)
2. Soğutma Üniteleri (Gtech, FRENOX, Scotsman)
3. Hazırlık Ekipmanları (Gtech, ESSEDUE, LERICA, CGF, vitella, Dalle)
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from apps.catalog.models import Category, Series, Brand, CategoryLogoGroup, LogoGroupSeries


def slugify_tr(text):
    """Turkish-aware slugify"""
    tr_map = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
              'İ': 'i', 'Ğ': 'g', 'Ü': 'u', 'Ş': 's', 'Ö': 'o', 'Ç': 'c'}
    for tr, en in tr_map.items():
        text = text.replace(tr, en)
    return slugify(text)


class Command(BaseCommand):
    help = 'Seeds complete category hierarchy from user images'

    def handle(self, *args, **options):
        self.stdout.write('Starting Master Seed...')
        
        with transaction.atomic():
            # ===== BRANDS =====
            brands = self._create_brands()
            
            # ===== FIRINLAR =====
            self._seed_firinlar(brands)
            
            # ===== SOGUTMA UNITELERI =====
            self._seed_sogutma(brands)
            
            # ===== HAZIRLIK EKIPMANLARI =====
            self._seed_hazirlik(brands)

        self.stdout.write(self.style.SUCCESS('Master Seed Complete!'))

    def _create_brands(self):
        """Create all required brands"""
        brand_data = [
            ('salva', 'Salva', 10),
            ('vital', 'VITAL', 20),
            ('asterm', 'AS TERM', 30),
            ('mychef', 'Mychef', 40),
            ('electrolux', 'Electrolux', 50),
            ('gtech', 'Gtech', 60),
            ('frenox', 'FRENOX', 70),
            ('scotsman', 'Scotsman', 80),
            ('essedue', 'ESSEDUE', 90),
            ('lerica', 'LERICA', 100),
            ('cgf', 'CGF', 110),
            ('vitella', 'vitella', 120),
            ('dalle', 'Dalle', 130),
        ]
        
        brands = {}
        for slug, name, order in brand_data:
            brand, _ = Brand.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'is_active': True, 'order': order}
            )
            brands[slug] = brand
            
        self.stdout.write(f'  Created/verified {len(brands)} brands')
        return brands

    def _seed_firinlar(self, brands):
        """Seed Fırınlar category structure"""
        self.stdout.write('  Seeding Fırınlar...')
        
        # Get or create Fırınlar root
        firinlar, _ = Category.objects.get_or_create(
            slug='firinlar',
            defaults={'name': 'Fırınlar', 'order': 2}
        )
        
        # 1. Main Fırınlar -> Salva
        self._create_logo_group(
            category=firinlar,
            brand=brands['salva'],
            series_data=[
                ('KWIK-CO Serisi Konveksiyonel Fırınlar', False),
                ('KWIK-E Serisi Pro Wash Fırınlar', False),
                ('Elektrikli Fırınlar', False),
                ('Taş Tabanlı Bakery Fırınlar', False),
            ]
        )
        
        # 2. Pizza Fırınları subcategory
        pizza, _ = Category.objects.get_or_create(
            slug='pizza-firinlari',
            defaults={'name': 'Pizza Fırınları', 'parent': firinlar, 'order': 5}
        )
        if pizza.parent != firinlar:
            pizza.parent = firinlar
            pizza.save()
        
        self._create_logo_group(
            category=pizza,
            brand=brands['vital'],
            series_data=[
                ('Pizza Fırınları', False),
                ('Tek Katlı Pizza Fırınları', False),
                ('Çift Katlı Pizza Fırınları', False),
                ('Taş Tabanlı Gazlı Pizza Fırınları', False),
            ]
        )
        
        self._create_logo_group(
            category=pizza,
            brand=brands['asterm'],
            series_data=[
                ('Pizza Fırınları', False),
                ('Gazlı Döner Tabanlı Pizza Fırınları', False),
                ('Gazlı ve Odunlu Döner Tabanlı Pizza Fırınları', False),
            ]
        )
        
        # 3. Mayalama Kabinleri subcategory
        mayalama, _ = Category.objects.get_or_create(
            slug='mayalama-kabinleri',
            defaults={'name': 'Mayalama Kabinleri', 'parent': firinlar, 'order': 10}
        )
        if mayalama.parent != firinlar:
            mayalama.parent = firinlar
            mayalama.save()
        
        self._create_logo_group(
            category=mayalama,
            brand=brands['vital'],
            series_data=[('Mayalama Kabinleri', False)]
        )
        
        self._create_logo_group(
            category=mayalama,
            brand=brands['salva'],
            series_data=[('Mayalama Kabinleri', False)]
        )
        
        # 4. Hızlı Pişirme Fırınları
        hizli, _ = Category.objects.get_or_create(
            slug='hizli-pisirme-firinlari',
            defaults={'name': 'Hızlı Pişirme Fırınları', 'parent': firinlar, 'order': 40}
        )
        if hizli.parent != firinlar:
            hizli.parent = firinlar
            hizli.save()
        
        self._create_logo_group(
            category=hizli,
            brand=brands['mychef'],
            series_data=[('Hızlı Pişirme Fırınları', False)]
        )
        
        # 5. Mikrodalgalar
        mikro, _ = Category.objects.get_or_create(
            slug='mikrodalgalar',
            defaults={'name': 'Mikrodalgalar', 'parent': firinlar, 'order': 50}
        )
        if mikro.parent != firinlar:
            mikro.parent = firinlar
            mikro.save()
        
        self._create_logo_group(
            category=mikro,
            brand=brands['electrolux'],
            series_data=[('Mikrodalga Fırınlar', False)]
        )

    def _seed_sogutma(self, brands):
        """Seed Soğutma Üniteleri structure"""
        self.stdout.write('  Seeding Soğutma Üniteleri...')
        
        # Get or create Soğutma Üniteleri root
        sogutma, _ = Category.objects.get_or_create(
            slug='sogutma-uniteleri',
            defaults={'name': 'Soğutma Üniteleri', 'order': 3}
        )
        
        # 1. Soğutma Ekipmanları
        ekip, _ = Category.objects.get_or_create(
            slug='sogutma-ekipmanlari',
            defaults={'name': 'Soğutma Ekipmanları', 'parent': sogutma, 'order': 20}
        )
        if ekip.parent != sogutma:
            ekip.parent = sogutma
            ekip.save()
        
        # Gtech with headings
        self._create_logo_group(
            category=ekip,
            brand=brands['gtech'],
            series_data=[
                ('Soğutma Ekipmanları - Basic Seri', True),  # HEADING
                ('Tezgah Tipi Buzdolapları', False),
                ('Tezgah Tipi Derin Dondurucular', False),
                ('Set Altı Buzdolapları', False),
                ('Pizza-Salata Hazırlık Buzdolapları', False),
                ('Make-up Üniteleri', False),
                ('Dik Tip Buzdolapları', False),
                ('Dik Tip Derin Dondurucular', False),
                ('Şişe Soğutucular', True),  # HEADING
                ('Bar Dipi Şişe Soğutucular', False),
                ('Paslanmaz Çelik Kasa Şişe Soğutucular', False),
                ('Dik Tip Şişe Soğutucular', False),
                ('Bar Altı Dondurucular', False),
                ('Soğuk Odalar', True),  # HEADING
                ('Soğuk Hava Depoları -5/+5 °C', False),
                ('Soğuk Hava Depoları -18/-22 °C', False),
            ]
        )
        
        # FRENOX with headings
        self._create_logo_group(
            category=ekip,
            brand=brands['frenox'],
            series_data=[
                ('Soğutma Ekipmanları - Premium Seri', True),  # HEADING
                ('Tezgah Tipi Buzdolapları', False),
                ('Tezgah Tipi Derin Dondurucular', False),
                ('Set Altı Buzdolapları', False),
                ('Pizza/Salata Hazırlık Buzdolapları', False),
                ('Pizza Hazırlık Buzdolapları', False),
                ('Make-Up Üniteleri', False),
                ('Dik Tip Buzdolapları', False),
                ('Dik Tip Kombinasyonlu Buzdolapları', False),
                ('Dik Tip Dry Age Buzdolapları', False),
                ('Şok Soğutucu/Dondurucular', False),
                ('Kokteyl Tezgahları', False),
            ]
        )
        
        # 2. Buz Makineleri
        buz, _ = Category.objects.get_or_create(
            slug='buz-makineleri',
            defaults={'name': 'Buz Makineleri', 'parent': sogutma, 'order': 10}
        )
        if buz.parent != sogutma:
            buz.parent = sogutma
            buz.save()
        
        # Scotsman with full hierarchy
        self._create_logo_group(
            category=buz,
            brand=brands['scotsman'],
            series_data=[
                ('Gurme Buz Makineleri', True),
                ('EC Serisi', False),
                ('AC Serisi', False),
                ('Barline B Serisi', False),
                ('Legacy', False),
                ('Haznesiz Gurme Buz Makineleri', True),
                ('MXG Serisi', False),
                ('DICE ICE Buze Makineleri', False),
                ('NU Serisi', False),
                ('Haznesiz DICE ICE Buz Makineleri', True),
                ('NW Serisi', False),
                ('Kar Buz Makineleri', True),
                ('AF Serisi', False),
                ('Haznesiz Buz Makineleri', True),
                ('MF Serisi', False),
                ('MXF Serisi', False),
                ('Dispenserli Buz & Buzlu Su Makineleri', True),
                ('DXN Serisi', False),
                ('DXG Serisi', False),
                ('Buz Saklama Sistemleri', True),
                ('SB Serisi', False),
                ('Yerli Saklama Sistemleri', True),
                ('BK Serisi', False),
            ]
        )

    def _seed_hazirlik(self, brands):
        """Seed Hazırlık Ekipmanları structure"""
        self.stdout.write('  Seeding Hazırlık Ekipmanları...')
        
        # Get or create Hazırlık Ekipmanları root
        hazirlik, _ = Category.objects.get_or_create(
            slug='hazirlik-ekipmanlari',
            defaults={'name': 'Hazırlık Ekipmanları', 'order': 4}
        )
        
        # 1. Sebze Yıkama Makineleri
        sebze, _ = Category.objects.get_or_create(
            slug='sebze-yikama-makineleri',
            defaults={'name': 'Sebze Yıkama Makineleri', 'parent': hazirlik, 'order': 10}
        )
        if sebze.parent != hazirlik:
            sebze.parent = hazirlik
            sebze.save()
        
        self._create_logo_group(
            category=sebze,
            brand=brands['gtech'],
            series_data=[
                ('Sebze Yıkama Makineleri', False),
                ('Devirli Sebze Yıkama Makineleri', False),
            ]
        )
        
        # 2. Et İşleme Makineleri
        et, _ = Category.objects.get_or_create(
            slug='et-isleme-makineleri',
            defaults={'name': 'Et İşleme Makineleri', 'parent': hazirlik, 'order': 20}
        )
        if et.parent != hazirlik:
            et.parent = hazirlik
            et.save()
        
        self._create_logo_group(
            category=et,
            brand=brands['essedue'],
            series_data=[
                ('Gıda Dilimleme Makineleri', False),
                ('Diket Gıda Dilimleme Makineleri', False),
                ('Otomatik Gıda Dilimleme Makineleri', False),
            ]
        )
        
        # 3. Vakum Makineleri
        vakum, _ = Category.objects.get_or_create(
            slug='vakum-makineleri',
            defaults={'name': 'Vakum Makineleri', 'parent': hazirlik, 'order': 30}
        )
        if vakum.parent != hazirlik:
            vakum.parent = hazirlik
            vakum.save()
        
        self._create_logo_group(
            category=vakum,
            brand=brands['lerica'],
            series_data=[('Vakum Makineleri', False)]
        )
        
        # 4. Hamur İşleme Makineleri
        hamur, _ = Category.objects.get_or_create(
            slug='hamur-isleme-makineleri',
            defaults={'name': 'Hamur İşleme Makineleri', 'parent': hazirlik, 'order': 40}
        )
        if hamur.parent != hazirlik:
            hamur.parent = hazirlik
            hamur.save()
        
        self._create_logo_group(
            category=hamur,
            brand=brands['cgf'],
            series_data=[
                ('Kanatlı Hamur Açma Makineleri', True),  # HEADING
                ('Kruvasan Kesme Cihazları', False),
                ('Set Üstü Hamur Açma Makineleri', False),
                ('Standlı Hamur Açma Makineleri', False),
            ]
        )
        
        self._create_logo_group(
            category=hamur,
            brand=brands['vitella'],
            series_data=[
                ('Hamur Bölme ve Yuvarlama Makineleri', True),  # HEADING
                ('Manuel Hamur Bölme ve Yuvarlama Makineleri', False),
                ('Otomatik Hamur Bölme ve Yuvarlama Makineleri', False),
            ]
        )
        
        # 5. Sebze ve Meyve Kurutucular
        kurut, _ = Category.objects.get_or_create(
            slug='sebze-ve-meyve-kurutucular',
            defaults={'name': 'Sebze ve Meyve Kurutucular', 'parent': hazirlik, 'order': 50}
        )
        if kurut.parent != hazirlik:
            kurut.parent = hazirlik
            kurut.save()
        
        self._create_logo_group(
            category=kurut,
            brand=brands['gtech'],
            series_data=[('Dehidratörler', False)]
        )
        
        self._create_logo_group(
            category=kurut,
            brand=brands['dalle'],
            series_data=[('Dondurarak Sebze ve Meyve Kurutucular', False)]
        )

    def _create_logo_group(self, category, brand, series_data):
        """Helper to create logo group and link series"""
        # Get or create logo group
        logo_group, _ = CategoryLogoGroup.objects.get_or_create(
            category=category,
            brand=brand,
            defaults={'order': brand.order}
        )
        
        # Clear existing series links for this logo group (idempotent)
        LogoGroupSeries.objects.filter(logo_group=logo_group).delete()
        
        # Create series and link
        order = 10
        for name, is_heading in series_data:
            # Create unique slug with brand prefix to avoid collisions
            slug = slugify_tr(f"{brand.slug}-{name}")
            
            series, _ = Series.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'category': category,
                    'is_featured': False
                }
            )
            
            # Ensure category is correct
            if series.category != category:
                series.category = category
                series.save()
            
            # Link to logo group
            LogoGroupSeries.objects.create(
                logo_group=logo_group,
                series=series,
                order=order,
                is_heading=is_heading
            )
            order += 10
