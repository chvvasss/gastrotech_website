#!/usr/bin/env python3
"""Upload remaining 4 PDFs that failed due to rate limiting."""

import os
import sys
import io
import time
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

API = "https://api.gastrotech.com.tr/api/v1"
PDF_DIR = r"C:\Users\emir\Desktop\pdfler\sikistirilmis"

token = requests.post(f"{API}/auth/login/", json={
    "email": "admin@gastrotech.com",
    "password": "admin123",
}).json()["access"]
headers = {"Authorization": f"Bearer {token}"}
print("Login OK")

remaining = [
    ("pişirme electrolux 900 serisi.pdf", "44848d6f-f6f1-41bf-9892-0827dbbb0752", "Pişirme Electrolux 900 Serisi", "Cooking Electrolux 900 Series", 11),
    ("soğutma.pdf", "79c4a96c-c309-4f95-af25-91271da7a4e5", "Soğutma Sistemleri", "Cooling Systems", 12),
    ("tamamlayıcı.pdf", "f522a4aa-bdb2-4f9b-81ae-8940e976022a", "Tamamlayıcı Ekipmanlar", "Complementary Equipment", 13),
    ("çamaşır.pdf", "bc6f7c81-3086-4e4b-b27a-2c28b93a6619", "Çamaşır Makineleri", "Laundry Machines", 14),
]

for filename, cat_id, title_tr, title_en, order in remaining:
    filepath = os.path.join(PDF_DIR, filename)
    if not os.path.isfile(filepath):
        print(f"DOSYA BULUNAMADI: {filename}")
        continue

    size_mb = os.path.getsize(filepath) / 1024 / 1024
    print(f"\nYukleniyor: {filename} ({size_mb:.1f} MB)...")

    for attempt in range(3):
        with open(filepath, "rb") as f:
            files = {"file": (filename, f, "application/pdf")}
            resp = requests.post(f"{API}/admin/media/upload/", headers=headers, files=files, timeout=120)

        if resp.status_code == 201:
            break
        elif resp.status_code == 429:
            wait = 20
            print(f"  Rate limit, {wait}s bekleniyor... (deneme {attempt + 1}/3)")
            time.sleep(wait)
        else:
            print(f"  Hata: {resp.status_code} - {resp.text[:200]}")
            break

    if resp.status_code != 201:
        print(f"  Media yuklenemedi, atlaniyor.")
        continue

    media_id = resp.json()["id"]
    print(f"  Media OK: {media_id}")

    data = {
        "category": cat_id,
        "media": media_id,
        "title_tr": title_tr,
        "title_en": title_en,
        "order": order,
        "published": True,
    }
    resp2 = requests.post(f"{API}/admin/category-catalogs/", headers=headers, json=data)
    if resp2.status_code == 201:
        print(f"  CategoryCatalog OK: {resp2.json()['id']}")
    else:
        print(f"  CategoryCatalog HATA: {resp2.status_code} - {resp2.text[:200]}")

    time.sleep(5)

# Verify
print("\n=== DOGRULAMA ===")
resp = requests.get(f"{API}/admin/category-catalogs/", headers=headers)
catalogs = resp.json()
print(f"Toplam CategoryCatalog: {len(catalogs)}")
for c in catalogs:
    t = c.get("title_tr", "?")
    cn = c.get("category_name", "?")
    sz = c.get("media_details", {}).get("size_bytes", 0)
    print(f"  - {t} | {cn} | {sz / 1024 / 1024:.1f} MB")

resp2 = requests.get(f"{API}/admin/catalog-assets/", headers=headers)
print(f"\nKalan CatalogAsset: {len(resp2.json())}")
