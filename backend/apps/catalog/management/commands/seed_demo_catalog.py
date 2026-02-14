"""
Seed command to populate demo catalog data for Gastrotech.

Creates categories, series, taxonomy nodes, products (catalog groups),
variants (model lines), and spec keys.

Idempotent: safe to run multiple times without duplicating data.

Usage:
    python manage.py seed_demo_catalog
    python manage.py seed_demo_catalog --clear
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.models import (
    Category,
    Media,
    Product,
    ProductMedia,
    ProductNode,
    Series,
    SpecKey,
    TaxonomyNode,
    Variant,
)


class Command(BaseCommand):
    help = "Seed demo catalog data for Gastrotech"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = {
            "categories": 0,
            "series": 0,
            "nodes": 0,
            "products": 0,
            "variants": 0,
            "spec_keys": 0,
            "media": 0,
        }
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing catalog data before seeding",
        )
        parser.add_argument(
            "--generate-leaf-products",
            action="store_true",
            help="Generate Product groups for all leaf taxonomy nodes",
        )
    
    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("\n🚀 Seeding Gastrotech catalog...\n"))
        
        if options["clear"]:
            self.clear_data()
        
        # Create spec keys first
        spec_keys = self.create_spec_keys()
        
        # Create categories
        categories = self.create_categories()
        
        # Create series for Pişirme Üniteleri
        pisirme = categories["pisirme"]
        series_data = self.create_series(pisirme)
        
        # Create taxonomy nodes for 600 Series
        series_600 = series_data["600"]
        taxonomy_600 = self.create_taxonomy_nodes_600(series_600)
        
        # Create product groups with variants
        self.create_product_groups(series_600, taxonomy_600, spec_keys)
        
        # Generate products for leaf nodes if requested
        if options["generate_leaf_products"]:
            self.generate_leaf_products(series_600)
        
        # Print summary
        self.print_summary()
    
    def clear_data(self):
        """Clear all existing catalog data."""
        self.stdout.write(self.style.WARNING("Clearing existing catalog data..."))
        ProductMedia.objects.all().delete()
        ProductNode.objects.all().delete()
        Variant.objects.all().delete()
        Product.objects.all().delete()
        TaxonomyNode.objects.all().delete()
        Series.objects.all().delete()
        Category.objects.all().delete()
        SpecKey.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("  ✓ Data cleared\n"))
    
    def create_spec_keys(self):
        """Create specification keys for catalog tables."""
        self.stdout.write("Creating spec keys...")
        
        spec_key_data = [
            {
                "slug": "goz-adedi",
                "label_tr": "Göz Adedi",
                "label_en": "Number of Burners",
                "value_type": "int",
                "sort_order": 1,
            },
            {
                "slug": "guc-kw",
                "label_tr": "Güç",
                "label_en": "Power",
                "unit": "kW",
                "value_type": "decimal",
                "sort_order": 2,
            },
            {
                "slug": "gaz-baglantisi",
                "label_tr": "Gaz Bağlantısı",
                "label_en": "Gas Connection",
                "value_type": "text",
                "sort_order": 3,
            },
            {
                "slug": "boyutlar",
                "label_tr": "Boyutlar (GxDxY)",
                "label_en": "Dimensions (WxDxH)",
                "unit": "mm",
                "value_type": "text",
                "sort_order": 4,
            },
            {
                "slug": "agirlik",
                "label_tr": "Ağırlık",
                "label_en": "Weight",
                "unit": "kg",
                "value_type": "decimal",
                "sort_order": 5,
            },
            {
                "slug": "elektrik-baglantisi",
                "label_tr": "Elektrik Bağlantısı",
                "label_en": "Electrical Connection",
                "value_type": "text",
                "sort_order": 6,
            },
            {
                "slug": "wok-capi",
                "label_tr": "Wok Çapı",
                "label_en": "Wok Diameter",
                "unit": "mm",
                "value_type": "int",
                "sort_order": 7,
            },
        ]
        
        spec_keys = {}
        for data in spec_key_data:
            sk, created = SpecKey.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "label_tr": data["label_tr"],
                    "label_en": data.get("label_en", ""),
                    "unit": data.get("unit", ""),
                    "value_type": data.get("value_type", "text"),
                    "sort_order": data.get("sort_order", 0),
                },
            )
            if created:
                self.stats["spec_keys"] += 1
                self.stdout.write(f"  ✓ Created: {sk.label_tr}")
            spec_keys[data["slug"]] = sk
        
        return spec_keys
    
    def create_categories(self):
        """Create main product categories."""
        self.stdout.write("\nCreating categories...")
        
        category_data = [
            {"name": "Pişirme Üniteleri", "order": 1, "is_featured": True},
            {"name": "Fırınlar", "order": 2, "is_featured": True},
            {"name": "Soğutma Üniteleri", "order": 3, "is_featured": True},
            {"name": "Hazırlık Ekipmanları", "order": 4},
            {"name": "Kahve Ekipmanları", "order": 5},
            {"name": "Bulaşıkhane", "order": 6},
            {"name": "Çamaşırhane", "order": 7},
            {"name": "Tamamlayıcı", "order": 8},
        ]
        
        categories = {}
        for data in category_data:
            cat, created = Category.objects.get_or_create(
                slug=slugify(data["name"]),
                defaults={
                    "name": data["name"],
                    "order": data["order"],
                    "is_featured": data.get("is_featured", False),
                    "description_short": f"{data['name']} profesyonel mutfak ekipmanları",
                },
            )
            if created:
                self.stats["categories"] += 1
                self.stdout.write(f"  ✓ Created: {cat.name}")
            else:
                self.stdout.write(f"  - Exists: {cat.name}")
            
            if "Pişirme" in cat.name:
                categories["pisirme"] = cat
        
        return categories
    
    def create_series(self, category):
        """Create series for the given category."""
        self.stdout.write(f"\nCreating series for {category.name}...")
        
        series_data = [
            {"name": "600 Serisi", "slug": "600", "order": 1, "is_featured": True},
            {"name": "700 Serisi", "slug": "700", "order": 2, "is_featured": True},
            {"name": "900 Serisi", "slug": "900", "order": 3, "is_featured": True},
            {"name": "Drop-in", "slug": "drop-in", "order": 4},
            {"name": "Eko Seri", "slug": "eko", "order": 5},
            {"name": "Banket", "slug": "banket", "order": 6},
        ]
        
        series_objs = {}
        for data in series_data:
            s, created = Series.objects.get_or_create(
                category=category,
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "order": data["order"],
                    "is_featured": data.get("is_featured", False),
                    "description_short": f"{data['name']} profesyonel pişirme ekipmanları",
                },
            )
            if created:
                self.stats["series"] += 1
                self.stdout.write(f"  ✓ Created: {s.name}")
            else:
                self.stdout.write(f"  - Exists: {s.name}")
            
            series_objs[data["slug"]] = s
        
        return series_objs
    
    def create_taxonomy_nodes_600(self, series):
        """Create expanded taxonomy tree for 600 series with parent and leaf nodes."""
        self.stdout.write(f"\nCreating taxonomy for {series.name}...")
        
        nodes = {}
        
        # Parent nodes (categories)
        parent_data = [
            {"name": "Ocaklar", "slug": "ocaklar", "order": 1},
            {"name": "Kuzineler", "slug": "kuzineler", "order": 2},
            {"name": "Izgaralar", "slug": "izgaralar", "order": 3},
            {"name": "Fritözler", "slug": "fritozler", "order": 4},
            {"name": "Pişiriciler", "slug": "pisiriciler", "order": 5},
            {"name": "Ara Tezgahlar", "slug": "ara-tezgahlar", "order": 6},
            {"name": "Alt Stant", "slug": "alt-stant", "order": 7},
        ]
        
        for data in parent_data:
            node, created = TaxonomyNode.objects.get_or_create(
                series=series,
                slug=data["slug"],
                parent=None,
                defaults={
                    "name": data["name"],
                    "order": data["order"],
                },
            )
            if created:
                self.stats["nodes"] += 1
                self.stdout.write(f"  ✓ Created parent: {node.name}")
            nodes[data["slug"]] = node
        
        # Leaf nodes under parents
        leaf_data = [
            # Under Ocaklar
            {"parent": "ocaklar", "name": "Gazlı Ocaklar", "slug": "gazli-ocaklar", "order": 1},
            {"parent": "ocaklar", "name": "Gazlı Wok Ocaklar", "slug": "gazli-wok-ocaklar", "order": 2},
            {"parent": "ocaklar", "name": "Elektrikli Ocaklar", "slug": "elektrikli-ocaklar", "order": 3},
            {"parent": "ocaklar", "name": "İndüksiyon Ocaklar", "slug": "induksiyon-ocaklar", "order": 4},
            # Under Kuzineler
            {"parent": "kuzineler", "name": "Gazlı Kuzineler", "slug": "gazli-kuzineler", "order": 1},
            {"parent": "kuzineler", "name": "Elektrikli Kuzineler", "slug": "elektrikli-kuzineler", "order": 2},
            # Under Izgaralar
            {"parent": "izgaralar", "name": "Lavalı Izgara", "slug": "lavali-izgara", "order": 1},
            {"parent": "izgaralar", "name": "Elektrikli Izgara", "slug": "elektrikli-izgara", "order": 2},
            {"parent": "izgaralar", "name": "Kömürlü Izgara", "slug": "komurlu-izgara", "order": 3},
            # Under Fritözler
            {"parent": "fritozler", "name": "Gazlı Fritöz", "slug": "gazli-fritoz", "order": 1},
            {"parent": "fritozler", "name": "Elektrikli Fritöz", "slug": "elektrikli-fritoz", "order": 2},
            # Under Pişiriciler
            {"parent": "pisiriciler", "name": "Makarna Pişirici", "slug": "makarna-pisirici", "order": 1},
            {"parent": "pisiriciler", "name": "Benmari", "slug": "benmari", "order": 2},
            # Under Ara Tezgahlar
            {"parent": "ara-tezgahlar", "name": "Nötr Tezgah", "slug": "notr-tezgah", "order": 1},
            # Under Alt Stant
            {"parent": "alt-stant", "name": "Açık Alt Stant", "slug": "acik-alt-stant", "order": 1},
            {"parent": "alt-stant", "name": "Kapaklı Alt Stant", "slug": "kapakli-alt-stant", "order": 2},
        ]
        
        for data in leaf_data:
            parent_node = nodes.get(data["parent"])
            if parent_node:
                node, created = TaxonomyNode.objects.get_or_create(
                    series=series,
                    slug=data["slug"],
                    parent=parent_node,
                    defaults={
                        "name": data["name"],
                        "order": data["order"],
                    },
                )
                if created:
                    self.stats["nodes"] += 1
                    self.stdout.write(f"    ✓ Created leaf: {parent_node.name} > {node.name}")
                nodes[data["slug"]] = node
        
        return nodes
    
    def create_product_groups(self, series, taxonomy, spec_keys):
        """Create product groups with variants matching PDF catalog style."""
        self.stdout.write(f"\nCreating product groups for {series.name}...")
        
        # Product Group 1: Gazlı Ocaklar
        self.create_gazli_ocaklar_group(series, taxonomy, spec_keys)
        
        # Product Group 2: Gazlı Wok Ocaklar
        self.create_gazli_wok_group(series, taxonomy, spec_keys)
        
        # Product Group 3: Elektrikli Fritözler
        self.create_elektrikli_fritoz_group(series, taxonomy, spec_keys)
        
        # Product Group 4: Lavalı Izgaralar
        self.create_lavali_izgara_group(series, taxonomy, spec_keys)
        
        # Product Group 5: Makarna Pişiriciler
        self.create_makarna_pisirici_group(series, taxonomy, spec_keys)
    
    def create_gazli_ocaklar_group(self, series, taxonomy, spec_keys):
        """Create Gazlı Ocaklar product group with variants."""
        
        general_features = [
            "Paslanmaz çelik gövde",
            "Pres baskı yekpare üst tabla (1 mm kalınlık)",
            "Ø 100 mm yüksek verimli brülörler",
            "Koruyucu iç emaye kaplama",
            "Termoelektrik emniyet sistemi (FFD)",
            "Döküm ızgaralar",
            "Çıkarılabilir ve kolay temizlenebilir brülör başlıkları",
            "Kolaylıkla ulaşılabilir ayarlanabilir ayaklar",
        ]
        
        notes = [
            "1 mm kalınlık paslanmaz çelik üst tabla standart olarak sunulmaktadır.",
            "Tüm modeller CE standartlarına uygundur.",
        ]
        
        spec_layout = ["goz-adedi", "guc-kw", "boyutlar", "agirlik", "gaz-baglantisi"]
        
        product, created = Product.objects.get_or_create(
            slug="600-serisi-gazli-ocaklar",
            defaults={
                "name": "600 Serisi Gazlı Ocaklar",
                "title_tr": "Gazlı Ocaklar",
                "title_en": "Gas Ranges",
                "series": series,
                "primary_node": taxonomy.get("gazli-ocaklar"),
                "status": Product.Status.ACTIVE,
                "is_featured": True,
                "general_features": general_features,
                "notes": notes,
                "spec_layout": spec_layout,
                "pdf_ref": "p9",
                "short_specs": general_features[:5],
            },
        )
        
        if created:
            self.stats["products"] += 1
            self.stdout.write(f"  ✓ Created Product: {product.title_tr}")
            
            # Add to taxonomy
            ProductNode.objects.get_or_create(
                product=product,
                node=taxonomy["gazli-ocaklar"],
            )
            
            # Create variants (model lines)
            variants_data = [
                {
                    "model_code": "GKO6010",
                    "name_tr": "Gazlı Ocak 2 Gözlü",
                    "name_en": "Gas Range 2 Burners",
                    "dimensions": "400x600x280",
                    "weight_kg": Decimal("32.0"),
                    "list_price": Decimal("4500.00"),
                    "specs": {
                        "goz-adedi": 2,
                        "guc-kw": "8.0",
                        "gaz-baglantisi": "1/2\"",
                    },
                },
                {
                    "model_code": "GKO6020",
                    "name_tr": "Gazlı Ocak 4 Gözlü",
                    "name_en": "Gas Range 4 Burners",
                    "dimensions": "800x600x280",
                    "weight_kg": Decimal("48.0"),
                    "list_price": Decimal("7200.00"),
                    "specs": {
                        "goz-adedi": 4,
                        "guc-kw": "16.0",
                        "gaz-baglantisi": "1/2\"",
                    },
                },
                {
                    "model_code": "GKO6030",
                    "name_tr": "Gazlı Ocak 6 Gözlü",
                    "name_en": "Gas Range 6 Burners",
                    "dimensions": "1200x600x280",
                    "weight_kg": Decimal("68.0"),
                    "list_price": Decimal("10500.00"),
                    "specs": {
                        "goz-adedi": 6,
                        "guc-kw": "24.0",
                        "gaz-baglantisi": "3/4\"",
                    },
                },
            ]
            
            for var_data in variants_data:
                variant, v_created = Variant.objects.get_or_create(
                    model_code=var_data["model_code"],
                    defaults={
                        "product": product,
                        "name_tr": var_data["name_tr"],
                        "name_en": var_data.get("name_en", ""),
                        "dimensions": var_data.get("dimensions", ""),
                        "weight_kg": var_data.get("weight_kg"),
                        "list_price": var_data.get("list_price"),
                        "specs": var_data.get("specs", {}),
                        "stock_qty": 10,
                    },
                )
                if v_created:
                    self.stats["variants"] += 1
                    self.stdout.write(f"    ✓ Variant: {variant.model_code}")
        else:
            self.stdout.write(f"  - Exists: {product.title_tr}")
    
    def create_gazli_wok_group(self, series, taxonomy, spec_keys):
        """Create Gazlı Wok Ocaklar product group with variants."""
        
        general_features = [
            "Paslanmaz çelik gövde",
            "Özel wok brülör tasarımı",
            "Yüksek BTU değeri",
            "Su soğutmalı wok ring",
            "Döküm wok adaptörü dahil",
            "Ayarlanabilir alev kontrolü",
            "Termoelektrik emniyet sistemi (FFD)",
        ]
        
        notes = [
            "Wok çapları 330mm ve 400mm arası uyumludur.",
        ]
        
        spec_layout = ["wok-capi", "guc-kw", "boyutlar", "agirlik", "gaz-baglantisi"]
        
        product, created = Product.objects.get_or_create(
            slug="600-serisi-gazli-wok-ocaklar",
            defaults={
                "name": "600 Serisi Gazlı Wok Ocaklar",
                "title_tr": "Gazlı Wok Ocaklar",
                "title_en": "Gas Wok Ranges",
                "series": series,
                "primary_node": taxonomy.get("gazli-wok-ocaklar"),
                "status": Product.Status.ACTIVE,
                "is_featured": False,
                "general_features": general_features,
                "notes": notes,
                "spec_layout": spec_layout,
                "pdf_ref": "p11",
                "short_specs": general_features[:5],
            },
        )
        
        if created:
            self.stats["products"] += 1
            self.stdout.write(f"  ✓ Created Product: {product.title_tr}")
            
            # Add to taxonomy
            ProductNode.objects.get_or_create(
                product=product,
                node=taxonomy["gazli-wok-ocaklar"],
            )
            
            # Create variants (model lines)
            variants_data = [
                {
                    "model_code": "GKW6010",
                    "name_tr": "Wok Ocağı Tek Gözlü",
                    "name_en": "Wok Range Single",
                    "dimensions": "400x600x450",
                    "weight_kg": Decimal("38.0"),
                    "list_price": Decimal("5800.00"),
                    "specs": {
                        "wok-capi": 330,
                        "guc-kw": "14.0",
                        "gaz-baglantisi": "1/2\"",
                    },
                },
                {
                    "model_code": "GKW6030",
                    "name_tr": "Wok Ocağı Çift Gözlü",
                    "name_en": "Wok Range Double",
                    "dimensions": "800x600x450",
                    "weight_kg": Decimal("62.0"),
                    "list_price": Decimal("9500.00"),
                    "specs": {
                        "wok-capi": 400,
                        "guc-kw": "28.0",
                        "gaz-baglantisi": "3/4\"",
                    },
                },
            ]
            
            for var_data in variants_data:
                variant, v_created = Variant.objects.get_or_create(
                    model_code=var_data["model_code"],
                    defaults={
                        "product": product,
                        "name_tr": var_data["name_tr"],
                        "name_en": var_data.get("name_en", ""),
                        "dimensions": var_data.get("dimensions", ""),
                        "weight_kg": var_data.get("weight_kg"),
                        "list_price": var_data.get("list_price"),
                        "specs": var_data.get("specs", {}),
                        "stock_qty": 5,
                    },
                )
                if v_created:
                    self.stats["variants"] += 1
                    self.stdout.write(f"    ✓ Variant: {variant.model_code}")
        else:
            self.stdout.write(f"  - Exists: {product.title_tr}")
    
    def create_elektrikli_fritoz_group(self, series, taxonomy, spec_keys):
        """Create Elektrikli Fritöz product group with variants."""
        
        general_features = [
            "Paslanmaz çelik gövde",
            "Elektronik termostat kontrolü",
            "Güvenlik termostatı",
            "Kapak dahil",
            "Yağ boşaltma vanası",
            "Baskı tipi sepet",
        ]
        
        notes = [
            "Fritöz yağı dahil değildir.",
            "Tüm modeller CE standartlarına uygundur.",
        ]
        
        spec_layout = ["guc-kw", "boyutlar", "agirlik", "elektrik-baglantisi"]
        
        product, created = Product.objects.get_or_create(
            slug="600-serisi-elektrikli-fritozler",
            defaults={
                "name": "600 Serisi Elektrikli Fritözler",
                "title_tr": "Elektrikli Fritözler",
                "title_en": "Electric Fryers",
                "series": series,
                "primary_node": taxonomy.get("elektrikli-fritoz"),
                "status": Product.Status.ACTIVE,
                "is_featured": True,
                "general_features": general_features,
                "notes": notes,
                "spec_layout": spec_layout,
                "pdf_ref": "p25",
                "short_specs": general_features[:5],
            },
        )
        
        if created:
            self.stats["products"] += 1
            self.stdout.write(f"  ✓ Created Product: {product.title_tr}")
            
            # Add to taxonomy
            if taxonomy.get("elektrikli-fritoz"):
                ProductNode.objects.get_or_create(
                    product=product,
                    node=taxonomy["elektrikli-fritoz"],
                )
            
            # Create variants
            variants_data = [
                {
                    "model_code": "EFR6010",
                    "name_tr": "Elektrikli Fritöz 8 Lt",
                    "name_en": "Electric Fryer 8 Lt",
                    "dimensions": "400x600x280",
                    "weight_kg": Decimal("18.0"),
                    "list_price": Decimal("3200.00"),
                    "specs": {
                        "guc-kw": "6.0",
                        "elektrik-baglantisi": "380V/50Hz",
                    },
                },
                {
                    "model_code": "EFR6020",
                    "name_tr": "Elektrikli Fritöz 2x8 Lt",
                    "name_en": "Electric Fryer 2x8 Lt",
                    "dimensions": "800x600x280",
                    "weight_kg": Decimal("34.0"),
                    "list_price": Decimal("5800.00"),
                    "specs": {
                        "guc-kw": "12.0",
                        "elektrik-baglantisi": "380V/50Hz",
                    },
                },
            ]
            
            for var_data in variants_data:
                variant, v_created = Variant.objects.get_or_create(
                    model_code=var_data["model_code"],
                    defaults={
                        "product": product,
                        "name_tr": var_data["name_tr"],
                        "name_en": var_data.get("name_en", ""),
                        "dimensions": var_data.get("dimensions", ""),
                        "weight_kg": var_data.get("weight_kg"),
                        "list_price": var_data.get("list_price"),
                        "specs": var_data.get("specs", {}),
                        "stock_qty": 8,
                    },
                )
                if v_created:
                    self.stats["variants"] += 1
                    self.stdout.write(f"    ✓ Variant: {variant.model_code}")
        else:
            self.stdout.write(f"  - Exists: {product.title_tr}")
    
    def create_lavali_izgara_group(self, series, taxonomy, spec_keys):
        """Create Lavalı Izgara product group with variants."""
        
        general_features = [
            "Paslanmaz çelik gövde",
            "Lav taşı ısıtma sistemi",
            "Döküm ızgara",
            "Yağ toplama tepsisi",
            "Ayarlanabilir alev kontrolü",
            "Kolay temizlenebilir tasarım",
        ]
        
        notes = [
            "Lav taşları 2 yılda bir değiştirilmelidir.",
        ]
        
        spec_layout = ["guc-kw", "boyutlar", "agirlik", "gaz-baglantisi"]
        
        product, created = Product.objects.get_or_create(
            slug="600-serisi-lavali-izgaralar",
            defaults={
                "name": "600 Serisi Lavalı Izgaralar",
                "title_tr": "Lavalı Izgaralar",
                "title_en": "Lava Stone Grills",
                "series": series,
                "primary_node": taxonomy.get("lavali-izgara"),
                "status": Product.Status.ACTIVE,
                "is_featured": False,
                "general_features": general_features,
                "notes": notes,
                "spec_layout": spec_layout,
                "pdf_ref": "p31",
                "short_specs": general_features[:5],
            },
        )
        
        if created:
            self.stats["products"] += 1
            self.stdout.write(f"  ✓ Created Product: {product.title_tr}")
            
            # Add to taxonomy
            if taxonomy.get("lavali-izgara"):
                ProductNode.objects.get_or_create(
                    product=product,
                    node=taxonomy["lavali-izgara"],
                )
            
            # Create variants
            variants_data = [
                {
                    "model_code": "GLI6010",
                    "name_tr": "Lavalı Izgara 40 cm",
                    "name_en": "Lava Stone Grill 40 cm",
                    "dimensions": "400x600x280",
                    "weight_kg": Decimal("42.0"),
                    "list_price": Decimal("4200.00"),
                    "specs": {
                        "guc-kw": "7.0",
                        "gaz-baglantisi": "1/2\"",
                    },
                },
                {
                    "model_code": "GLI6020",
                    "name_tr": "Lavalı Izgara 80 cm",
                    "name_en": "Lava Stone Grill 80 cm",
                    "dimensions": "800x600x280",
                    "weight_kg": Decimal("68.0"),
                    "list_price": Decimal("7400.00"),
                    "specs": {
                        "guc-kw": "14.0",
                        "gaz-baglantisi": "3/4\"",
                    },
                },
                {
                    "model_code": "GLI6030",
                    "name_tr": "Lavalı Izgara 120 cm",
                    "name_en": "Lava Stone Grill 120 cm",
                    "dimensions": "1200x600x280",
                    "weight_kg": Decimal("92.0"),
                    "list_price": Decimal("10200.00"),
                    "specs": {
                        "guc-kw": "21.0",
                        "gaz-baglantisi": "3/4\"",
                    },
                },
            ]
            
            for var_data in variants_data:
                variant, v_created = Variant.objects.get_or_create(
                    model_code=var_data["model_code"],
                    defaults={
                        "product": product,
                        "name_tr": var_data["name_tr"],
                        "name_en": var_data.get("name_en", ""),
                        "dimensions": var_data.get("dimensions", ""),
                        "weight_kg": var_data.get("weight_kg"),
                        "list_price": var_data.get("list_price"),
                        "specs": var_data.get("specs", {}),
                        "stock_qty": 6,
                    },
                )
                if v_created:
                    self.stats["variants"] += 1
                    self.stdout.write(f"    ✓ Variant: {variant.model_code}")
        else:
            self.stdout.write(f"  - Exists: {product.title_tr}")
    
    def create_makarna_pisirici_group(self, series, taxonomy, spec_keys):
        """Create Makarna Pişirici product group with variants."""
        
        general_features = [
            "Paslanmaz çelik gövde",
            "GN sepet sistemli",
            "Su boşaltma vanası",
            "Termostat kontrollü",
            "Hızlı ısınma özelliği",
        ]
        
        notes = [
            "Sepetler opsiyonel olarak sipariş edilebilir.",
        ]
        
        spec_layout = ["guc-kw", "boyutlar", "agirlik", "elektrik-baglantisi"]
        
        product, created = Product.objects.get_or_create(
            slug="600-serisi-makarna-pisiriciler",
            defaults={
                "name": "600 Serisi Makarna Pişiriciler",
                "title_tr": "Makarna Pişiriciler",
                "title_en": "Pasta Cookers",
                "series": series,
                "primary_node": taxonomy.get("makarna-pisirici"),
                "status": Product.Status.ACTIVE,
                "is_featured": False,
                "general_features": general_features,
                "notes": notes,
                "spec_layout": spec_layout,
                "pdf_ref": "p45",
                "short_specs": general_features[:4],
            },
        )
        
        if created:
            self.stats["products"] += 1
            self.stdout.write(f"  ✓ Created Product: {product.title_tr}")
            
            # Add to taxonomy
            if taxonomy.get("makarna-pisirici"):
                ProductNode.objects.get_or_create(
                    product=product,
                    node=taxonomy["makarna-pisirici"],
                )
            
            # Create variants
            variants_data = [
                {
                    "model_code": "EMP6010",
                    "name_tr": "Elektrikli Makarna Pişirici 40 Lt",
                    "name_en": "Electric Pasta Cooker 40 Lt",
                    "dimensions": "400x600x850",
                    "weight_kg": Decimal("38.0"),
                    "list_price": Decimal("5600.00"),
                    "specs": {
                        "guc-kw": "9.0",
                        "elektrik-baglantisi": "380V/50Hz",
                    },
                },
                {
                    "model_code": "GMP6010",
                    "name_tr": "Gazlı Makarna Pişirici 40 Lt",
                    "name_en": "Gas Pasta Cooker 40 Lt",
                    "dimensions": "400x600x850",
                    "weight_kg": Decimal("42.0"),
                    "list_price": Decimal("4800.00"),
                    "specs": {
                        "guc-kw": "10.0",
                        "gaz-baglantisi": "1/2\"",
                    },
                },
            ]
            
            for var_data in variants_data:
                variant, v_created = Variant.objects.get_or_create(
                    model_code=var_data["model_code"],
                    defaults={
                        "product": product,
                        "name_tr": var_data["name_tr"],
                        "name_en": var_data.get("name_en", ""),
                        "dimensions": var_data.get("dimensions", ""),
                        "weight_kg": var_data.get("weight_kg"),
                        "list_price": var_data.get("list_price"),
                        "specs": var_data.get("specs", {}),
                        "stock_qty": 4,
                    },
                )
                if v_created:
                    self.stats["variants"] += 1
                    self.stdout.write(f"    ✓ Variant: {variant.model_code}")
        else:
            self.stdout.write(f"  - Exists: {product.title_tr}")
    
    def generate_leaf_products(self, series):
        """Generate Product groups for all leaf taxonomy nodes."""
        from apps.catalog.services import generate_products_from_leaf_nodes
        
        self.stdout.write(f"\nGenerating products for leaf nodes in {series.name}...")
        
        # Get all nodes for this series
        nodes = TaxonomyNode.objects.filter(series=series)
        
        result = generate_products_from_leaf_nodes(nodes)
        
        self.stats["products"] += result["created"]
        
        self.stdout.write(
            f"  ✓ Created: {result['created']}, "
            f"Skipped existing: {result['skipped_existing']}, "
            f"Skipped non-leaf: {result['skipped_non_leaf']}"
        )
    
    def print_summary(self):
        """Print seeding summary."""
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 50))
        self.stdout.write(self.style.SUCCESS("✅ Catalog seeding complete!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"\n  Spec Keys created:   {self.stats['spec_keys']}")
        self.stdout.write(f"  Categories created:  {self.stats['categories']}")
        self.stdout.write(f"  Series created:      {self.stats['series']}")
        self.stdout.write(f"  Taxonomy nodes:      {self.stats['nodes']}")
        self.stdout.write(f"  Products (groups):   {self.stats['products']}")
        self.stdout.write(f"  Variants (models):   {self.stats['variants']}")
        self.stdout.write(f"  Media files:         {self.stats['media']}")
        self.stdout.write("")
