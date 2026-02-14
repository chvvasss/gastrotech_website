from io import BytesIO
import pandas as pd
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.catalog.models import Category, Series, Product, Variant, Brand, TaxonomyNode
from apps.catalog.services.bulk_upload import BulkUploadService


class BulkUploadServiceTests(TestCase):
    def setUp(self):
        # Create some base data if needed, but we mostly test creation from scratch
        pass

    def create_excel_file(self, data):
        """Helper to create an Excel file in memory."""
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return output

    def test_validation_empty_file(self):
        """Test that empty file raises validation error."""
        data = []
        file = self.create_excel_file(data)
        service = BulkUploadService(file)
        
        # Depending on implementation, pd.read_excel might fail directly or we check empty
        # We need to catch the validation error
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            service.validate_and_parse()

    def test_missing_columns(self):
        """Test missing required columns."""
        data = [{"Brand": "Test"}] # Missing Category, Series etc.
        file = self.create_excel_file(data)
        service = BulkUploadService(file)
        
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError) as cm:
            service.validate_and_parse()
        self.assertIn("Missing required columns", str(cm.exception))

    def test_successful_creation(self):
        """Test full creation flow."""
        data = [{
            "Brand": "Gastrotech",
            "Category": "Cooking",
            "Series": "900 Series",
            "Taxonomy": "Cookers > Gas",
            "Product Name": "Gas Cooker 4 Burner",
            "Model Code": "GKO9010",
            "Title TR": "Gazlı Ocak 4'lü",
            "Price": 1500.00,
            "Spec:Power": "20kW"
        }]
        
        file = self.create_excel_file(data)
        service = BulkUploadService(file)
        
        # 1. Validate
        service.validate_and_parse()
        
        # 2. Process (Real run)
        results = service.process_data(dry_run=False)
        
        print("Results:", results)
        
        self.assertEqual(results["errors"], [])
        self.assertEqual(results["brands_created"], 1)
        self.assertEqual(results["categories_created"], 1)
        self.assertEqual(results["series_created"], 1)
        self.assertEqual(results["products_created"], 1)
        self.assertEqual(results["variants_created"], 1)
        
        # Verify DB
        self.assertTrue(Brand.objects.filter(name="Gastrotech").exists())
        cat = Category.objects.get(name="Cooking")
        series = Series.objects.get(name="900 Series", category=cat)
        # Check taxonomy
        node_gas = TaxonomyNode.objects.get(name="Gas")
        node_cookers = TaxonomyNode.objects.get(name="Cookers")
        self.assertEqual(node_gas.parent, node_cookers)
        self.assertEqual(node_cookers.series, series)
        
        product = Product.objects.get(slug="gazli-ocak-4lu") # slugify_tr
        self.assertEqual(product.series, series)
        self.assertEqual(product.brand.name, "Gastrotech")
        self.assertEqual(product.primary_node, node_gas)
        
        variant = Variant.objects.get(model_code="GKO9010")
        self.assertEqual(variant.product, product)
        self.assertEqual(variant.specs.get("power"), "20kW") # slugified key

    def test_dry_run_rollback(self):
        """Test that dry run does not persist data."""
        data = [{
            "Brand": "NewBrand",
            "Category": "NewCat",
            "Series": "NewSeries",
            "Product Name": "Test Prod",
            "Model Code": "TEST001",
            "Title TR": "Test TR",
        }]
        file = self.create_excel_file(data)
        service = BulkUploadService(file)
        
        results = service.process_data(dry_run=True)
        
        self.assertEqual(results["errors"], [])
        self.assertEqual(results["brands_created"], 1)
        
        # Verify NOTHING was created
        self.assertFalse(Brand.objects.filter(name="NewBrand").exists())
        self.assertFalse(Category.objects.filter(name="NewCat").exists())
