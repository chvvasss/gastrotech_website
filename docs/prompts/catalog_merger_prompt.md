# FAZ 2: MERGER — Parçaları Birleştir ve Doğrula

Birden fazla worker'ın çıktısını (partial JSON) alıp tek bir `output.json` dosyası ve kalite raporu üret.

## GİRDİ
Sana birden fazla chunk sonucu verilecek. Her biri şu formatta:
```json
{"chunk_id": N, "pages": "X-Y", "products": [...], "image_map": [...]}
```

## GÖREVLER

### 1. Birleştir
- Tüm chunk'lardaki `products` dizilerini birleştir
- Chunk sırasına göre sırala (chunk_id)
- Tüm `image_map` girişlerini birleştir

### 2. Çakışma Kontrolü
- **Aynı `slug`**: İki chunk'ta aynı slug varsa → veriyi birleştir (ürün grup sınırında bölünmüş olabilir)
- **Aynı `model_code`**: Farklı ürünlerde aynı model kodu → HATA olarak raporla
- **Spec key tutarsızlığı**: Aynı özellik farklı key slug'larla mı yazılmış? (ör: `guc` vs `guc_kw`) → Normalize et, birini seç

### 3. Tamamlama
- `seo_title`: Yoksa "{title_tr} - {Brand}" formatında oluştur
- `seo_description`: Yoksa general_features'dan kısa bir cümle üret
- `short_specs`: Yoksa specs'ten en önemli 3 değeri seç
- `images` dizisine `image_map`'ten URL'leri ekle: `"url": "images/{match_to}.jpg"`

### 4. Doğrulama
Her ürün için kontrol et:
- [ ] `slug` benzersiz
- [ ] En az 1 varyant var
- [ ] Her varyantın `model_code`'u benzersiz
- [ ] `category` slug'ı geçerli
- [ ] `brand` slug'ı geçerli
- [ ] Sayısal alanlar gerçekten sayısal

## ÇIKTI

### 1. output.json
Admin panel'e doğrudan import edilebilir format:
```json
[
  {
    "slug": "...",
    "name": "...",
    "title_tr": "...",
    "status": "active",
    "category": "...",
    "series": "...",
    "brand": "...",
    "general_features": [],
    "short_specs": [],
    "notes": [],
    "images": [{"url": "images/XXX.jpg", "is_primary": true, "sort_order": 0, "alt": "..."}],
    "variants": [{"model_code": "...", "name_tr": "...", "dimensions": "...", "weight_kg": 0, "list_price": null, "specs": {}}]
  }
]
```

### 2. Kalite Raporu
```
═══ KATALOG DİJİTALLEŞTİRME RAPORU ═══
PDF: [dosya adı]
Chunk Sayısı: X
Toplam Ürün Grubu: X
Toplam Varyant: X
Toplam Görsel Eşleştirme: X

── KALİTE KONTROL ──
✓/✗ Model kodları benzersiz
✓/✗ Slug'lar benzersiz
✓/✗ Referans verileri geçerli
✓/✗ Spec key'ler tutarlı

── DOĞRULAMA GEREKLİ ──
1. ...
2. ...
════════════════════════════════════════
```

### 3. image_commands.json
Python script'e verilecek yeniden isimlendirme komutları:
```json
[
  {"source": "page3_img0.jpg", "target": "GKO7040.jpg", "is_primary": true},
  {"source": "page4_img0.jpg", "target": "gazli-ocaklar-700_technical.jpg", "is_primary": false}
]
```
