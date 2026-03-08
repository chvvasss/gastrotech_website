# FAZ 0: SCOUT — PDF Katalog Harita Çıkarma

PDF'i hızlıca tarayıp sayfa haritası ve chunk planı oluştur.

## GÖREV
1. PDF'in HER sayfasını TEXT olarak oku (Read tool, pages parametresi ile)
2. Her sayfanın konusunu/başlığını tek satırda özetle
3. Ürün grubu sınırlarını tespit et (bir ürün grubu hangi sayfalarda?)
4. Boş/kapak/içindekiler/dipnot sayfalarını işaretle
5. PDF genelindeki marka ve kategori bilgisini belirle

## ÇIKTI FORMATI
Aşağıdaki JSON'u ÇIK olarak döndür (başka açıklama ekleme):

```json
{
  "pdf_path": "dosya/yolu.pdf",
  "total_pages": 42,
  "category": "pisirme",
  "brand": "gtech",
  "series_prefix": "700-serisi",
  "page_map": [
    {"page": 1, "type": "cover", "title": "Kapak"},
    {"page": 2, "type": "toc", "title": "İçindekiler"},
    {"page": 3, "type": "product", "title": "Gazlı Ocaklar", "product_group": "gazli-ocaklar"},
    {"page": 4, "type": "product", "title": "Gazlı Ocaklar (devam)", "product_group": "gazli-ocaklar"},
    {"page": 5, "type": "product", "title": "Elektrikli Ocaklar", "product_group": "elektrikli-ocaklar"}
  ],
  "chunks": [
    {"id": 1, "pages": "3-8",   "groups": ["gazli-ocaklar", "elektrikli-ocaklar"]},
    {"id": 2, "pages": "9-16",  "groups": ["kizartma-tavasi", "izgara"]},
    {"id": 3, "pages": "17-24", "groups": ["firinlar", "benmari"]},
    {"id": 4, "pages": "25-32", "groups": ["makarna-pisirici", "notr-elemanlar"]},
    {"id": 5, "pages": "33-42", "groups": ["aksesuarlar"]}
  ]
}
```

## CHUNK KURALLARI
- Her chunk MAX 10 sayfa
- Bir ürün grubunu ORTADAN BÖLME (grup sınırına göre kes)
- Kapak, içindekiler, boş sayfaları chunk'a dahil etme
- Çok kısa grupları (1-2 sayfa) komşu chunk'a birleştir

## KATEGORİ SLUG REFERANSI
Aşağıdakilerden birini seç:
`bulasik`, `firinlar`, `hazirlik`, `kafeterya`, `pisirme`, `sogutma`, `tamamlayici`, `camasirhane`

## MARKA SLUG REFERANSI
Aşağıdakilerden birini seç:
`salva`, `vital`, `asterm`, `mychef`, `electrolux`, `gtech`, `frenox`, `scotsman`, `essedue`, `lerica`, `cgf`, `vitella`, `dalle`

Eğer katalogdaki marka/kategori bu listede yoksa, en yakın eşleşmeyi yaz ve `"unknown_brand": true` ekle.
