"""
Tests for create_test_catalog_item management command.

Verifies:
- Command creates all required entities
- Command is idempotent (no duplicates on re-run)
- All entities are properly linked
- Data integrity is maintained
"""

from django.core.management import call_command
from django.test import TestCase

from apps.catalog.models import Category, Brand, BrandCategory, Series, Product, Variant


class CreateTestCatalogItemCommandTestCase(TestCase):
    """Test cases for create_test_catalog_item command."""

    def test_command_creates_all_entities(self):
        """Test that command creates category, brand, series, product, and variants."""
        # Run the command
        call_command("create_test_catalog_item")

        # Verify Category exists
        category = Category.objects.get(slug="pisirme-uniteleri")
        self.assertEqual(category.name, "Pişirme Üniteleri")
        self.assertEqual(category.menu_label, "Pişirme")
        self.assertTrue(category.is_featured)

        # Verify Brand exists
        brand = Brand.objects.get(slug="gastrotech-test")
        self.assertEqual(brand.name, "Gastrotech Test")
        self.assertTrue(brand.is_active)

        # Verify BrandCategory link exists
        self.assertTrue(
            BrandCategory.objects.filter(brand=brand, category=category).exists()
        )

        # Verify Series exists
        series = Series.objects.get(slug="900-serisi-test")
        self.assertEqual(series.name, "900 Serisi (Test)")
        self.assertEqual(series.category, category)

        # Verify Product exists
        product = Product.objects.get(slug="test-endustriyel-ocak")
        self.assertEqual(product.title_tr, "Test Endüstriyel Ocak")
        self.assertEqual(product.title_en, "Test Industrial Range")
        self.assertEqual(product.series, series)
        self.assertEqual(product.brand, brand)
        self.assertEqual(product.status, "active")
        self.assertFalse(product.is_featured)

        # Verify general_features are populated
        self.assertIsInstance(product.general_features, list)
        self.assertGreater(len(product.general_features), 0)

        # Verify short_specs are populated
        self.assertIsInstance(product.short_specs, list)
        self.assertGreater(len(product.short_specs), 0)

        # Verify Variants exist
        variant1 = Variant.objects.get(model_code="TEST-OC-900-001")
        self.assertEqual(variant1.name_tr, "4 Gözlü (Test)")
        self.assertEqual(variant1.name_en, "4 Burner (Test)")
        self.assertEqual(variant1.product, product)
        self.assertEqual(str(variant1.list_price), "19999.90")
        self.assertEqual(variant1.stock_qty, 7)
        self.assertEqual(variant1.dimensions, "800x700x280")
        self.assertEqual(str(variant1.weight_kg), "78.500")

        # Verify variant1 specs
        self.assertIsInstance(variant1.specs, dict)
        self.assertEqual(variant1.specs["power"], "18 kW")
        self.assertEqual(variant1.specs["burner_count"], "4")

        variant2 = Variant.objects.get(model_code="TEST-OC-900-002")
        self.assertEqual(variant2.name_tr, "6 Gözlü (Test)")
        self.assertEqual(variant2.name_en, "6 Burner (Test)")
        self.assertEqual(variant2.product, product)
        self.assertEqual(str(variant2.list_price), "24999.90")
        self.assertEqual(variant2.stock_qty, 3)
        self.assertEqual(variant2.dimensions, "1000x700x280")
        self.assertEqual(str(variant2.weight_kg), "92.000")

        # Verify variant2 specs
        self.assertIsInstance(variant2.specs, dict)
        self.assertEqual(variant2.specs["power"], "27 kW")
        self.assertEqual(variant2.specs["burner_count"], "6")

    def test_command_is_idempotent(self):
        """Test that running command multiple times doesn't create duplicates."""
        # Run command first time
        call_command("create_test_catalog_item")

        # Count entities
        category_count_1 = Category.objects.filter(slug="pisirme-uniteleri").count()
        brand_count_1 = Brand.objects.filter(slug="gastrotech-test").count()
        series_count_1 = Series.objects.filter(slug="900-serisi-test").count()
        product_count_1 = Product.objects.filter(slug="test-endustriyel-ocak").count()
        variant1_count_1 = Variant.objects.filter(model_code="TEST-OC-900-001").count()
        variant2_count_1 = Variant.objects.filter(model_code="TEST-OC-900-002").count()

        # All should be 1
        self.assertEqual(category_count_1, 1)
        self.assertEqual(brand_count_1, 1)
        self.assertEqual(series_count_1, 1)
        self.assertEqual(product_count_1, 1)
        self.assertEqual(variant1_count_1, 1)
        self.assertEqual(variant2_count_1, 1)

        # Run command second time
        call_command("create_test_catalog_item")

        # Count entities again
        category_count_2 = Category.objects.filter(slug="pisirme-uniteleri").count()
        brand_count_2 = Brand.objects.filter(slug="gastrotech-test").count()
        series_count_2 = Series.objects.filter(slug="900-serisi-test").count()
        product_count_2 = Product.objects.filter(slug="test-endustriyel-ocak").count()
        variant1_count_2 = Variant.objects.filter(model_code="TEST-OC-900-001").count()
        variant2_count_2 = Variant.objects.filter(model_code="TEST-OC-900-002").count()

        # Counts should remain 1 (no duplicates)
        self.assertEqual(category_count_2, 1)
        self.assertEqual(brand_count_2, 1)
        self.assertEqual(series_count_2, 1)
        self.assertEqual(product_count_2, 1)
        self.assertEqual(variant1_count_2, 1)
        self.assertEqual(variant2_count_2, 1)

    def test_data_integrity(self):
        """Test that all entities are properly linked and maintain data integrity."""
        # Run the command
        call_command("create_test_catalog_item")

        # Get all entities
        category = Category.objects.get(slug="pisirme-uniteleri")
        brand = Brand.objects.get(slug="gastrotech-test")
        series = Series.objects.get(slug="900-serisi-test")
        product = Product.objects.get(slug="test-endustriyel-ocak")

        # Check 1: Series category matches product's series category
        self.assertEqual(product.series.category, category)

        # Check 2: Product has exactly 2 variants
        variant_count = product.variants.count()
        self.assertEqual(variant_count, 2)

        # Check 3: All variants have required fields
        for variant in product.variants.all():
            self.assertIsNotNone(variant.list_price)
            self.assertIsNotNone(variant.stock_qty)
            self.assertTrue(variant.specs)  # specs dict should not be empty
            self.assertTrue(variant.name_tr)
            self.assertTrue(variant.dimensions)
            self.assertIsNotNone(variant.weight_kg)

        # Check 4: Brand-Category M2M exists
        self.assertTrue(
            BrandCategory.objects.filter(brand=brand, category=category).exists()
        )

        # Check 5: Product brand and series are correctly linked
        self.assertEqual(product.brand, brand)
        self.assertEqual(product.series, series)
        self.assertEqual(series.category, category)
