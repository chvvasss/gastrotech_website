# Product Upload Format Specification

This document defines the JSON format for bulk uploading products into the Gastrotech system. This format is designed to support the complete product hierarchy, including Categories, Series, Brands, Taxonomy Nodes, Products, Variants, and Images.

## Overview

The upload format is a **JSON Array** of Product objects. Each Product object contains all necessary information to create or update a product and its related entities.

### Key Features
- **Hierarchy Support**: Links products to Category, Series, and Brand.
- **Taxonomy**: Supports linking to `TaxonomyNode` (e.g., `Ocaklar > Gazlı`).
- **Variants**: Nested list of variants with specific pricing, dimensions, and technical specs.
- **Images**: Inline definition of images (local paths or URLs) to be processed.
- **Content**: Full support for rich text descriptions, features, and SEO metadata.

---

## JSON Structure

### Top Level
```json
[
  {
    // Product 1
  },
  {
    // Product 2
  }
]
```

### Product Object Fields
| Field | Type | Required | Description |
|---|---|---|---|
| `slug` | String | **Yes** | Unique identifier for the URL (e.g., `700-serisi-kompakt-ocak`). |
| `name` | String | **Yes** | Internal system name. |
| `title_tr` | String | **Yes** | Display title in Turkish. |
| `title_en` | String | No | Display title in English. |
| `status` | String | No | `active`, `draft`, or `archived`. Default: `draft`. |
| `is_featured` | Boolean | No | If `true`, shown in featured sections. |
| **Relationships** | | | |
| `category` | String | **Yes** | Slug of the Category (e.g., `pisirme-uniteleri`). |
| `series` | String | No | Slug of the Series. **Optional**. If omitted, products will be assigned to a default series for the category. |
| `brand` | String | **Yes** | Slug of the Brand (e.g., `gastrotech`). |
| `primary_node` | String | No | Slug of the primary Taxonomy Node (e.g., `gazli-ocaklar`). |
| **Content** | | | |
| `general_features` | List[String] | No | List of bullet points (Genel Özellikler). |
| `short_specs` | List[String] | No | 3-5 key specs for cards (e.g., "12 kW", "LPG"). |
| `notes` | List[String] | No | Footnotes or special info. |
| `long_description` | String | No | Detailed HTML or text description. |
| `seo_title` | String | No | SEO Title tag. |
| `seo_description` | String | No | SEO Meta description. |
| **Media** | | | |
| `images` | List[Object] | No | See [Image Object](#image-object) below. |
| **Variants** | | | |
| `variants` | List[Object] | **Yes** | See [Variant Object](#variant-object) below. MUST have at least one. |

### Variant Object
| Field | Type | Required | Description |
|---|---|---|---|
| `model_code` | String | **Yes** | Unique Model Code (e.g., `GKO-700`). |
| `name_tr` | String | **Yes** | Variant name (e.g., "2 Gözlü", "4 Burner"). |
| `sku` | String | No | Stock Keeping Unit (optional). |
| `dimensions` | String | No | Dimensions string (e.g., `400x700x280`). |
| `weight_kg` | Number | No | Weight in kg (can be float). |
| `list_price` | Number | No | List price. |
| `price_override` | Number | No | Override price (optional). |
| `stock_qty` | Integer | No | Stock quantity. Use `null` for unlimited. |
| `specs` | Object | No | Key-Value pairs of technical specs. Keys must match `SpecKey` slugs. |

### Image Object
| Field | Type | Required | Description |
|---|---|---|---|
| `url` | String | **Yes** | URL (http/https) OR Absolute Local Path (e.g., `C:/images/img1.jpg`). |
| `is_primary` | Boolean | No | Set `true` for the main product image. |
| `sort_order` | Integer | No | Ordering (0 = first). |
| `alt` | String | No | Alt text for accessibility. |

---

## Example JSON

```json
[
  {
    "slug": "700-serisi-gazli-ocak",
    "name": "700 Serisi Gazlı Ocak",
    "title_tr": "700 Serisi Gazlı Ocak (4 Gözlü)",
    "title_en": "700 Series Gas Range (4 Burner)",
    "status": "active",
    "category": "pisirme-uniteleri",
    "series": "700-serisi",
    "brand": "gastrotech",
    "primary_node": "ocaklar-gazli",
    "general_features": [
      "Paslanmaz çelik gövde",
      "Emniyet ventilli musluklar",
      "LPG ve Doğalgaz uyumlu"
    ],
    "short_specs": [
      "24 kW Güç",
      "Gazlı",
      "4 Gözlü"
    ],
    "images": [
      {
        "url": "https://example.com/images/gko-700-main.jpg",
        "is_primary": true,
        "alt": "700 Serisi Gazlı Ocak Önden Görünüm"
      },
      {
        "url": "C:\\Users\\emir\\Desktop\\images\\gko-700-detail.jpg",
        "sort_order": 1,
        "alt": "Detay"
      }
    ],
    "variants": [
      {
        "model_code": "GKO-740",
        "name_tr": "4 Gözlü Ocak",
        "dimensions": "800x700x285",
        "weight_kg": 55.5,
        "list_price": 15000.00,
        "stock_qty": 10,
        "specs": {
            "guc": "24 kW",
            "gaz_tipi": "LPG/NG",
            "goz_sayisi": "4"
        }
      },
      {
        "model_code": "GKO-720",
        "name_tr": "2 Gözlü Ocak",
        "dimensions": "400x700x285",
        "weight_kg": 35.0,
        "list_price": 9500.00,
        "specs": {
            "guc": "12 kW",
            "gaz_tipi": "LPG/NG",
            "goz_sayisi": "2"
        }
      }
    ]
  }
]
```

## Validation Rules
1. **Uniqueness**: `slug` (Product) and `model_code` (Variant) must be unique system-wide.
2. **References**: `category`, `series`, `brand` slugs MUST exist in the database before import.
    - If they don't exist, the import script should either error or defined behavior (e.g., skip).
3. **Specs**: Keys in the `specs` object (e.g., `guc`, `gaz_tipi`) should correspond to valid `SpecKey` slugs if you want them to display correctly with icons/labels, though the system stores them as raw JSON so strict validation is optional.
