"""
Import product data from ciktilar/*.txt files into the database.
Handles 3 formats: TSV, space-separated, and Markdown tables.
Updates existing products with richer data, creates new ones if needed.
"""
import os
import re
import sys
import json
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.db import transaction
from django.db.models import Count
from apps.catalog.models import Category, Series, Product, Variant
from apps.common.slugify_tr import slugify_tr

CIKTILAR_DIR = r'C:\gastrotech.com.tr.0101\gastrotech.com_cursor\ciktilar'

# Expected header columns (canonical names)
EXPECTED_HEADERS = [
    'sira_no', 'kategori', 'seri', 'urun_adi_tr', 'urun_adi_en',
    'model_kodu', 'sku', 'boyutlar', 'agirlik', 'guc', 'voltaj',
    'kapasite', 'yakit_tipi', 'malzeme',
    'ek_spec_1_anahtar', 'ek_spec_1_deger',
    'ek_spec_2_anahtar', 'ek_spec_2_deger',
    'ek_spec_3_anahtar', 'ek_spec_3_deger',
    'genel_ozellikler_tr', 'genel_ozellikler_en',
]
# Some files have extra columns (uzun_aciklama_tr/en, liste_fiyati, durum, foto refs, notlar)
# We handle them dynamically.

HEADER_ALIASES = {
    'sira no': 'sira_no', 'sıra no': 'sira_no',
    'kategori': 'kategori',
    'seri': 'seri',
    'urun adi tr': 'urun_adi_tr', 'ürün adı tr': 'urun_adi_tr',
    'urun adi en': 'urun_adi_en', 'ürün adı en': 'urun_adi_en',
    'model kodu': 'model_kodu',
    'sku': 'sku',
    'boyutlar (gxdxy mm)': 'boyutlar', 'boyutlar': 'boyutlar',
    'agirlik (kg)': 'agirlik', 'ağırlık (kg)': 'agirlik',
    'guc (w/kw)': 'guc', 'güç (w/kw)': 'guc',
    'voltaj': 'voltaj',
    'kapasite': 'kapasite',
    'yakit tipi': 'yakit_tipi', 'yakıt tipi': 'yakit_tipi',
    'malzeme': 'malzeme',
    'ek spec 1 anahtar': 'ek_spec_1_anahtar',
    'ek spec 1 deger': 'ek_spec_1_deger', 'ek spec 1 değer': 'ek_spec_1_deger',
    'ek spec 2 anahtar': 'ek_spec_2_anahtar',
    'ek spec 2 deger': 'ek_spec_2_deger', 'ek spec 2 değer': 'ek_spec_2_deger',
    'ek spec 3 anahtar': 'ek_spec_3_anahtar',
    'ek spec 3 deger': 'ek_spec_3_deger', 'ek spec 3 değer': 'ek_spec_3_deger',
    'genel ozellikler tr': 'genel_ozellikler_tr', 'genel özellikler tr': 'genel_ozellikler_tr',
    'genel ozellikler en': 'genel_ozellikler_en', 'genel özellikler en': 'genel_ozellikler_en',
    'uzun aciklama tr': 'uzun_aciklama_tr', 'uzun açıklama tr': 'uzun_aciklama_tr',
    'uzun aciklama en': 'uzun_aciklama_en', 'uzun açıklama en': 'uzun_aciklama_en',
    'liste fiyati': 'liste_fiyati', 'liste fiyatı': 'liste_fiyati',
    'durum': 'durum',
    'foto 1 (sayfa-sira)': 'foto_1', 'foto 1 (sayfa-sıra)': 'foto_1',
    'foto 2 (sayfa-sira)': 'foto_2', 'foto 2 (sayfa-sıra)': 'foto_2',
    'foto 3 (sayfa-sira)': 'foto_3', 'foto 3 (sayfa-sıra)': 'foto_3',
    'foto 4 (sayfa-sira)': 'foto_4', 'foto 4 (sayfa-sıra)': 'foto_4',
    'foto 5 (sayfa-sira)': 'foto_5', 'foto 5 (sayfa-sıra)': 'foto_5',
    'notlar': 'notlar',
}


def detect_format(lines):
    """Detect file format: 'tsv', 'markdown', or 'space'."""
    for line in lines[:5]:
        line = line.strip()
        if not line:
            continue
        if line.startswith('|'):
            return 'markdown'
        if '\t' in line:
            return 'tsv'
    return 'space'


def parse_markdown_row(line):
    """Parse a markdown table row."""
    parts = line.strip().strip('|').split('|')
    return [p.strip() for p in parts]


def normalize_header(h):
    """Normalize a header string to canonical name."""
    h = h.strip().lower()
    return HEADER_ALIASES.get(h, h)


def parse_file(filepath):
    """Parse a ciktilar file and return list of dicts."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fmt = detect_format(lines)
    rows = []

    if fmt == 'markdown':
        # Find header row (first | row), skip separator
        header_line = None
        data_start = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('|') and '---' not in line:
                if header_line is None:
                    header_line = line
                    data_start = i + 1
                    continue
            if header_line and '---' in line.strip():
                data_start = i + 1
                continue
            if header_line and data_start <= i and line.strip().startswith('|'):
                rows.append(line)

        if not header_line:
            return []

        headers = [normalize_header(h) for h in parse_markdown_row(header_line)]
        parsed = []
        for row_line in rows:
            values = parse_markdown_row(row_line)
            d = {}
            for j, h in enumerate(headers):
                if j < len(values):
                    d[h] = values[j]
            parsed.append(d)
        return parsed

    elif fmt == 'tsv':
        if not lines:
            return []
        headers = [normalize_header(h) for h in lines[0].strip().split('\t')]
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            values = line.split('\t')
            d = {}
            for j, h in enumerate(headers):
                if j < len(values):
                    d[h] = values[j]
            parsed.append(d) if 'd' not in dir() else None
        # re-do properly
        parsed = []
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            values = line.split('\t')
            d = {}
            for j, h in enumerate(headers):
                if j < len(values):
                    d[h] = values[j]
            parsed.append(d)
        return parsed

    else:  # space-separated (tricky - need to match header positions)
        # These files have space-separated columns matching the header template
        # Best approach: try to extract by known field patterns
        if not lines:
            return []

        # First line is header
        header_line = lines[0].strip()
        # Check if it looks like our known header
        if 'Model Kodu' not in header_line and 'Model kodu' not in header_line.lower():
            return []

        parsed = []
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            # Extract model code with regex - it's the key field
            # Pattern: number at start, then category, series, product name, english name, MODEL CODE, then rest
            # This is very hard to parse reliably with spaces. Let's use a regex approach.
            d = extract_space_separated_row(line)
            if d and d.get('model_kodu'):
                parsed.append(d)
        return parsed


def extract_space_separated_row(line):
    """Extract data from space-separated line using pattern matching."""
    # These lines follow: SIRA KATEGORI SERI URUN_TR URUN_EN MODEL_KODU ...
    # Model codes have patterns like: GKO6010, PRIME061GP, EKF6020, VBY500CD, etc.
    # Strategy: find the model code, then split around it

    # Find model code pattern (letters+digits, possibly with hyphens)
    model_patterns = [
        r'\b([A-Z]{2,}[\d-]+[A-Z]*[\d]*(?:-[A-Z\d]+)*)\b',  # GKO6010, PRIME061GP, VBY-FT3600L
        r'\b(\d{4,})\b',  # Pure numeric codes like 260813
        r'\b([A-Z]+\s\d+[A-Z]*(?:-[A-Z\d]+)*)\b',  # MAESTRO 061G-TOUCH
    ]

    # Find all potential model codes
    model_code = None
    model_pos = -1

    # Known model code prefixes
    prefixes = ['GKO', 'GKW', 'EKO', 'EKF', 'IKO', 'GPI', 'GPT', 'GP1', 'EPI', 'GKF',
                'ESI', 'GSI', 'ESB', 'GSB', 'EFP', 'GFP', 'GLI', 'GBM', 'EBM',
                'EMP', 'EPD', 'EDBT', 'EDT', 'VDRP', 'VBY', 'VGY', 'PRIME',
                'NEVO', 'MAESTRO', 'KWIK', 'MIX', 'GR-', 'CC6', 'CC7', 'CC9',
                'NTR', 'RTR', 'RTW', 'WFCE', 'CNS', 'CPS', 'TTR', 'VHE',
                'VPRU', 'KTA', 'CBU', 'ICB', 'ICC', 'ICP', 'ALL', 'NO:']

    for prefix in prefixes:
        idx = line.find(prefix)
        if idx > 0:
            # Extract until next space
            rest = line[idx:]
            match = re.match(r'(\S+)', rest)
            if match:
                model_code = match.group(1)
                model_pos = idx
                break

    if not model_code:
        # Try generic pattern
        m = re.search(r'\b([A-Z]{2,}\d{3,}[A-Z]*(?:-\S+)?)\b', line)
        if m:
            model_code = m.group(1)
            model_pos = m.start()

    if not model_code or model_pos < 0:
        return None

    # Everything before model code: sira + kategori + seri + urun_tr + urun_en
    before = line[:model_pos].strip()
    after = line[model_pos + len(model_code):].strip()

    # Extract sira_no (first number)
    m_sira = re.match(r'^(\d+)\s+', before)
    sira = m_sira.group(1) if m_sira else ''
    if m_sira:
        before = before[m_sira.end():]

    # Try to find category from known list
    known_cats = [
        'Pisirme Ekipmanlari', 'Pişirme Ekipmanları',
        'Firinlar', 'Fırınlar',
        'Sogutma Uniteleri', 'Soğutma Üniteleri',
        'Buz Makineleri',
        'Hazirlik Ekipmanlari', 'Hazırlık Ekipmanları',
        'Kafeterya Ekipmanlari', 'Kafeterya Ekipmanları',
        'Tamamlayici Ekipmanlar', 'Tamamlayıcı Ekipmanlar',
        'Bulashane', 'Bulaşıkhane',
        'Camasirhane', 'Çamaşırhane',
        'Aksesuarlar',
    ]

    kategori = ''
    for cat in known_cats:
        if cat in before:
            kategori = cat
            before = before.replace(cat, '', 1).strip()
            break

    # Try to find series
    known_series = [
        '600 Serisi', '700 Serisi', '900 Serisi', 'Drop-in Serisi',
        'Eco Serisi', 'Eko Serisi',
        'Prime Konveksiyonel Serisi', 'PRIME', 'NEVO', 'MAESTRO Serisi',
        'MIX', 'GR', 'KWIK-CO Serisi',
        'Basic Serisi', 'Premium Serisi', 'B Serisi',
        'Kitchen Aid', 'ALL GROUND', 'CBU Serisi',
        'Scotsman', 'Thermospeed',
        'I Combi Classic Serisi', 'Rational', 'iVario Serisi',
    ]

    seri = ''
    for s in known_series:
        if s in before:
            seri = s
            before = before.replace(s, '', 1).strip()
            break

    # Remaining before = product names (TR + EN mixed)
    urun_tr = before.strip()
    urun_en = ''

    # Split TR/EN - usually EN is capitalized differently or after the Turkish name
    # Heuristic: find where English starts (common English words)
    en_markers = [' Gas ', ' Electric ', ' Burner', ' Range', ' Fryer', ' Cooker',
                  ' Oven', ' Grill', ' Bain', ' Pasta', ' Boiling', ' Tilting',
                  ' Convection', ' Induction', ' Solid', ' Fry Top', ' Hot Plate',
                  ' Smooth', ' Ribbed', ' Drop-in']
    for marker in en_markers:
        idx = urun_tr.find(marker)
        if idx > 5:  # Must have some TR text before
            urun_en = urun_tr[idx:].strip()
            urun_tr = urun_tr[:idx].strip()
            break

    # Parse after model code for remaining fields
    # Fields: SKU, Boyutlar, Agirlik, Guc, Voltaj, Kapasite, Yakit, Malzeme, specs...
    d = {
        'sira_no': sira,
        'kategori': kategori,
        'seri': seri,
        'urun_adi_tr': urun_tr,
        'urun_adi_en': urun_en,
        'model_kodu': model_code,
    }

    # Try to extract dimensions pattern from after
    dim_match = re.search(r'(\d+x\d+x\d+(?:-\d+)?)', after)
    if dim_match:
        d['boyutlar'] = dim_match.group(1)

    # Extract weight (number after dimensions)
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s', after)
    if weight_match:
        d['agirlik'] = weight_match.group(1)

    # Extract voltage
    volt_match = re.search(r'((?:220|380|350|500)[-\d]*V[^|]*)', after)
    if volt_match:
        d['voltaj'] = volt_match.group(1).strip()

    # Extract general features
    feat_match = re.search(r'((?:Paslanmaz|Stainless|IPX|Kuvvetli).+?)(?:\s+(?:active|draft)|\s*$)', after)
    if feat_match:
        features = feat_match.group(1)
        if '|' in features:
            # Split TR and EN parts
            parts = features.split('Stainless')
            if len(parts) > 1:
                d['genel_ozellikler_tr'] = parts[0].strip().rstrip('|').strip()
                d['genel_ozellikler_en'] = 'Stainless' + '|'.join(parts[1:]).strip()

    # Extract fuel type
    for fuel in ['Dogalgaz', 'Doğalgaz', 'Elektrik', 'LPG']:
        if fuel in after:
            d['yakit_tipi'] = fuel
            break

    d['durum'] = 'active'

    return d


def get_or_create_category(name):
    """Get or create category."""
    # Normalize common variants
    name_map = {
        'Pisirme Ekipmanlari': 'Pişirme Ekipmanları',
        'Pişirme Ekipmanları': 'Pişirme Ekipmanları',
        'Firinlar': 'Fırınlar',
        'Fırınlar': 'Fırınlar',
        'Sogutma Uniteleri': 'Soğutma Üniteleri',
        'Soğutma Üniteleri': 'Soğutma Üniteleri',
        'Buz Makineleri': 'Buz Makineleri',
        'Hazirlik Ekipmanlari': 'Hazırlık Ekipmanları',
        'Hazırlık Ekipmanları': 'Hazırlık Ekipmanları',
        'Kafeterya Ekipmanlari': 'Kafeterya Ekipmanları',
        'Kafeterya Ekipmanları': 'Kafeterya Ekipmanları',
        'Tamamlayici Ekipmanlar': 'Tamamlayıcı Ekipmanlar',
        'Tamamlayıcı Ekipmanlar': 'Tamamlayıcı Ekipmanlar',
        'Bulashane': 'Bulaşıkhane',
        'Bulaşıkhane': 'Bulaşıkhane',
        'Bulasikane': 'Bulaşıkhane',
        'Camasirhane': 'Çamaşırhane',
        'Çamaşırhane': 'Çamaşırhane',
        'Aksesuarlar': 'Aksesuarlar',
    }
    name = name_map.get(name, name)
    try:
        return Category.objects.get(name=name)
    except Category.DoesNotExist:
        slug = slugify_tr(name)
        return Category.objects.create(name=name, slug=slug)


def get_or_create_series(category, series_name):
    """Get or create series, handle duplicates."""
    if not series_name or series_name == '-':
        series_name = 'Diger'

    existing = Series.objects.filter(category=category, name=series_name)
    if existing.count() == 1:
        return existing.first()
    elif existing.count() > 1:
        return existing.annotate(num_products=Count('products')).order_by('-num_products', 'created_at').first()
    else:
        slug = slugify_tr(series_name)
        base_slug = slug
        counter = 1
        while Series.objects.filter(category=category, slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return Series.objects.create(category=category, name=series_name, slug=slug)


def clean_value(val):
    """Clean a cell value."""
    if val is None:
        return ''
    val = str(val).strip()
    if val in ('-', 'N/A', 'n/a', '-\t', ''):
        return ''
    return val


def parse_weight(val):
    """Parse weight string to Decimal."""
    from decimal import Decimal, InvalidOperation
    val = clean_value(val)
    if not val:
        return None
    # Remove commas, handle dots
    val = val.replace(',', '.').replace(' ', '')
    # Remove "kg" suffix
    val = re.sub(r'[a-zA-Z]+', '', val).strip()
    try:
        w = Decimal(val)
        if w < 0:
            w = abs(w)
        return w if w > 0 else None
    except (InvalidOperation, ValueError):
        return None


def parse_price(val):
    """Parse price string to Decimal."""
    from decimal import Decimal, InvalidOperation
    val = clean_value(val)
    if not val:
        return None
    val = val.replace('.', '').replace(',', '.').replace(' ', '')
    val = re.sub(r'[^0-9.]', '', val)
    try:
        return Decimal(val) if val else None
    except (InvalidOperation, ValueError):
        return None


def build_specs(row):
    """Build variant specs dict from row data."""
    specs = {}
    for key in ['guc', 'voltaj', 'kapasite', 'yakit_tipi', 'malzeme']:
        val = clean_value(row.get(key, ''))
        if val:
            specs[key] = val

    # Add ek specs
    for i in range(1, 4):
        k = clean_value(row.get(f'ek_spec_{i}_anahtar', ''))
        v = clean_value(row.get(f'ek_spec_{i}_deger', ''))
        if k and v:
            specs[k] = v

    return specs


def build_general_features(row):
    """Build general_features list from pipe-separated string."""
    val = clean_value(row.get('genel_ozellikler_tr', ''))
    if not val:
        return []
    # Filter out "Ayni genel ozellikler" references
    if 'ayni' in val.lower() or 'aynı' in val.lower():
        return []
    return [f.strip() for f in val.split('|') if f.strip()]


def main():
    print("=" * 70)
    print("CIKTILAR IMPORT ISLEMI")
    print("=" * 70)

    # Parse all files
    all_rows = []
    files = sorted(os.listdir(CIKTILAR_DIR))

    for fname in files:
        if not fname.endswith('.txt'):
            continue
        fpath = os.path.join(CIKTILAR_DIR, fname)
        rows = parse_file(fpath)
        print(f"  {fname}: {len(rows)} satir")
        for r in rows:
            r['_source_file'] = fname
        all_rows.extend(rows)

    print(f"\nToplam parse edilen satir: {len(all_rows)}")

    # Filter rows with model codes
    valid_rows = [r for r in all_rows if clean_value(r.get('model_kodu', ''))]
    print(f"Model kodu olan satir: {len(valid_rows)}")

    # Deduplicate by model_code (keep the one with more data)
    by_code = {}
    for row in valid_rows:
        code = clean_value(row['model_kodu'])
        if code not in by_code:
            by_code[code] = row
        else:
            # Keep the row with more non-empty fields
            existing_count = sum(1 for v in by_code[code].values() if clean_value(str(v)))
            new_count = sum(1 for v in row.values() if clean_value(str(v)))
            if new_count > existing_count:
                by_code[code] = row

    print(f"Benzersiz model kodu: {len(by_code)}")

    # Import
    updated_variants = 0
    created_variants = 0
    updated_products = 0
    created_products = 0
    errors = []

    with transaction.atomic():
        for code, row in by_code.items():
            try:
                kategori_name = clean_value(row.get('kategori', ''))
                seri_name = clean_value(row.get('seri', ''))
                urun_tr = clean_value(row.get('urun_adi_tr', ''))
                urun_en = clean_value(row.get('urun_adi_en', ''))
                model_code = clean_value(row.get('model_kodu', ''))

                if not model_code:
                    continue
                if not urun_tr:
                    urun_tr = model_code

                # Check if variant exists
                variant = Variant.objects.filter(model_code=model_code).first()

                if variant:
                    # UPDATE existing variant and product
                    product = variant.product

                    # Update variant fields
                    changed = False
                    dims = clean_value(row.get('boyutlar', ''))
                    if dims and not variant.dimensions:
                        variant.dimensions = dims
                        changed = True

                    weight = parse_weight(row.get('agirlik', ''))
                    if weight and not variant.weight_kg:
                        variant.weight_kg = weight
                        changed = True

                    specs = build_specs(row)
                    if specs:
                        existing_specs = variant.specs or {}
                        for k, v in specs.items():
                            if k not in existing_specs:
                                existing_specs[k] = v
                        if existing_specs != (variant.specs or {}):
                            variant.specs = existing_specs
                            changed = True

                    name_en = clean_value(row.get('urun_adi_en', ''))
                    if name_en and not variant.name_en:
                        variant.name_en = name_en
                        changed = True

                    price = parse_price(row.get('liste_fiyati', ''))
                    if price and not variant.list_price:
                        variant.list_price = price
                        changed = True

                    sku = clean_value(row.get('sku', ''))
                    if sku and not variant.sku:
                        variant.sku = sku
                        changed = True

                    if changed:
                        variant.save()
                        updated_variants += 1

                    # Update product fields
                    p_changed = False
                    if urun_en and not product.title_en:
                        product.title_en = urun_en
                        p_changed = True

                    features = build_general_features(row)
                    if features and not product.general_features:
                        product.general_features = features
                        p_changed = True

                    long_desc = clean_value(row.get('uzun_aciklama_tr', ''))
                    if long_desc and not product.long_description:
                        product.long_description = long_desc
                        p_changed = True

                    if p_changed:
                        product.save()
                        updated_products += 1

                else:
                    # CREATE new variant (and possibly product)
                    if not kategori_name:
                        errors.append(f"{model_code}: Kategori belirtilmemis")
                        continue

                    category = get_or_create_category(kategori_name)
                    series = get_or_create_series(category, seri_name)

                    # Check if product already exists (by name + series)
                    product = Product.objects.filter(
                        title_tr=urun_tr, series=series
                    ).first()

                    if not product:
                        slug = slugify_tr(urun_tr)
                        base_slug = slug
                        counter = 1
                        while Product.objects.filter(slug=slug).exists():
                            slug = f"{base_slug}-{counter}"
                            counter += 1

                        features = build_general_features(row)
                        long_desc = clean_value(row.get('uzun_aciklama_tr', ''))

                        product = Product.objects.create(
                            series=series,
                            category=category,
                            name=urun_tr,
                            slug=slug,
                            title_tr=urun_tr,
                            title_en=urun_en,
                            status='active',
                            general_features=features if features else [],
                            long_description=long_desc,
                        )
                        created_products += 1

                    # Create variant
                    specs = build_specs(row)
                    Variant.objects.create(
                        product=product,
                        model_code=model_code,
                        name_tr=urun_tr,
                        name_en=urun_en,
                        dimensions=clean_value(row.get('boyutlar', '')),
                        weight_kg=parse_weight(row.get('agirlik', '')),
                        list_price=parse_price(row.get('liste_fiyati', '')),
                        sku=clean_value(row.get('sku', '')),
                        specs=specs if specs else {},
                    )
                    created_variants += 1

            except Exception as e:
                errors.append(f"{code}: {str(e)[:100]}")

    print(f"\n{'=' * 70}")
    print("SONUC")
    print(f"{'=' * 70}")
    print(f"Guncellenen varyant: {updated_variants}")
    print(f"Guncellenen urun: {updated_products}")
    print(f"Olusturulan varyant: {created_variants}")
    print(f"Olusturulan urun: {created_products}")
    print(f"Hata: {len(errors)}")

    if errors:
        print("\nHatalar:")
        for e in errors[:30]:
            print(f"  - {e}")
        if len(errors) > 30:
            print(f"  ... +{len(errors)-30} daha")

    # Final stats
    print(f"\nVeritabani durumu:")
    print(f"  Toplam urun: {Product.objects.count()}")
    print(f"  Toplam varyant: {Variant.objects.count()}")
    print(f"  Specs dolu varyant: {Variant.objects.exclude(specs={}).count()}")
    print(f"  Boyut dolu varyant: {Variant.objects.exclude(dimensions='').count()}")
    print(f"  Agirlik dolu varyant: {Variant.objects.filter(weight_kg__isnull=False).count()}")
    print(f"  Genel ozellikler dolu urun: {Product.objects.exclude(general_features=[]).count()}")


if __name__ == '__main__':
    main()
