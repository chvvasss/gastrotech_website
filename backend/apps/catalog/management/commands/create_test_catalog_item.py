"""
Django management command to create a complete test product with full hierarchy.

Creates:
- Category: Pişirme Üniteleri
- Brand: Gastrotech Test
- Series: 900 Serisi (Test)
- Product: Test Endüstriyel Ocak
- 2 Variants: 4-burner and 6-burner models

Idempotent: running multiple times will not create duplicates.
Usage: python manage.py create_test_catalog_item
"""

from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Category, Brand, BrandCategory, Series, Product, Variant


class Command(BaseCommand):
    help = "Create a complete test product with category, brand, series, product, and variants"

    def handle(self, *args, **options):
        """Create test catalog item with full hierarchy."""
        self.stdout.write("=" * 80)
        self.stdout.write("Creating Test Catalog Item (Idempotent)")
        self.stdout.write("=" * 80)

        try:
            with transaction.atomic():
                # A) Create/update Category
                category, cat_created = Category.objects.update_or_create(
                    slug="pisirme-uniteleri",
                    defaults={
                        "name": "Pişirme Üniteleri",
                        "menu_label": "Pişirme",
                        "description_short": "Profesyonel pişirme ekipmanları",
                        "order": 10,
                        "is_featured": True,
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] Category: {category.name} ({category.slug}) "
                        f"[{'CREATED' if cat_created else 'UPDATED'}]"
                    )
                )

                # B) Create/update Brand
                brand, brand_created = Brand.objects.update_or_create(
                    slug="gastrotech-test",
                    defaults={
                        "name": "Gastrotech Test",
                        "description": "Test brand for QA/UAT validation",
                        "is_active": True,
                        "order": 100,
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] Brand: {brand.name} ({brand.slug}) "
                        f"[{'CREATED' if brand_created else 'UPDATED'}]"
                    )
                )

                # C) Link Brand to Category (M2M through BrandCategory)
                brand_cat, bc_created = BrandCategory.objects.get_or_create(
                    brand=brand,
                    category=category,
                    defaults={
                        "is_active": True,
                        "order": 10,
                    }
                )
                if not bc_created:
                    brand_cat.is_active = True
                    brand_cat.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] BrandCategory link: {brand.name} <-> {category.name} "
                        f"[{'CREATED' if bc_created else 'EXISTS'}]"
                    )
                )

                # D) Create/update Series 1: 700 Serisi
                series700, s700_created = Series.objects.update_or_create(
                    slug="700-serisi-test",
                    defaults={
                        "category": category,
                        "name": "700 Serisi (Test)",
                        "description_short": "Test serisi - 700 serisi kompakt ekipmanlar",
                        "order": 20,
                        "is_featured": True,
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] Series 1: {series700.name} ({series700.slug}) in {category.name} "
                        f"[{'CREATED' if s700_created else 'UPDATED'}]"
                    )
                )

                # E) Create/update Series 2: 900 Serisi
                series900, s900_created = Series.objects.update_or_create(
                    slug="900-serisi-test",
                    defaults={
                        "category": category,
                        "name": "900 Serisi (Test)",
                        "description_short": "Test serisi - 900 serisi endüstriyel ekipmanlar",
                        "order": 30,
                        "is_featured": False,
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] Series 2: {series900.name} ({series900.slug}) in {category.name} "
                        f"[{'CREATED' if s900_created else 'UPDATED'}]"
                    )
                )

                # F) Create/update Product 1 (700 Serisi): Kompakt Ocak
                product700_1, p700_1_created = Product.objects.update_or_create(
                    slug="test-kompakt-ocak-700",
                    defaults={
                        "series": series700,
                        "brand": brand,
                        "name": "Test Kompakt Ocak",
                        "title_tr": "Test Kompakt Ocak (700)",
                        "title_en": "Test Compact Range (700)",
                        "status": "active",
                        "is_featured": False,
                        "general_features": [
                            "Kompakt tasarım",
                            "Paslanmaz çelik gövde",
                            "LPG / Doğalgaz uyumlu",
                            "Enerji tasarruflu",
                        ],
                        "short_specs": [
                            "12 kW güç",
                            "Kompakt boyut",
                            "LPG/NG",
                        ],
                        "notes": [
                            "Test ürünü - 700 Serisi",
                        ],
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] Product 1 (700): {product700_1.title_tr} ({product700_1.slug}) "
                        f"[{'CREATED' if p700_1_created else 'UPDATED'}]"
                    )
                )

                # G) Create/update Product 2 (700 Serisi): Fritöz
                product700_2, p700_2_created = Product.objects.update_or_create(
                    slug="test-fritoz-700",
                    defaults={
                        "series": series700,
                        "brand": brand,
                        "name": "Test Fritöz",
                        "title_tr": "Test Elektrikli Fritöz (700)",
                        "title_en": "Test Electric Fryer (700)",
                        "status": "active",
                        "is_featured": True,
                        "general_features": [
                            "Elektrikli fritöz",
                            "Ayarlanabilir sıcaklık kontrolü",
                            "Paslanmaz çelik tank",
                            "Güvenlik termostatı",
                        ],
                        "short_specs": [
                            "6 kW elektrik",
                            "8 litre kapasite",
                            "Dijital kontrol",
                        ],
                        "notes": [
                            "Test ürünü - 700 Serisi Fritöz",
                        ],
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] Product 2 (700): {product700_2.title_tr} ({product700_2.slug}) "
                        f"[{'CREATED' if p700_2_created else 'UPDATED'}]"
                    )
                )

                # H) Create/update Product 3 (900 Serisi): Endüstriyel Ocak
                product900_1, p900_1_created = Product.objects.update_or_create(
                    slug="test-endustriyel-ocak-900",
                    defaults={
                        "series": series900,
                        "brand": brand,
                        "name": "Test Endüstriyel Ocak",
                        "title_tr": "Test Endüstriyel Ocak (900)",
                        "title_en": "Test Industrial Range (900)",
                        "status": "active",
                        "is_featured": False,
                        "general_features": [
                            "Paslanmaz çelik gövde (Stainless Steel body)",
                            "LPG / Doğalgaz uyumlu (LPG / NG compatible)",
                            "Termostat korumalı emniyet sistemi (Thermostat safety system)",
                            "Endüstriyel kullanım için tasarlanmıştır (Designed for industrial use)",
                        ],
                        "short_specs": [
                            "24 kW toplam güç",
                            "Paslanmaz çelik",
                            "LPG/NG uyumlu",
                        ],
                        "notes": [
                            "Test ürünüdür - QA/UAT için oluşturulmuştur",
                            "This is a test product for QA/UAT validation",
                        ],
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] Product 3 (900): {product900_1.title_tr} ({product900_1.slug}) "
                        f"[{'CREATED' if p900_1_created else 'UPDATED'}]"
                    )
                )

                # I) Create/update Product 4 (900 Serisi): Fırın
                product900_2, p900_2_created = Product.objects.update_or_create(
                    slug="test-endustriyel-firin-900",
                    defaults={
                        "series": series900,
                        "brand": brand,
                        "name": "Test Endüstriyel Fırın",
                        "title_tr": "Test Endüstriyel Konveksiyonlu Fırın (900)",
                        "title_en": "Test Industrial Convection Oven (900)",
                        "status": "active",
                        "is_featured": True,
                        "general_features": [
                            "Konveksiyonlu pişirme",
                            "Dijital sıcaklık kontrolü",
                            "Çift camlı kapı",
                            "5 tepsi kapasitesi",
                        ],
                        "short_specs": [
                            "15 kW elektrik",
                            "5 tepsi",
                            "Dijital kontrol",
                        ],
                        "notes": [
                            "Test ürünü - 900 Serisi Fırın",
                        ],
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] Product 4 (900): {product900_2.title_tr} ({product900_2.slug}) "
                        f"[{'CREATED' if p900_2_created else 'UPDATED'}]"
                    )
                )

                # J) Create variants for Product 1 (700 - Kompakt Ocak)
                v700_1_1, v700_1_1_created = Variant.objects.update_or_create(
                    model_code="TEST-KO-700-001",
                    defaults={
                        "product": product700_1,
                        "name_tr": "2 Gözlü",
                        "name_en": "2 Burner",
                        "dimensions": "400x700x280",
                        "weight_kg": Decimal("45.0"),
                        "list_price": Decimal("12999.90"),
                        "stock_qty": 15,
                        "specs": {
                            "power": "8 kW",
                            "gas_type": "LPG / NG",
                            "burner_count": "2",
                            "body_material": "Stainless Steel",
                        },
                    }
                )

                v700_1_2, v700_1_2_created = Variant.objects.update_or_create(
                    model_code="TEST-KO-700-002",
                    defaults={
                        "product": product700_1,
                        "name_tr": "4 Gözlü",
                        "name_en": "4 Burner",
                        "dimensions": "800x700x280",
                        "weight_kg": Decimal("65.0"),
                        "list_price": Decimal("16999.90"),
                        "stock_qty": 10,
                        "specs": {
                            "power": "12 kW",
                            "gas_type": "LPG / NG",
                            "burner_count": "4",
                            "body_material": "Stainless Steel",
                        },
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(f"[OK] Product 1 variants: 2 variants created/updated")
                )

                # K) Create variants for Product 2 (700 - Fritöz)
                v700_2_1, v700_2_1_created = Variant.objects.update_or_create(
                    model_code="TEST-FR-700-001",
                    defaults={
                        "product": product700_2,
                        "name_tr": "8L Tek Hazneli",
                        "name_en": "8L Single Tank",
                        "dimensions": "300x600x350",
                        "weight_kg": Decimal("25.0"),
                        "list_price": Decimal("9999.90"),
                        "stock_qty": 20,
                        "specs": {
                            "power": "6 kW",
                            "capacity": "8 liters",
                            "type": "Electric",
                            "body_material": "Stainless Steel",
                        },
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(f"[OK] Product 2 variants: 1 variant created/updated")
                )

                # L) Create variants for Product 3 (900 - Endüstriyel Ocak)
                v900_1_1, v900_1_1_created = Variant.objects.update_or_create(
                    model_code="TEST-EO-900-001",
                    defaults={
                        "product": product900_1,
                        "name_tr": "4 Gözlü",
                        "name_en": "4 Burner",
                        "dimensions": "800x900x280",
                        "weight_kg": Decimal("95.0"),
                        "list_price": Decimal("24999.90"),
                        "stock_qty": 7,
                        "specs": {
                            "power": "20 kW",
                            "gas_type": "LPG / NG",
                            "burner_count": "4",
                            "body_material": "Stainless Steel",
                            "safety": "Thermocouple",
                        },
                    }
                )

                v900_1_2, v900_1_2_created = Variant.objects.update_or_create(
                    model_code="TEST-EO-900-002",
                    defaults={
                        "product": product900_1,
                        "name_tr": "6 Gözlü",
                        "name_en": "6 Burner",
                        "dimensions": "1200x900x280",
                        "weight_kg": Decimal("120.0"),
                        "list_price": Decimal("32999.90"),
                        "stock_qty": 5,
                        "specs": {
                            "power": "30 kW",
                            "gas_type": "LPG / NG",
                            "burner_count": "6",
                            "body_material": "Stainless Steel",
                            "safety": "Thermocouple",
                        },
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(f"[OK] Product 3 variants: 2 variants created/updated")
                )

                # M) Create variants for Product 4 (900 - Fırın)
                v900_2_1, v900_2_1_created = Variant.objects.update_or_create(
                    model_code="TEST-FI-900-001",
                    defaults={
                        "product": product900_2,
                        "name_tr": "5 Tepsi",
                        "name_en": "5 Tray",
                        "dimensions": "800x800x900",
                        "weight_kg": Decimal("150.0"),
                        "list_price": Decimal("45999.90"),
                        "stock_qty": 3,
                        "specs": {
                            "power": "15 kW",
                            "tray_count": "5",
                            "type": "Electric Convection",
                            "body_material": "Stainless Steel",
                            "control": "Digital",
                        },
                    }
                )

                v900_2_2, v900_2_2_created = Variant.objects.update_or_create(
                    model_code="TEST-FI-900-002",
                    defaults={
                        "product": product900_2,
                        "name_tr": "10 Tepsi",
                        "name_en": "10 Tray",
                        "dimensions": "1000x1000x1200",
                        "weight_kg": Decimal("220.0"),
                        "list_price": Decimal("67999.90"),
                        "stock_qty": 2,
                        "specs": {
                            "power": "25 kW",
                            "tray_count": "10",
                            "type": "Electric Convection",
                            "body_material": "Stainless Steel",
                            "control": "Digital",
                        },
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(f"[OK] Product 4 variants: 2 variants created/updated")
                )

                # N) Verification
                self.stdout.write("\n" + "=" * 80)
                self.stdout.write("VERIFICATION CHECKS")
                self.stdout.write("=" * 80)

                # Check 1: All products' series.category == Category
                all_products = [product700_1, product700_2, product900_1, product900_2]
                for prod in all_products:
                    if prod.series.category != category:
                        raise CommandError(
                            f"Data integrity error: Product {prod.slug} series category "
                            f"({prod.series.category}) != Category ({category})"
                        )
                self.stdout.write(
                    self.style.SUCCESS("[OK] All products' series.category matches Category")
                )

                # Check 2: Series count
                series_count = Series.objects.filter(category=category, slug__contains="test").count()
                if series_count < 2:
                    raise CommandError(f"Expected at least 2 series, found {series_count}")
                self.stdout.write(
                    self.style.SUCCESS(f"[OK] {series_count} series created")
                )

                # Check 3: Product count
                product_count = Product.objects.filter(slug__contains="test").count()
                if product_count < 4:
                    raise CommandError(f"Expected at least 4 products, found {product_count}")
                self.stdout.write(
                    self.style.SUCCESS(f"[OK] {product_count} products created")
                )

                # Check 4: Variant count
                variant_count = Variant.objects.filter(model_code__contains="TEST").count()
                if variant_count < 7:
                    raise CommandError(f"Expected at least 7 variants, found {variant_count}")
                self.stdout.write(
                    self.style.SUCCESS(f"[OK] {variant_count} variants created")
                )

                # Check 5: All variants have required fields
                all_variants = Variant.objects.filter(model_code__contains="TEST")
                for variant in all_variants:
                    if not variant.list_price:
                        raise CommandError(f"Variant {variant.model_code} missing list_price")
                    if variant.stock_qty is None:
                        raise CommandError(f"Variant {variant.model_code} missing stock_qty")
                    if not variant.specs:
                        raise CommandError(f"Variant {variant.model_code} missing specs")
                self.stdout.write(
                    self.style.SUCCESS("[OK] All variants have required fields (price, stock, specs)")
                )

                # Check 6: Brand-Category link exists
                if not BrandCategory.objects.filter(brand=brand, category=category).exists():
                    raise CommandError(f"BrandCategory link not found for {brand} - {category}")
                self.stdout.write(
                    self.style.SUCCESS("[OK] Brand-Category M2M relationship exists")
                )

                # O) Summary
                self.stdout.write("\n" + "=" * 80)
                self.stdout.write("SUCCESS - Test Catalog Data Created/Updated")
                self.stdout.write("=" * 80)
                self.stdout.write("\nHierarchy Created:")
                self.stdout.write(f"  1 Category: {category.name}")
                self.stdout.write(f"  1 Brand: {brand.name}")
                self.stdout.write(f"  2 Series:")
                self.stdout.write(f"    - {series700.name} (featured)")
                self.stdout.write(f"    - {series900.name}")
                self.stdout.write(f"  4 Products:")
                self.stdout.write(f"    - {product700_1.title_tr} (2 variants)")
                self.stdout.write(f"    - {product700_2.title_tr} (1 variant, featured)")
                self.stdout.write(f"    - {product900_1.title_tr} (2 variants)")
                self.stdout.write(f"    - {product900_2.title_tr} (2 variants, featured)")
                self.stdout.write(f"  7 Total Variants")

                self.stdout.write("\nFrontend Navigation URLs:")
                self.stdout.write(f"  1. Categories List: /catalog/categories/list")
                self.stdout.write(f"  2. Category Detail: /catalog/categories/{category.slug}")
                self.stdout.write(f"  3. Filter by 700 Series: /catalog/products?category={category.slug}&series={series700.slug}")
                self.stdout.write(f"  4. Filter by 900 Series: /catalog/products?category={category.slug}&series={series900.slug}")
                self.stdout.write(f"  5. Product Details:")
                self.stdout.write(f"     - /catalog/products/{product700_1.slug}")
                self.stdout.write(f"     - /catalog/products/{product700_2.slug}")
                self.stdout.write(f"     - /catalog/products/{product900_1.slug}")
                self.stdout.write(f"     - /catalog/products/{product900_2.slug}")

                self.stdout.write("\nDatabase IDs:")
                self.stdout.write(f"  Category: {category.id}")
                self.stdout.write(f"  Brand: {brand.id}")
                self.stdout.write(f"  Series 700: {series700.id}")
                self.stdout.write(f"  Series 900: {series900.id}")

                self.stdout.write("\n" + "=" * 80)

        except Exception as e:
            raise CommandError(f"Failed to create test catalog item: {str(e)}")
