# Katalog Dijitalleştirme — Orchestrator Kılavuzu

PDF katalogları Claude Code ile paralel subagent pipeline kullanarak dijitalleştirme sistemi.

## Ön Koşullar
```bash
pip install pymupdf
```

## Hızlı Başlangıç (Önerilen)

`docs/prompts/catalog_master_prompt.md` dosyasını oku ve PDF yolunu ekleyerek Claude Code'a ver:

```
docs/prompts/catalog_master_prompt.md dosyasını oku ve uygula.
PDF: C:\Users\emir\Desktop\kataloglar\pisirme.pdf
```

Master prompt self-contained'dır — tüm kurallar inline olarak içindedir, başka dosya referansı yoktur.

## Nasıl Çalışır

```
ADIM 1: SCOUT          → PDF'i text olarak tara, chunk planı oluştur
ADIM 2: WORKER'LAR     → Her chunk için paralel Task subagent başlat
ADIM 3: MERGER          → Sonuçları birleştir, output.json + image_commands.json yaz
ADIM 4: GÖRSEL ÇIKARMA  → Python script ile PDF'den görselleri çıkar ve isimlendir
ADIM 5: KALİTE RAPORU   → Doğrulama raporu göster
```

## Dosya Yapısı

| Dosya | Amaç |
|-------|------|
| `docs/prompts/catalog_master_prompt.md` | **Ana prompt** — Claude Code'a bunu ver |
| `docs/prompts/catalog_scout_prompt.md` | Scout faz referans (modüler kullanım) |
| `docs/prompts/catalog_worker_prompt.md` | Worker faz referans (modüler kullanım) |
| `docs/prompts/catalog_merger_prompt.md` | Merger faz referans (modüler kullanım) |
| `scripts/catalog_digitize.py` | Python görsel çıkarma script'i |

## Çıktılar

| Dosya | Açıklama |
|-------|----------|
| `output.json` | Admin panel JSON import'a hazır veri |
| `image_commands.json` | Görsel eşleştirme komutları |
| `images/*.jpg` | İsimlendirilmiş ürün görselleri |
| `images/raw/*.jpg` | Ham çıkarılmış görseller |

## Token Bütçesi

| Faz | Token |
|-----|-------|
| Scout (ana session) | ~15K |
| Worker (her biri) | ~25K |
| Merger (ana session) | ~10K |
| **Toplam (50 sayfa PDF)** | **~75K** |

Eski tek prompt: ~150K+ (limit aşımı!) → %50 tasarruf + paralel hız.

## Manuel Kullanım (Alternatif)

Master prompt yerine adım adım:
1. `catalog_scout_prompt.md` ile PDF'i tara
2. `catalog_worker_prompt.md` ile her chunk'ı ayrı ayrı işle
3. `catalog_merger_prompt.md` ile birleştir
4. `python scripts/catalog_digitize.py pipeline PDF_YOLU image_commands.json`

## Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| Worker token limit | Chunk boyutunu 10→5 sayfaya düşür |
| Görsel eşleşmiyor | `images/extraction_metadata.json` ile `image_map`'i karşılaştır |
| Model kodu çakışması | Merger kalite raporunu kontrol et |
| Subagent dosya okuyamıyor | Master prompt kullan (tüm kurallar inline) |
