#!/usr/bin/env python3
"""
Catalog Migration Script
========================
1. Delete all CatalogAsset records (ana katalog - wrong location)
2. Delete all CategoryCatalog records (old PDFs)
3. Upload new compressed PDFs and create CategoryCatalog records

Usage:
    python scripts/catalog_migrate.py
"""

import os
import sys
import time
import io
import requests

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

API_BASE = "https://api.gastrotech.com.tr/api/v1"
ADMIN_EMAIL = "admin@gastrotech.com"
ADMIN_PASSWORD = "admin123"

PDF_DIR = r"C:\Users\emir\Desktop\pdfler\sikistirilmis"

# PDF filename -> (category_id, title_tr, title_en)
PDF_CATEGORY_MAP = {
    "bulaşık.pdf": ("6624c9f9-6072-463e-9f7d-0180b1c5b0c2", "Bulaşık Makineleri", "Dishwashers"),
    "fırınlar.pdf": ("c8e24a7f-348e-44c0-9e1c-ca80e2fa8ee7", "Fırınlar", "Ovens"),
    "hazırlık ekipmanları.pdf": ("7e7773af-4e48-46bd-b8dd-6f2435547958", "Hazırlık Ekipmanları", "Preparation Equipment"),
    "kafeterya.pdf": ("cd50c9f1-9ee2-450a-81ff-19fda6c90521", "Kafeterya Ekipmanları", "Cafeteria Equipment"),
    "pişirme 600 serisi.pdf": ("44848d6f-f6f1-41bf-9892-0827dbbb0752", "Pişirme 600 Serisi", "Cooking 600 Series"),
    "pişirme 700 serisi.pdf": ("44848d6f-f6f1-41bf-9892-0827dbbb0752", "Pişirme 700 Serisi", "Cooking 700 Series"),
    "pişirme 900 serisi.pdf": ("44848d6f-f6f1-41bf-9892-0827dbbb0752", "Pişirme 900 Serisi", "Cooking 900 Series"),
    "pişirme diğer serisi.pdf": ("44848d6f-f6f1-41bf-9892-0827dbbb0752", "Pişirme Diğer Serisi", "Cooking Other Series"),
    "pişirme drop-in serisi.pdf": ("44848d6f-f6f1-41bf-9892-0827dbbb0752", "Pişirme Drop-In Serisi", "Cooking Drop-In Series"),
    "pişirme electrolux 700 serisi.pdf": ("44848d6f-f6f1-41bf-9892-0827dbbb0752", "Pişirme Electrolux 700 Serisi", "Cooking Electrolux 700 Series"),
    "pişirme electrolux 900 serisi.pdf": ("44848d6f-f6f1-41bf-9892-0827dbbb0752", "Pişirme Electrolux 900 Serisi", "Cooking Electrolux 900 Series"),
    "soğutma.pdf": ("79c4a96c-c309-4f95-af25-91271da7a4e5", "Soğutma Sistemleri", "Cooling Systems"),
    "tamamlayıcı.pdf": ("f522a4aa-bdb2-4f9b-81ae-8940e976022a", "Tamamlayıcı Ekipmanlar", "Complementary Equipment"),
    "çamaşır.pdf": ("bc6f7c81-3086-4e4b-b27a-2c28b93a6619", "Çamaşır Makineleri", "Laundry Machines"),
}


def login():
    """Get JWT access token."""
    resp = requests.post(f"{API_BASE}/auth/login/", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
    })
    resp.raise_for_status()
    token = resp.json()["access"]
    print(f"✓ Login OK")
    return {"Authorization": f"Bearer {token}"}


def delete_all_catalog_assets(headers):
    """Delete all CatalogAsset records (ana katalog section)."""
    print("\n=== CatalogAsset Silme (Ana Katalog) ===")
    resp = requests.get(f"{API_BASE}/admin/catalog-assets/", headers=headers)
    resp.raise_for_status()
    assets = resp.json()

    if not assets:
        print("  Hiç CatalogAsset kaydı yok.")
        return 0

    count = 0
    for asset in assets:
        aid = asset["id"]
        title = asset.get("title_tr", "?")
        r = requests.delete(f"{API_BASE}/admin/catalog-assets/{aid}/", headers=headers)
        if r.status_code in (204, 200):
            print(f"  ✓ Silindi: {title} ({aid})")
            count += 1
        else:
            print(f"  ✗ Silinemedi: {title} ({aid}) -> {r.status_code}: {r.text[:200]}")
    print(f"  Toplam {count}/{len(assets)} CatalogAsset silindi.")
    return count


def delete_all_category_catalogs(headers):
    """Delete all CategoryCatalog records (kategori PDF'leri section)."""
    print("\n=== CategoryCatalog Silme (Kategori PDF'leri) ===")
    resp = requests.get(f"{API_BASE}/admin/category-catalogs/", headers=headers)
    resp.raise_for_status()
    catalogs = resp.json()

    if not catalogs:
        print("  Hiç CategoryCatalog kaydı yok.")
        return 0

    count = 0
    for cat in catalogs:
        cid = cat["id"]
        title = cat.get("title_tr", "?")
        cat_name = cat.get("category_name", "?")
        r = requests.delete(f"{API_BASE}/admin/category-catalogs/{cid}/", headers=headers)
        if r.status_code in (204, 200):
            print(f"  ✓ Silindi: {title} ({cat_name}) ({cid})")
            count += 1
        else:
            print(f"  ✗ Silinemedi: {title} ({cid}) -> {r.status_code}: {r.text[:200]}")
    print(f"  Toplam {count}/{len(catalogs)} CategoryCatalog silindi.")
    return count


def upload_media(filepath, headers):
    """Upload a PDF file and return Media ID."""
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    print(f"  Yükleniyor: {filename} ({filesize / 1024 / 1024:.1f} MB)...", end=" ", flush=True)

    with open(filepath, "rb") as f:
        files = {"file": (filename, f, "application/pdf")}
        resp = requests.post(
            f"{API_BASE}/admin/media/upload/",
            headers=headers,
            files=files,
            timeout=120,
        )

    if resp.status_code == 201:
        media_id = resp.json()["id"]
        print(f"✓ Media ID: {media_id}")
        return media_id
    else:
        print(f"✗ HATA {resp.status_code}: {resp.text[:300]}")
        return None


def create_category_catalog(headers, category_id, media_id, title_tr, title_en, order):
    """Create a CategoryCatalog record."""
    data = {
        "category": category_id,
        "media": media_id,
        "title_tr": title_tr,
        "title_en": title_en,
        "order": order,
        "published": True,
    }
    resp = requests.post(
        f"{API_BASE}/admin/category-catalogs/",
        headers=headers,
        json=data,
    )
    if resp.status_code == 201:
        cc_id = resp.json()["id"]
        print(f"  ✓ CategoryCatalog oluşturuldu: {title_tr} -> {cc_id}")
        return cc_id
    else:
        print(f"  ✗ CategoryCatalog oluşturulamadı: {title_tr} -> {resp.status_code}: {resp.text[:300]}")
        return None


def main():
    print("=" * 60)
    print("GastroTech Katalog Migrasyon Scripti")
    print("=" * 60)

    # Check PDF directory
    if not os.path.isdir(PDF_DIR):
        print(f"HATA: PDF dizini bulunamadı: {PDF_DIR}")
        sys.exit(1)

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    print(f"\nPDF dizini: {PDF_DIR}")
    print(f"Bulunan PDF sayısı: {len(pdf_files)}")

    # Verify all PDFs are mapped
    unmapped = [f for f in pdf_files if f not in PDF_CATEGORY_MAP]
    if unmapped:
        print(f"UYARI: Eşleştirilmemiş PDF'ler: {unmapped}")

    # Login
    headers = login()

    # Step 1: Delete CatalogAsset records
    delete_all_catalog_assets(headers)

    # Step 2: Delete CategoryCatalog records
    delete_all_category_catalogs(headers)

    # Step 3: Upload new PDFs and create CategoryCatalog records
    print("\n=== Yeni PDF'leri Yükleme ve CategoryCatalog Oluşturma ===")
    success_count = 0
    order = 1

    for pdf_name, (category_id, title_tr, title_en) in PDF_CATEGORY_MAP.items():
        filepath = os.path.join(PDF_DIR, pdf_name)
        if not os.path.isfile(filepath):
            print(f"\n  ✗ Dosya bulunamadı: {pdf_name}")
            continue

        print(f"\n[{order}/{len(PDF_CATEGORY_MAP)}] {pdf_name}")

        # Upload media
        media_id = upload_media(filepath, headers)
        if not media_id:
            continue

        # Create CategoryCatalog
        cc_id = create_category_catalog(headers, category_id, media_id, title_tr, title_en, order)
        if cc_id:
            success_count += 1

        order += 1
        time.sleep(0.5)  # Rate limit

    # Summary
    print("\n" + "=" * 60)
    print(f"SONUÇ: {success_count}/{len(PDF_CATEGORY_MAP)} CategoryCatalog başarıyla oluşturuldu.")
    print("=" * 60)

    # Verify
    print("\n=== Doğrulama ===")
    resp = requests.get(f"{API_BASE}/admin/category-catalogs/", headers=headers)
    if resp.status_code == 200:
        catalogs = resp.json()
        print(f"Toplam CategoryCatalog: {len(catalogs)}")
        for c in catalogs:
            title = c.get("title_tr", "?")
            cat_name = c.get("category_name", "?")
            size = c.get("media_details", {}).get("size_bytes", 0)
            print(f"  - {title} | Kategori: {cat_name} | Boyut: {size / 1024 / 1024:.1f} MB")
    else:
        print(f"Doğrulama başarısız: {resp.status_code}")

    resp2 = requests.get(f"{API_BASE}/admin/catalog-assets/", headers=headers)
    if resp2.status_code == 200:
        assets = resp2.json()
        print(f"\nKalan CatalogAsset: {len(assets)}")
    else:
        print(f"CatalogAsset kontrol başarısız: {resp2.status_code}")


if __name__ == "__main__":
    main()
