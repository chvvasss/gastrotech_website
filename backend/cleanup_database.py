"""
Database cleanup script.
Fixes duplicates, orphans, and inconsistencies.
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.db import transaction
from django.db.models import Count
from apps.catalog.models import Category, Series, Product, Variant

def cleanup_orphan_series():
    """Delete series that have no products."""
    print("\n" + "=" * 60)
    print("1. ORPHAN SERİLERİ TEMİZLE")
    print("=" * 60)

    orphan_series = Series.objects.annotate(
        num_products=Count('products')
    ).filter(num_products=0)

    count = orphan_series.count()
    print(f"\n  Silinecek boş seri sayısı: {count}")

    if count > 0:
        # Silmeden önce listele
        print("\n  Silinecek seriler:")
        for s in orphan_series[:30]:
            print(f"    - {s.category.name} > {s.name}")
        if count > 30:
            print(f"    ... ve {count - 30} tane daha")

        # Sil
        deleted = orphan_series.delete()
        print(f"\n  [OK] {deleted[0]} kayit silindi")

    return count


def cleanup_duplicate_series():
    """Merge duplicate series (same name in same category)."""
    print("\n" + "=" * 60)
    print("2. DUPLICATE SERİLERİ BİRLEŞTİR")
    print("=" * 60)

    dup_series = Series.objects.values('category', 'name').annotate(
        count=Count('id')
    ).filter(count__gt=1)

    merged_count = 0

    for item in dup_series:
        cat = Category.objects.get(id=item['category'])
        series_list = list(Series.objects.filter(
            category=cat, name=item['name']
        ).annotate(
            num_products=Count('products')
        ).order_by('-num_products', 'created_at'))

        if len(series_list) < 2:
            continue

        # En çok ürünü olan seriyi tut
        primary_series = series_list[0]
        duplicate_series = series_list[1:]

        print(f"\n  '{cat.name}' > '{item['name']}':")
        print(f"    Ana seri: {primary_series.slug} ({primary_series.num_products} ürün)")

        for dup in duplicate_series:
            # Ürünleri ana seriye taşı
            moved = Product.objects.filter(series=dup).update(series=primary_series)
            print(f"    Birleştirilen: {dup.slug} ({dup.num_products} ürün -> {moved} taşındı)")

            # Boş seriyi sil
            dup.delete()
            merged_count += 1

    print(f"\n  [OK] {merged_count} duplicate seri birlestirildi ve silindi")
    return merged_count


def cleanup_products_without_variants():
    """Delete or list products without any variants."""
    print("\n" + "=" * 60)
    print("3. VARYANTSIZ ÜRÜNLERİ KONTROL ET")
    print("=" * 60)

    products_without_variants = Product.objects.annotate(
        variant_count=Count('variants')
    ).filter(variant_count=0)

    count = products_without_variants.count()
    print(f"\n  Varyantsız ürün sayısı: {count}")

    if count > 0:
        print("\n  Varyantsız ürünler:")
        for p in products_without_variants[:20]:
            series_name = p.series.name if p.series else '-'
            print(f"    - {p.title_tr[:50]} (seri: {series_name})")
        if count > 20:
            print(f"    ... ve {count - 20} tane daha")

        # Bu ürünleri silmek yerine sadece raporluyoruz
        # Silmek isterseniz aşağıdaki satırı aktif edin:
        # deleted = products_without_variants.delete()
        # print(f"\n  ✓ {deleted[0]} varyantsız ürün silindi")
        print("\n  [!] Bu urunler silinmedi (manuel kontrol gerekebilir)")

    return count


def fix_category_inconsistencies():
    """Fix products where category doesn't match series category."""
    print("\n" + "=" * 60)
    print("4. KATEGORİ TUTARSIZLIKLARINI DÜZELT")
    print("=" * 60)

    # Product.category'yi series.category ile eşitle
    mismatched = Product.objects.exclude(
        category__isnull=True
    ).exclude(
        series__category=django.db.models.F('category')
    ).select_related('category', 'series', 'series__category')

    count = mismatched.count()
    print(f"\n  Tutarsız ürün sayısı: {count}")

    if count > 0:
        for p in mismatched:
            old_cat = p.category.name if p.category else '-'
            new_cat = p.series.category.name if p.series else '-'
            print(f"    - {p.title_tr[:40]}: {old_cat} -> {new_cat}")
            p.category = p.series.category
            p.save(update_fields=['category', 'updated_at'])

        print(f"\n  [OK] {count} urunun kategorisi duzeltildi")

    return count


def show_summary():
    """Show database summary after cleanup."""
    print("\n" + "=" * 60)
    print("TEMİZLİK SONRASI ÖZET")
    print("=" * 60)

    total_categories = Category.objects.count()
    total_series = Series.objects.count()
    total_products = Product.objects.count()
    total_variants = Variant.objects.count()

    orphan_series = Series.objects.annotate(
        num_products=Count('products')
    ).filter(num_products=0).count()

    dup_series = Series.objects.values('category', 'name').annotate(
        count=Count('id')
    ).filter(count__gt=1).count()

    variantless = Product.objects.annotate(
        variant_count=Count('variants')
    ).filter(variant_count=0).count()

    print(f"""
  Toplam Kategori: {total_categories}
  Toplam Seri: {total_series}
  Toplam Ürün: {total_products}
  Toplam Varyant: {total_variants}

  Kalan orphan seri: {orphan_series}
  Kalan duplicate seri: {dup_series}
  Kalan varyantsız ürün: {variantless}
""")


def main():
    print("=" * 60)
    print("VERİTABANI TEMİZLİK İŞLEMİ")
    print("=" * 60)

    with transaction.atomic():
        # 1. Önce duplicate serileri birleştir (ürünleri kaybetmemek için)
        cleanup_duplicate_series()

        # 2. Sonra orphan serileri temizle
        cleanup_orphan_series()

        # 3. Kategori tutarsızlıklarını düzelt
        fix_category_inconsistencies()

        # 4. Varyantsız ürünleri kontrol et (silmiyoruz, sadece raporluyoruz)
        cleanup_products_without_variants()

    # Özet
    show_summary()

    print("\n" + "=" * 60)
    print("TEMİZLİK TAMAMLANDI")
    print("=" * 60)


if __name__ == '__main__':
    main()
