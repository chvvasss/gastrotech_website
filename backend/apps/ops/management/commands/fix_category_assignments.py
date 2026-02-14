"""
Fix misassigned series and products.

All series were incorrectly imported into KWIK-CO category.
This command moves them to their correct categories based on product names.
"""

import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import Category, Series, Product

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fix series category assignments based on product names"

    # Category slugs
    TARGET_CATEGORIES = {
        'sogutma-uniteleri': [
            'buzdolabi', 'buzdolap', 'dondurucu', 'sogutma', 'soguk', 'sogutucu',
            'buz', 'ice', 'cooler', 'freezer', 'refriger', 'chiller', 'sise-sogutucu',
            'dkp-kasa', 'hava-perdeli', 'teshir', 'moduler', 'soguk-hava', 'depo'
        ],
        'hazirlik-ekipmanlari': [
            'dilimleme', 'mikser', 'blender', 'dograma', 'parcalama', 'kesme',
            'ufalayici', 'rende', 'dogruyucu', 'slicer', 'cutter', 'mixer',
            'food-processor', 'sebze', 'robot', 'bermixer', 'hamur', 'yogurma',
            'kruvasan', 'pastane', 'terazi', 'vakum', 'dehidrat', 'kurutucu',
            'dondurarak', 'duslama', 'makarna', 'imperia', 'meyve-pres', 'sikacagi',
            'narenciye', 'kitchen-aid', 'kitchenaid', 'stand-mikser'
        ],
        'camasirhane': [
            'camasir', 'kurutma-makine', 'utuleme', 'washer', 'dryer', 'tekstil',
            'merdane', 'laundry', 'leke-cikarma'
        ],
        'bulas\u0131khane': [  # bulasıkhane with Turkish dotless i
            'bulasik', 'bardak-yikama', 'dishwash', 'kazan-yikama', 'flight-tip',
            'giyotin', 'konveyorlu', 'yikama-makine'
        ],
        'kafeterya-ekipmanlari': [
            'kahve', 'espresso', 'coffee', 'brewing', 'probrew', 'grind', 'arcadia',
            'eagle', 'sense', 'aria', 'aurora', 'nero', 'degirmen', 'filtre-kahve',
            'barista', 'cappuccino', 'latte', 'sut-koputucu', 'tamper', 'b-serisi',
            'b2013', 'b2016', 'gt-serisi', 'gtech', 'm23', 'matrix', 'moda',
            'xone', 'tall-cup'
        ],
        'firinlar': [
            'i-combi', 'i-vario', 'maestro', 'combi', 'vario', 'firin', 'rational',
            'konveksiyonel'
        ],
        'aksesuarlar': [
            'aksesuar', 'accessory'
        ]
    }

    # Product name keywords (Turkish)
    PRODUCT_KEYWORDS = {
        'sogutma-uniteleri': [
            'buzdolabı', 'buzdolap', 'dondurucu', 'soğutma', 'soğuk', 'soğutucu',
            'buz', 'şişe soğutucu', 'soğuk hava deposu', 'teşhir ünitesi'
        ],
        'hazirlik-ekipmanlari': [
            'dilimleme', 'mikser', 'blender', 'doğrama', 'parçalama', 'kesme',
            'ufalayıcı', 'rende', 'doğruyucu', 'sebze', 'robot', 'hamur',
            'yoğurma', 'vakum', 'kurutucu', 'makarna', 'meyve presi', 'sıkacağı',
            'narenciye'
        ],
        'camasirhane': [
            'çamaşır', 'kurutma makinesi', 'ütü', 'leke çıkarma', 'tekstil'
        ],
        'bulas\u0131khane': [  # bulasıkhane with Turkish dotless i
            'bulaşık', 'bardak yıkama', 'kazan yıkama'
        ],
        'kafeterya-ekipmanlari': [
            'kahve', 'espresso', 'değirmen', 'filtre kahve', 'barista', 'tamper'
        ],
        'firinlar': [
            'fırın', 'pişirici', 'combi', 'kombi', 'konveksiyonel'
        ]
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']

        self.stdout.write(self.style.WARNING(
            f"{'[DRY RUN] ' if dry_run else ''}Starting category fix..."
        ))

        # Get the source category (KWIK-CO)
        try:
            kwik_co = Category.objects.get(slug='kwik-co-konveksiyonel')
        except Category.DoesNotExist:
            self.stdout.write(self.style.ERROR("KWIK-CO category not found!"))
            return

        # Get all target categories
        target_cats = {}
        for slug in self.TARGET_CATEGORIES.keys():
            try:
                target_cats[slug] = Category.objects.get(slug=slug)
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Category '{slug}' not found, skipping"))

        # Stats
        stats = {cat: 0 for cat in target_cats.keys()}
        stats['unchanged'] = 0
        stats['errors'] = 0

        # Get all series in KWIK-CO
        series_to_process = list(Series.objects.filter(category=kwik_co))
        self.stdout.write(f"Found {len(series_to_process)} series in KWIK-CO")

        moves = []

        for series in series_to_process:
            # Determine target category
            target_slug = self._determine_category(series, verbose)

            if target_slug and target_slug in target_cats:
                target_cat = target_cats[target_slug]
                moves.append({
                    'series': series,
                    'from': kwik_co,
                    'to': target_cat,
                    'target_slug': target_slug
                })
                stats[target_slug] += 1
            else:
                stats['unchanged'] += 1
                if verbose:
                    self.stdout.write(f"  UNCHANGED: {series.name} ({series.slug})")

        # Print summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("SUMMARY:")
        for cat_slug, count in stats.items():
            if count > 0:
                self.stdout.write(f"  {cat_slug}: {count} series")
        self.stdout.write("=" * 60 + "\n")

        # Show moves
        if verbose or dry_run:
            self.stdout.write("\nPlanned moves:")
            for move in moves[:30]:
                self.stdout.write(
                    f"  {move['series'].name} -> {move['to'].name}"
                )
            if len(moves) > 30:
                self.stdout.write(f"  ... and {len(moves) - 30} more")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] No changes made."))
            return

        # Apply changes
        self.stdout.write("\nApplying changes...")

        with transaction.atomic():
            for move in moves:
                series = move['series']
                target_cat = move['to']

                # Check for slug collision in target category
                existing = Series.objects.filter(
                    category=target_cat,
                    slug=series.slug
                ).exclude(id=series.id).first()

                if existing:
                    # Append suffix to avoid collision
                    new_slug = f"{series.slug}-imported"
                    counter = 1
                    while Series.objects.filter(category=target_cat, slug=new_slug).exists():
                        new_slug = f"{series.slug}-imported-{counter}"
                        counter += 1
                    series.slug = new_slug
                    self.stdout.write(self.style.WARNING(
                        f"  Renamed slug: {move['series'].name} -> {new_slug}"
                    ))

                series.category = target_cat
                series.save()

        self.stdout.write(self.style.SUCCESS(
            f"\nSuccessfully moved {len(moves)} series to their correct categories!"
        ))

    # Priority order for category checking (more specific first)
    CATEGORY_CHECK_ORDER = [
        'bulas\u0131khane',  # Check bulaşıkhane first (before sogutma catches tezgah-alti)
        'camasirhane',
        'kafeterya-ekipmanlari',
        'firinlar',
        'aksesuarlar',
        'hazirlik-ekipmanlari',
        'sogutma-uniteleri',  # Most generic, check last
    ]

    def _determine_category(self, series, verbose=False):
        """Determine the correct category for a series based on keywords."""
        slug_lower = series.slug.lower()
        name_lower = series.name.lower()

        # Get product names for this series
        product_names = list(
            series.products.values_list('name', flat=True)[:5]
        )
        products_text = ' '.join(product_names).lower()

        # Check categories in priority order
        for cat_slug in self.CATEGORY_CHECK_ORDER:
            if cat_slug not in self.TARGET_CATEGORIES:
                continue
            keywords = self.TARGET_CATEGORIES[cat_slug]
            for kw in keywords:
                if kw in slug_lower or kw in name_lower:
                    if verbose:
                        self.stdout.write(f"  {series.name} -> {cat_slug} (slug/name match: '{kw}')")
                    return cat_slug

        # Check product name keywords in priority order
        for cat_slug in self.CATEGORY_CHECK_ORDER:
            if cat_slug not in self.PRODUCT_KEYWORDS:
                continue
            keywords = self.PRODUCT_KEYWORDS[cat_slug]
            for kw in keywords:
                if kw in products_text:
                    if verbose:
                        self.stdout.write(f"  {series.name} -> {cat_slug} (product match: '{kw}')")
                    return cat_slug

        return None
