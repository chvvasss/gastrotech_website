# FAZ 1: WORKER — Katalog Chunk Veri Çıkarma

PDF'in belirtilen sayfalarını hem TEXT hem GÖRSEL olarak derinlemesine incele ve yapılandırılmış veri çıkar.

## PARAMETRELER
- **PDF**: `{{PDF_PATH}}`
- **Sayfalar**: `{{PAGES}}` (ör: "3-12")
- **Kategori**: `{{CATEGORY}}` (ör: "pisirme")
- **Marka**: `{{BRAND}}` (ör: "gtech")
- **Seri**: `{{SERIES}}` (ör: "700-serisi")

## İNCELEME YÖNTEMİ
Her sayfayı ÇİFT KATMANLI incele:
1. **TEXT**: Tüm metni oku, tabloları yapılandır, model kodlarını çıkar
2. **GÖRSEL**: Sayfayı görsel olarak incele — tablo yapısını doğrula, ürün fotoğraflarını tespit et, OCR'ın kaçırdığı detayları yakala
3. **ÇAPRAZ DOĞRULAMA**: Metin ile görsel uyuşmuyorsa, görsel veriyi tercih et

## VERİ ÇIKARIM KURALLARI

### Slug
Türkçe→ASCII (ç→c, ğ→g, ı→i, ö→o, ş→s, ü→u), boşluk→tire, küçük harf, özel karakter yok.
Örnek: "Gazlı Ocak 700" → `gazli-ocak-700`

### Model Kodu
Katalogdaki kodu AYNEN al. Benzersiz olmalı. Genellikle büyük harf+rakam (GKO7040).

### Specs (Teknik Özellikler)
Tablo sütunlarını spec key'e çevir:
- Sütun başlığı → slug (Türkçe→ASCII, boşluk→alt çizgi, küçük harf)
- "Güç (kW)" → `guc`, value: "24"
- "Gaz Tipi" → `gaz_tipi`, value: "LPG/NG"
- **İSTİSNA**: Boyutlar → `dimensions` alanına "GxDxY" mm olarak yaz (specs'e değil)
- **İSTİSNA**: Ağırlık → `weight_kg` alanına sayısal yaz (specs'e değil)

### Görseller
Her sayfadaki ürün fotoğraflarını tespit et:
- Logo/dekoratif görselleri ATLA
- Her görseli en yakın model kodu veya ürün grubuyla eşleştir
- `image_map` listesine kaydet (aşağıdaki formatta)

## ÇIKTI FORMATI

İki bölüm döndür: `products` ve `image_map`.

```json
{
  "chunk_id": 1,
  "pages": "3-8",
  "products": [
    {
      "slug": "gazli-ocaklar-700",
      "name": "Gazlı Ocaklar",
      "title_tr": "700 Serisi Gazlı Ocaklar",
      "status": "active",
      "category": "{{CATEGORY}}",
      "series": "{{BRAND}}-{{SERIES}}",
      "brand": "{{BRAND}}",
      "general_features": ["AISI 304 paslanmaz çelik", "CE belgeli"],
      "short_specs": ["Gazlı", "700 Serisi"],
      "notes": [],
      "variants": [
        {
          "model_code": "GKO7040",
          "name_tr": "4 Gözlü Gazlı Ocak",
          "dimensions": "800x730x280",
          "weight_kg": 58.0,
          "list_price": null,
          "specs": {"guc_kw": "24", "goz_sayisi": "4", "gaz_tipi": "LPG/NG"}
        }
      ]
    }
  ],
  "image_map": [
    {"page": 3, "position": "top-right", "description": "Gazlı ocak ürün fotoğrafı", "match_to": "GKO7040", "is_primary": true},
    {"page": 4, "position": "bottom", "description": "Teknik çizim", "match_to": "gazli-ocaklar-700", "is_primary": false, "suffix": "_technical"}
  ]
}
```

## ÖZEL DURUMLAR
- **Aksesuarlar**: Ayrı varyant DEĞİL → `notes`'a ekle
- **Devam eden tablo**: Önceki sayfanın devamıysa birleştir
- **Birden fazla ürün grubu**: Ayrı product objeleri oluştur
- **Bilinmeyen veri**: null bırak, UYDURMA. `notes`'a "DOĞRULAMA GEREKLİ: ..." ekle
- **Birim**: Boyut=mm, Ağırlık=kg, Güç=kW (gerekirse dönüştür)
