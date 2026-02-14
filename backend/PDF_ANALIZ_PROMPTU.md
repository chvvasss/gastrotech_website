# GASTROTECH PDF KATALOG ANALİZ PROMPTU

Aşağıdaki promptu, PDF katalog dosyasını yüklediğin AI aracına (ChatGPT, Claude vb.) yapıştır. PDF'i yükle ve promptu gönder.

---

## PROMPT:

```
Sen bir endüstriyel mutfak ekipmanları uzmanısın. Sana yüklediğim PDF katalogdan TÜM ürünleri çıkarmanı istiyorum.

## GÖREV
Bu PDF katalogdaki HER ÜRÜNü aşağıdaki Excel formatına uygun şekilde çıkar. Sadece metinleri değil, GÖRSELLERİ DE ANALİZ ET. Her görseldeki ürünün ne olduğunu belirle.

## ÇIKTI FORMATI (Excel sütunları)
Her ürün için şu bilgileri doldur:

| Sütun | Açıklama | Örnek |
|-------|----------|-------|
| Sıra No | Sıralı numara | 1, 2, 3... |
| Kategori | Ana kategori | Pişirme Ekipmanları |
| Seri | Alt seri adı | 600 Serisi |
| Ürün Adı TR | Türkçe ürün adı | 2 Yanıslı Gazlı Ocak |
| Ürün Adı EN | İngilizce ürün adı | 2 Burner Gas Range |
| Model Kodu | Benzersiz model kodu | GKO6010 |
| SKU | Stok kodu (varsa) | |
| Boyutlar (GxDxY mm) | Genişlik x Derinlik x Yükseklik | 400x700x300 |
| Ağırlık (kg) | Net ağırlık | 35 |
| Güç (W/kW) | Elektrik gücü | 12 |
| Voltaj | Elektrik bilgisi | 220-230V 1N AC 50Hz |
| Kapasite | Litre, kişi, GN | 40L |
| Yakıt Tipi | Elektrik / Doğalgaz / LPG | Doğalgaz |
| Malzeme | Ana malzeme | Paslanmaz çelik |
| Ek Spec 1 Anahtar | Ekstra özellik adı | pilot_flame |
| Ek Spec 1 Değer | Ekstra özellik değeri | evet |
| Ek Spec 2 Anahtar | | thermocouple |
| Ek Spec 2 Değer | | evet |
| Ek Spec 3 Anahtar | | oven_type |
| Ek Spec 3 Değer | | statik |
| Genel Özellikler TR | Pipe ile ayrılmış | Paslanmaz çelik gövde\|Gaz emniyet tertibatı |
| Genel Özellikler EN | Pipe ile ayrılmış | Stainless steel body\|Gas safety device |
| Uzun Açıklama TR | Detaylı açıklama | |
| Uzun Açıklama EN | Detailed description | |
| Liste Fiyatı | Fiyat (varsa) | |
| Durum | active | active |
| Foto 1 (Sayfa-Sıra) | PDF sayfa no - görselin sırası | 9-1 |
| Foto 2 (Sayfa-Sıra) | | 9-2 |
| Foto 3 (Sayfa-Sıra) | | |
| Foto 4 (Sayfa-Sıra) | | |
| Foto 5 (Sayfa-Sıra) | | |
| Notlar | Ek bilgiler | |

## KRİTİK KURALLAR

### 1. GÖRSEL ANALİZİ (ÇOK ÖNEMLİ)
- Her sayfadaki görselleri TEK TEK analiz et
- Her görselin hangi ürüne ait olduğunu belirle
- Görselleri SOLDAN SAĞA, YUKARDAN AŞAĞI numaralandır
- Format: SAYFA_NUMARASI-GÖRSEL_SIRASI (örnek: 9-1 = Sayfa 9'daki 1. görsel)
- Eğer bir görselde model kodu yazıyorsa, o kodu kullan
- Eğer model kodu görünmüyorsa, görseldeki ekipmanı tanımla ve en yakın ürünle eşleştir
- Bir ürünün birden fazla görseli olabilir (farklı açılar, detay çekimleri)
- Genel kategori görselleri (header, banner) varsa bunları NOT olarak belirt

### 2. ÜRÜN ÇIKARIMI
- Tablolardaki HER satırı bir varyant olarak çıkar
- Model kodu olan her şey ayrı bir satır olmalı
- Teknik tablo verilerini (boyut, ağırlık, güç, voltaj) doğru sütunlara yerleştir
- Eğer bir ürün grubu altında birden fazla model varsa, her model ayrı satır
- Aynı ürün adı + farklı model kodu = farklı varyant (aynı Ürün Adı TR yazılır)

### 3. KATEGORİ VE SERİ
Mevcut kategoriler:
- Pişirme Ekipmanları (Seriler: 600 Serisi, 700 Serisi, 900 Serisi, Drop-in Serisi, Diğer)
- Fırınlar (Seriler: PRIME, NEVO, MAESTRO Serisi, MIX, GR, KWIK-CO Serisi, Taş Tabanlı Bakery Fırınlar)
- Soğutma Üniteleri (Seriler: Basic Serisi, Premium Serisi, B Serisi, DKP Kasa Serisi, DXN Serisi, Paslanmaz Çelik Serisi, Yerli Üretim)
- Buz Makineleri (Seriler: Scotsman, AC Serisi, AF Serisi, EC Serisi, MF Serisi, MXG Serisi, NU Serisi, NW Serisi)
- Hazırlık Ekipmanları (Seriler: Kitchen Aid, Diğer)
- Kafeterya Ekipmanları (Seriler: ALL GROUND, Diğer)
- Tamamlayıcı Ekipmanlar (Seriler: CBU Serisi, Diğer)
- Bulaşıkhane
- Çamaşırhane
- Aksesuarlar

Eğer ürün mevcut kategorilere uymuyorsa, en uygun kategori adını yaz.

### 4. TEKNİK BİLGİLER
- Boyutlar HER ZAMAN mm cinsinden GxDxY formatında (Genişlik x Derinlik x Yükseklik)
- Güç kW cinsinden (W ise 1000'e böl)
- Voltaj TAM olarak yaz: "220-230V 1N AC 50Hz" veya "380-415V 3N AC 50Hz"
- Ağırlık kg cinsinden

### 5. GENEL ÖZELLİKLER
- Her özelliği | (pipe) karakteri ile ayır
- Hem TR hem EN olarak yaz
- PDF'deki madde işaretli listeleri kullan
- Ortak özellikler (tüm seride geçerli olanlar) her ürüne eklenmeli

### 6. EK SPEC ALANLARI
Teknik tabloda standart sütunlar dışında kalan özellikler için kullan:
- pilot_flame (pilot alevli mi)
- thermocouple (termokupl var mı)
- thermostat (termostat aralığı)
- oven_type (fırın tipi: statik/konveksiyonel)
- gas_safety (gaz emniyet tertibatı)
- burner_type (brülör tipi)
- plate_type (pleyt tipi: yuvarlak/kare)
- grid_type (ızgara tipi: pik döküm/paslanmaz)

## ÇIKTI
- Çıktıyı TSV (tab-separated) veya Excel uyumlu tablo formatında ver
- HER ürünü atlamadan listele
- Foto referanslarını MUTLAKA doldur - bu en önemli bilgilerden biri
- Eşleştiremediğin görselleri "Notlar" sütununda belirt
- Sayfa numaralarını PDF'deki gerçek sayfa numarasıyla eşle

## BAŞLA
Şimdi PDF'i sayfa sayfa analiz et. Her sayfada:
1. Önce görselleri say ve numaralandır (soldan sağa, yukardan aşağı)
2. Sonra metinleri ve tabloları oku
3. Görselleri ürünlerle eşleştir
4. Tabloyu doldur

HİÇBİR ÜRÜNÜ VE HİÇBİR GÖRSELİ ATLAMA. Her sayfayı ayrı ayrı ve detaylıca analiz et.
```

---

## KULLANIM TALİMATLARI

1. Yukarıdaki promptu kopyala
2. AI aracına (Claude/ChatGPT) yapıştır
3. PDF katalogu yükle
4. AI çıktısını Excel'e yapıştır veya TSV olarak kaydet
5. `urun_yukleme_sablonu.xlsx` formatına uygun hale getir
6. Import scriptine ver

## NOTLAR
- Büyük PDF'ler için sayfa aralığı belirtebilirsin: "Sayfa 1-20'yi analiz et" sonra "Sayfa 21-40'ı analiz et"
- AI görselleri analiz edemezse, görsellerin altındaki/yanındaki model kodlarını kullanır
- Foto referans sistemi: SAYFA-SIRA formatı (9-1 = PDF sayfa 9, o sayfadaki 1. görsel)
