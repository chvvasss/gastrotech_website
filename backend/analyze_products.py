"""
Comprehensive product analysis script.
Checks for duplicates, inconsistencies, and data quality issues.
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from collections import defaultdict
from django.db.models import Count, Q
from apps.catalog.models import Category, Series, Product, Variant, ProductMedia
import difflib

print("=" * 70)
print("KAPSAMLI URUN ANALIZI")
print("=" * 70)

# ============================================================
# 1. DUPLICATE MODEL KODLARI
# ============================================================
print("\n" + "=" * 70)
print("1. DUPLICATE MODEL KODLARI")
print("=" * 70)

model_code_counts = Variant.objects.values('model_code').annotate(
    count=Count('id')
).filter(count__gt=1).order_by('-count')

if model_code_counts:
    print(f"\n{model_code_counts.count()} adet tekrarlayan model kodu bulundu:\n")
    for item in model_code_counts[:30]:
        variants = Variant.objects.filter(model_code=item['model_code']).select_related('product')
        print(f"  '{item['model_code']}' - {item['count']} kez:")
        for v in variants:
            print(f"    -> Urun: {v.product.title_tr[:50]} (ID: {v.product.id})")
else:
    print("\nDuplicate model kodu YOK - OK")

# ============================================================
# 2. DUPLICATE URUN SLUGLARI
# ============================================================
print("\n" + "=" * 70)
print("2. DUPLICATE URUN SLUGLARI")
print("=" * 70)

slug_counts = Product.objects.values('slug').annotate(
    count=Count('id')
).filter(count__gt=1)

if slug_counts:
    print(f"\n{slug_counts.count()} adet tekrarlayan slug bulundu:\n")
    for item in slug_counts:
        print(f"  '{item['slug']}' - {item['count']} kez")
else:
    print("\nDuplicate slug YOK - OK")

# ============================================================
# 3. AYNI ISIMLI URUNLER (FARKLI KATEGORILERDE)
# ============================================================
print("\n" + "=" * 70)
print("3. AYNI ISIMLI URUNLER")
print("=" * 70)

title_counts = Product.objects.values('title_tr').annotate(
    count=Count('id')
).filter(count__gt=1).order_by('-count')

if title_counts:
    print(f"\n{title_counts.count()} adet ayni isimli urun grubu:\n")
    for item in list(title_counts)[:20]:
        products = Product.objects.filter(title_tr=item['title_tr']).select_related('series', 'category')
        print(f"\n  '{item['title_tr'][:50]}' - {item['count']} kez:")
        for p in products:
            series_name = p.series.name if p.series else 'Serisiz'
            cat_name = p.category.name if p.category else (p.series.category.name if p.series else 'Kategorisiz')
            print(f"    -> Seri: {series_name}, Kategori: {cat_name}")
    if title_counts.count() > 20:
        print(f"\n  ... ve {title_counts.count() - 20} grup daha")
else:
    print("\nAyni isimli urun YOK - OK")

# ============================================================
# 4. BOS VEYA EKSIK ALANLAR
# ============================================================
print("\n" + "=" * 70)
print("4. BOS VEYA EKSIK ALANLAR")
print("=" * 70)

# Bos title_tr
empty_title = Product.objects.filter(Q(title_tr__isnull=True) | Q(title_tr=''))
print(f"\n  Bos title_tr: {empty_title.count()}")
if empty_title.count() > 0:
    for p in empty_title[:5]:
        print(f"    -> {p.name} (slug: {p.slug})")

# Bos name
empty_name = Product.objects.filter(Q(name__isnull=True) | Q(name=''))
print(f"  Bos name: {empty_name.count()}")

# Serisi olmayan urunler
no_series = Product.objects.filter(series__isnull=True)
print(f"  Serisi olmayan urun: {no_series.count()}")
if no_series.count() > 0:
    for p in no_series[:5]:
        print(f"    -> {p.title_tr}")

# Varyantsiz urunler
products_without_variants = Product.objects.annotate(
    variant_count=Count('variants')
).filter(variant_count=0)
print(f"  Varyantsiz urun: {products_without_variants.count()}")
if products_without_variants.count() > 0:
    for p in products_without_variants[:10]:
        print(f"    -> {p.title_tr} (seri: {p.series.name if p.series else '-'})")

# Variant'ta bos model_code
empty_model_code = Variant.objects.filter(Q(model_code__isnull=True) | Q(model_code=''))
print(f"  Bos model_code: {empty_model_code.count()}")

# ============================================================
# 5. ORPHAN SERILER (URUNU OLMAYAN)
# ============================================================
print("\n" + "=" * 70)
print("5. ORPHAN SERILER (Urunu olmayan)")
print("=" * 70)

orphan_series = Series.objects.annotate(
    num_products=Count('products')
).filter(num_products=0)

print(f"\n  Urunu olmayan seri sayisi: {orphan_series.count()}")
if orphan_series.count() > 0:
    print("\n  Ornekler:")
    for s in orphan_series[:20]:
        print(f"    -> {s.category.name} > {s.name}")
    if orphan_series.count() > 20:
        print(f"    ... ve {orphan_series.count() - 20} tane daha")

# ============================================================
# 6. DUPLICATE SERILER (AYNI ISIM, AYNI KATEGORI)
# ============================================================
print("\n" + "=" * 70)
print("6. DUPLICATE SERILER")
print("=" * 70)

dup_series = Series.objects.values('category', 'name').annotate(
    count=Count('id')
).filter(count__gt=1)

if dup_series:
    print(f"\n  {dup_series.count()} adet duplicate seri bulundu:\n")
    for item in list(dup_series)[:20]:
        cat = Category.objects.get(id=item['category'])
        series_list = Series.objects.filter(category=cat, name=item['name']).annotate(
            num_products=Count('products')
        )
        print(f"  '{cat.name}' > '{item['name']}' - {item['count']} kez:")
        for s in series_list:
            print(f"    -> ID: {s.id}, Slug: {s.slug}, Urun sayisi: {s.num_products}")
else:
    print("\nDuplicate seri YOK - OK")

# ============================================================
# 7. COK BENZER URUN ISIMLERI (Levenshtein)
# ============================================================
print("\n" + "=" * 70)
print("7. COK BENZER URUN ISIMLERI")
print("=" * 70)

products = list(Product.objects.values_list('id', 'title_tr', 'series__name'))
similar_pairs = []

# Sadece ayni serideki urunleri karsilastir (performans icin)
by_series = defaultdict(list)
for pid, title, series in products:
    if title:
        by_series[series].append((pid, title))

for series, items in by_series.items():
    if len(items) < 2:
        continue
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            ratio = difflib.SequenceMatcher(None, items[i][1].lower(), items[j][1].lower()).ratio()
            if ratio > 0.85 and items[i][1] != items[j][1]:
                similar_pairs.append((items[i][1], items[j][1], series, ratio))

if similar_pairs:
    print(f"\n  {len(similar_pairs)} adet cok benzer urun cifti bulundu:\n")
    for p1, p2, series, ratio in sorted(similar_pairs, key=lambda x: -x[3])[:20]:
        print(f"  [{ratio:.0%}] Seri: {series}")
        print(f"    1: {p1[:60]}")
        print(f"    2: {p2[:60]}")
        print()
else:
    print("\nCok benzer isim YOK - OK")

# ============================================================
# 8. KATEGORI TUTARSIZLIKLARI
# ============================================================
print("\n" + "=" * 70)
print("8. KATEGORI TUTARSIZLIKLARI")
print("=" * 70)

# Urunun kategorisi ile serisinin kategorisi farkli mi?
mismatched = Product.objects.exclude(
    category__isnull=True
).exclude(
    series__category=django.db.models.F('category')
).select_related('category', 'series', 'series__category')

print(f"\n  Seri kategorisi ile urun kategorisi farkli olan: {mismatched.count()}")
if mismatched.count() > 0:
    for p in mismatched[:10]:
        print(f"    -> {p.title_tr[:40]}")
        print(f"       Urun kategorisi: {p.category.name if p.category else '-'}")
        print(f"       Seri kategorisi: {p.series.category.name if p.series else '-'}")

# ============================================================
# 9. RESMI OLMAYAN URUNLER
# ============================================================
print("\n" + "=" * 70)
print("9. RESMI OLMAYAN URUNLER")
print("=" * 70)

products_without_images = Product.objects.annotate(
    media_count=Count('product_media')
).filter(media_count=0, status='active')

print(f"\n  Resmi olmayan aktif urun: {products_without_images.count()}")

# ============================================================
# 10. ISTATISTIKLER
# ============================================================
print("\n" + "=" * 70)
print("10. GENEL ISTATISTIKLER")
print("=" * 70)

total_categories = Category.objects.count()
total_series = Series.objects.count()
total_products = Product.objects.count()
total_variants = Variant.objects.count()
active_products = Product.objects.filter(status='active').count()
draft_products = Product.objects.filter(status='draft').count()

print(f"""
  Toplam Kategori: {total_categories}
  Toplam Seri: {total_series}
  Toplam Urun Grubu: {total_products}
  Toplam Varyant (Model Kodu): {total_variants}

  Aktif Urun: {active_products}
  Taslak Urun: {draft_products}

  Ortalama varyant/urun: {total_variants/total_products:.1f}
""")

# ============================================================
# 11. KATEGORI BAZLI DAGILIM
# ============================================================
print("\n" + "=" * 70)
print("11. KATEGORI BAZLI DAGILIM")
print("=" * 70)

categories = Category.objects.filter(parent__isnull=True).annotate(
    series_count=Count('series', distinct=True),
    product_count=Count('series__products', distinct=True)
).order_by('-product_count')

print("\nAna kategoriler:\n")
for cat in categories:
    if cat.product_count > 0:
        print(f"  {cat.name}: {cat.series_count} seri, {cat.product_count} urun")

# ============================================================
# OZET
# ============================================================
print("\n" + "=" * 70)
print("ANALIZ OZETI")
print("=" * 70)

issues = []
if model_code_counts.count() > 0:
    issues.append(f"- {model_code_counts.count()} duplicate model kodu")
if slug_counts.count() > 0:
    issues.append(f"- {slug_counts.count()} duplicate slug")
if title_counts.count() > 0:
    issues.append(f"- {title_counts.count()} ayni isimli urun grubu")
if products_without_variants.count() > 0:
    issues.append(f"- {products_without_variants.count()} varyantsiz urun")
if orphan_series.count() > 0:
    issues.append(f"- {orphan_series.count()} urunu olmayan seri")
if dup_series.count() > 0:
    issues.append(f"- {dup_series.count()} duplicate seri")
if mismatched.count() > 0:
    issues.append(f"- {mismatched.count()} kategori tutarsizligi")

if issues:
    print("\nTESPIT EDILEN SORUNLAR:")
    for issue in issues:
        print(f"  {issue}")
else:
    print("\nHicbir sorun tespit edilmedi!")

print("\n" + "=" * 70)
