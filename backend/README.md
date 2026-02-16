# Gastrotech B2B Catalog Backend

Production-grade Django REST API for B2B product catalog management. Built with Django 5.x, Django REST Framework, and PostgreSQL.

## Features

- **Custom User Model**: Email-based authentication with admin/editor roles
- **JWT Authentication**: Secure token-based auth with refresh tokens
- **OpenAPI/Swagger**: Auto-generated API documentation
- **Health Endpoint**: Monitor database and Redis connectivity
- **Docker Ready**: Full Docker Compose setup for development
- **Production Hardened**: Secure settings for production deployment
- **Payment Ready**: Architecture prepared for payment integration
- **Media Management**: Upload and manage images/PDFs directly in PostgreSQL
- **B2B Inquiries**: Lead capture with honeypot spam protection
- **Cache Invalidation**: Automatic cache clearing on data changes
- **Catalog Assets**: PDF catalog download management

## Tech Stack

- Python 3.12
- Django 5.x
- Django REST Framework
- PostgreSQL 16
- Redis 7
- Simple JWT
- drf-spectacular (OpenAPI)
- Gunicorn (production)
- Whitenoise (static files)

## Project Structure

```
backend/
├── apps/
│   ├── common/          # Shared models (SiteSetting), utilities, slugify
│   ├── accounts/        # Custom User model (email-based), JWT auth
│   ├── catalog/         # Products, categories, brands, series, media, specs
│   ├── orders/          # Cart system (anonymous + authenticated)
│   ├── inquiries/       # Lead capture, quote composition, honeypot
│   ├── blog/            # Blog posts, categories, tags
│   ├── ops/             # Operational scripts and bulk imports
│   └── api/             # API routing and versioning (v1)
├── config/
│   ├── settings/
│   │   ├── base.py      # Base settings (shared)
│   │   ├── dev.py       # Development settings
│   │   └── prod.py      # Production settings (hardened)
│   ├── urls.py
│   ├── asgi.py          # Requires explicit DJANGO_SETTINGS_MODULE
│   └── wsgi.py          # Requires explicit DJANGO_SETTINGS_MODULE
├── fixtures/
│   ├── catalog_metadata.json    # Category definitions
│   ├── catalog_pdfs/            # 14 PDF catalog files
│   └── full_site_data.json       # Full data export (via export_full_data v2.0)
├── docker/
│   └── web/
│       ├── Dockerfile
│       ├── Dockerfile.prod
│       └── entrypoint.sh        # Auto-migration + optional SEED_DATA
├── Gastrotech_Tum_Veriler.xlsx  # Product data source
├── urunlerfotoupload/           # 2900+ product images (PNG)
├── manage.py
├── requirements.txt
├── docker-compose.yml           # Development (runserver)
├── docker-compose.prod.yml      # Production (gunicorn + nginx)
├── .env.example
└── README.md
```

## Quick Start (Docker)

### Prerequisites

- Docker and Docker Compose installed
- Git

### Full Setup (with all product data, images, catalogs)

```bash
# 1. Clone and enter directory
git clone <repo-url>
cd gastrotech_website-main/backend

# 2. Copy environment file
cp .env.example .env

# 3. Start all services
docker compose up --build

# 4. Run full setup (categories, brands, products, images, catalogs, admin user)
docker compose exec web python manage.py setup_full

# 5. Access the application
#    Backend API:  http://localhost:8000
#    Swagger UI:   http://localhost:8000/api/v1/docs/
#    Django Admin:  http://localhost:8000/admin/
#    Health Check:  http://localhost:8000/api/v1/health/
```

**Admin login:** admin@gastrotech.com / admin123

### Quick Setup (skip images for speed)

```bash
docker compose exec web python manage.py setup_full --skip-images
```

### Auto-Seed on Docker Startup

Add `SEED_DATA=1` to docker-compose environment for automatic first-time setup:

```yaml
environment:
  - SEED_DATA=1           # Run setup_full on startup
  - SEED_SKIP_IMAGES=1    # Optional: skip images for speed
```

### What `setup_full` Does

1. Runs database migrations
2. Loads categories from `fixtures/catalog_metadata.json`
3. Imports catalog PDFs from `fixtures/catalog_pdfs/`
4. Seeds master hierarchy (brands, series, logo groups)
5. Imports products from `Gastrotech_Tum_Veriler.xlsx`
6. Uploads product images from `urunlerfotoupload/`
7. Syncs spec keys from imported data
8. Sets default site settings
9. Creates dev admin user
10. Clears cache

### Data Export/Import (Full Site Reconstruction)

The export/import system covers ALL site data — media (images, PDFs, logos, favicons),
categories, brands, products, variants, blog posts, settings, and more (22 data sections).

```bash
# Export EVERYTHING including binary media (images, PDFs, logos)
python manage.py export_full_data
# Output: fixtures/full_site_data.json (includes binary data by default)

# Export metadata only (much smaller file, no images/PDFs)
python manage.py export_full_data --skip-media-bytes

# Import full site data (idempotent — safe to re-run)
python manage.py import_full_data
# Or from specific file:
python manage.py import_full_data --file fixtures/full_site_data.json

# Dry run (preview what would be imported)
python manage.py import_full_data --dry-run
```

### Access Points

- **Swagger UI**: http://localhost:8000/api/v1/docs/
- **OpenAPI Schema**: http://localhost:8000/api/v1/schema/
- **Django Admin**: http://localhost:8000/admin/
- **Health Check**: http://localhost:8000/api/v1/health/

### Testing Protected Endpoints in Swagger UI

The Swagger UI supports Bearer JWT authentication. Follow these steps to test protected (admin) endpoints:

1. **Get JWT token**

   First, call the login endpoint to get your access token:

   - In Swagger UI, find `POST /api/v1/auth/login/`
   - Click "Try it out"
   - Enter your credentials:
     ```json
     {
       "email": "admin@gastrotech.com",
       "password": "admin123"
     }
     ```
   - Click "Execute"
   - Copy the `access` token from the response (without quotes)

2. **Authorize Swagger**

   - Click the **"Authorize"** button (🔓) at the top right of Swagger UI
   - In the "BearerAuth" field, paste your access token
   - Do **NOT** include "Bearer " prefix - Swagger adds it automatically
   - Click "Authorize" and then "Close"

3. **Test protected endpoints**

   You can now test admin endpoints like:
   - `GET /api/v1/admin/stats/` - Dashboard statistics
   - `GET /api/v1/admin/products/` - List products
   - `POST /api/v1/admin/media/upload/` - Upload media

4. **Token expiry**

   - Access tokens expire after 30 minutes by default
   - Use `POST /api/v1/auth/refresh/` with your refresh token to get a new access token
   - Re-authorize in Swagger UI with the new token

**Note**: Public endpoints (marked with no lock icon 🔓) work without authentication.

### API Endpoints

#### Authentication & System

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/login` | Obtain JWT tokens | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | No |
| GET | `/api/v1/auth/me` | Current user info | Yes |
| GET | `/api/v1/health` | Health check | No |
| GET | `/api/v1/docs/` | Swagger UI | No |
| GET | `/api/v1/schema/` | OpenAPI schema | No |

#### Catalog Public APIs

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/nav` | Navigation structure (cached 5min) | No |
| GET | `/api/v1/categories/tree` | Category tree (cached 5min) | No |
| GET | `/api/v1/series` | Series list (filter: ?category=slug) | No |
| GET | `/api/v1/taxonomy/tree` | Taxonomy tree (require: ?series=slug) | No |
| GET | `/api/v1/spec-keys` | Specification keys | No |
| GET | `/api/v1/products` | Product list (cursor-paginated, filtered) | No |
| GET | `/api/v1/products/{slug}` | Product detail | No |
| GET | `/api/v1/media/{id}` | Media metadata | No |
| GET | `/api/v1/media/{id}/file` | Stream media file (cached 7 days) | No |
| GET | `/api/v1/catalog-assets` | PDF catalog downloads | No |
| GET | `/api/v1/variants/by-codes` | Lookup variants by model codes | No |
| POST | `/api/v1/inquiries` | Submit inquiry (single or multi-item) | No |
| POST | `/api/v1/quote/validate` | Validate quote items before submit | No |
| POST | `/api/v1/quote/compose` | Compose WhatsApp/email-ready quote | No |

#### Cart API (Anonymous & Authenticated)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/cart/token/` | Create anonymous cart token | No |
| GET | `/api/v1/cart/` | Get current cart | Token or JWT |
| POST | `/api/v1/cart/items/` | Add item to cart | Token or JWT |
| PATCH | `/api/v1/cart/items/{id}/` | Update item quantity | Token or JWT |
| DELETE | `/api/v1/cart/items/{id}/` | Remove item from cart | Token or JWT |
| DELETE | `/api/v1/cart/clear/` | Clear all cart items | Token or JWT |
| POST | `/api/v1/cart/merge/` | Merge anonymous cart into user cart | JWT required |

#### Admin APIs (requires admin/editor role)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/admin/stats` | Dashboard statistics | Yes (admin/editor) |
| POST | `/api/v1/admin/media/upload` | Upload media file | Yes (admin/editor) |
| POST | `/api/v1/admin/products/{id}/media/upload` | Upload product media | Yes (admin/editor) |
| PATCH | `/api/v1/admin/products/{id}/media/reorder` | Reorder product media | Yes (admin/editor) |
| DELETE | `/api/v1/admin/products/{id}/media/{pm_id}` | Delete product media | Yes (admin/editor) |
| GET | `/api/v1/admin/inquiries` | List inquiries with filters | Yes (admin/editor) |
| GET | `/api/v1/admin/inquiries/{id}` | Get inquiry detail | Yes (admin/editor) |
| PATCH | `/api/v1/admin/inquiries/{id}` | Update inquiry status/note | Yes (admin/editor) |

### Authentication

1. **Login to get tokens**

   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@example.com", "password": "yourpassword"}'
   ```

   Response:
   ```json
   {
     "access": "eyJ...",
     "refresh": "eyJ..."
   }
   ```

2. **Use the access token**

   ```bash
   curl http://localhost:8000/api/v1/auth/me \
     -H "Authorization: Bearer <access_token>"
   ```

3. **Refresh the access token**

   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh": "<refresh_token>"}'
   ```

### Testing Catalog Endpoints with curl

```bash
# Navigation structure (categories + series)
curl http://localhost:8000/api/v1/nav

# Category tree
curl http://localhost:8000/api/v1/categories/tree

# Series list (all)
curl http://localhost:8000/api/v1/series

# Series by category
curl "http://localhost:8000/api/v1/series?category=pisirme-uniteleri"

# Taxonomy tree for a series
curl "http://localhost:8000/api/v1/taxonomy/tree?series=600"

# Spec keys
curl http://localhost:8000/api/v1/spec-keys

# Products list (active only, paginated)
curl http://localhost:8000/api/v1/products

# Products with filters
curl "http://localhost:8000/api/v1/products?series=600&sort=featured"

# Products search
curl "http://localhost:8000/api/v1/products?search=GKO"

# Product detail
curl http://localhost:8000/api/v1/products/600-serisi-gazli-ocaklar

# Media metadata (replace {id} with actual UUID)
curl http://localhost:8000/api/v1/media/{id}

# Media file with ETag caching
curl -i http://localhost:8000/api/v1/media/{id}/file

# Test 304 response with If-None-Match
curl -i -H "If-None-Match: \"<checksum>\"" http://localhost:8000/api/v1/media/{id}/file

# Catalog assets (PDF downloads)
curl http://localhost:8000/api/v1/catalog-assets
```

### Submitting an Inquiry (Teklif İste)

```bash
# Basic inquiry
curl -X POST http://localhost:8000/api/v1/inquiries \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Ahmet Yılmaz",
    "email": "ahmet@company.com",
    "phone": "+90 555 123 4567",
    "company": "ABC Restaurant",
    "message": "We need 5 units of GKO6010"
  }'

# Inquiry with product reference (single item)
curl -X POST http://localhost:8000/api/v1/inquiries \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Mehmet Kaya",
    "email": "mehmet@hotel.com",
    "product_slug": "600-serisi-gazli-ocaklar",
    "model_code": "GKO6010",
    "source_url": "https://gastrotech.com/products/600-serisi-gazli-ocaklar",
    "utm_source": "google",
    "utm_medium": "cpc"
  }'

# Multi-item quote request
curl -X POST http://localhost:8000/api/v1/inquiries \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Ali Yıldız",
    "email": "ali@restaurant.com",
    "company": "Grand Restaurant",
    "message": "Need quote for new kitchen equipment",
    "items": [
      {"model_code": "GKO6010", "qty": 2},
      {"model_code": "GKO6020", "qty": 1},
      {"model_code": "EFR6010", "qty": 3}
    ]
  }'

# Validate items before submitting quote
curl -X POST http://localhost:8000/api/v1/quote/validate \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"model_code": "GKO6010", "qty": 2},
      {"model_code": "INVALID123", "qty": 1}
    ]
  }'
```

### Uploading Media via Admin API (JWT)

```bash
# 1. Get JWT token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@gastrotech.com", "password": "yourpassword"}' \
  | jq -r '.access')

# 2. Upload a media file
curl -X POST http://localhost:8000/api/v1/admin/media/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@./product-image.jpg"

# 3. Upload media directly to a product
curl -X POST http://localhost:8000/api/v1/admin/products/{product-uuid}/media/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@./product-image.jpg" \
  -F "alt=Product main image" \
  -F "is_primary=true"

# 4. Reorder product media
curl -X PATCH http://localhost:8000/api/v1/admin/products/{product-uuid}/media/reorder \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"product_media_id": "uuid1", "sort_order": 10, "is_primary": true},
      {"product_media_id": "uuid2", "sort_order": 20}
    ]
  }'
```

### Uploading Media via Django Admin

1. Go to http://localhost:8000/admin/catalog/media/
2. Click "Add media"
3. Choose a file in the "Upload" field
4. The system automatically detects:
   - Content type (image/PDF/video)
   - Image dimensions
   - File size and checksum
5. Click "Save"

To attach media to a product:
1. Go to http://localhost:8000/admin/catalog/product/
2. Edit a product
3. Scroll to "Product media" section
4. Select media, set alt text, sort order, and primary flag
5. Use actions: "Set first image as primary" or "Normalize sort_order"

### Generating Product Groups from Taxonomy Leaf Nodes

To quickly create Product groups for taxonomy leaf nodes (e.g., all sub-categories under "Ocaklar"):

1. Go to http://localhost:8000/admin/catalog/taxonomynode/
2. Select the leaf nodes you want to generate products for
3. Choose action "Generate Product group pages for selected leaf nodes"
4. Click "Go"

The system will:
- Skip non-leaf nodes (nodes with children)
- Skip nodes that already have products
- Create products with appropriate slugs (e.g., "600-serisi-gazli-ocaklar")
- Add ProductNode relationships for the node and its ancestors
- Apply SpecTemplate if one matches the series/parent

You can also use the seed command:

```bash
# Using the original command
docker compose exec web python manage.py seed_demo_catalog --generate-leaf-products

# Or using the alias
docker compose exec web python manage.py seed_gastrotech_ia --generate-leaf-products
```

### Looking Up Variants by Model Codes

```bash
# Lookup multiple variants by model codes (preserves input order)
curl "http://localhost:8000/api/v1/variants/by-codes?codes=GKO6010,GKO6020,INVALID123"
```

Response includes full hierarchy info:
```json
[
  {
    "model_code": "GKO6010",
    "name_tr": "Gazlı Ocak 2 Gözlü",
    "product_slug": "600-serisi-gazli-ocaklar",
    "series_slug": "600",
    "category_slug": "pisirme-uniteleri",
    "dimensions": "400x600x280",
    "specs": {"goz-adedi": 2, "guc-kw": "8.0"},
    "error": null
  },
  {
    "model_code": "INVALID123",
    "error": "not_found"
  }
]
```

### Admin Inquiry Management (JWT)

```bash
# Get JWT token first
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@gastrotech.com", "password": "yourpassword"}' \
  | jq -r '.access')

# List inquiries
curl http://localhost:8000/api/v1/admin/inquiries \
  -H "Authorization: Bearer $TOKEN"

# Filter by status
curl "http://localhost:8000/api/v1/admin/inquiries?status=new&page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# Get inquiry detail
curl http://localhost:8000/api/v1/admin/inquiries/{inquiry-uuid} \
  -H "Authorization: Bearer $TOKEN"

# Update inquiry status
curl -X PATCH http://localhost:8000/api/v1/admin/inquiries/{inquiry-uuid} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "internal_note": "Called customer, waiting for response"
  }'
```

### Dashboard Statistics (JWT)

```bash
# Get dashboard stats
curl http://localhost:8000/api/v1/admin/stats \
  -H "Authorization: Bearer $TOKEN"

# Returns:
# {
#   "new_inquiries_count": 5,
#   "total_products": 42,
#   "total_variants": 156
# }
```

### Cart API Usage (X-Cart-Token)

The Cart API supports both anonymous users (via token) and authenticated users (via JWT).

#### Anonymous Cart Flow

```bash
# 1. Create a new anonymous cart and get token
curl -X POST http://localhost:8000/api/v1/cart/token/

# Response:
# {
#   "cart_token": "550e8400-e29b-41d4-a716-446655440000",
#   "cart": { "id": "...", "token": "...", "status": "open", "items": [], "totals": {...} }
# }

# 2. Get cart using the token
curl http://localhost:8000/api/v1/cart/ \
  -H "X-Cart-Token: 550e8400-e29b-41d4-a716-446655440000"

# 3. Add item to cart (replace variant_id with actual UUID)
curl -X POST http://localhost:8000/api/v1/cart/items/ \
  -H "X-Cart-Token: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{"variant_id": "VARIANT-UUID-HERE", "quantity": 2}'

# 4. Update item quantity (set to 0 to remove)
curl -X PATCH http://localhost:8000/api/v1/cart/items/ITEM-UUID/ \
  -H "X-Cart-Token: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{"quantity": 5}'

# 5. Remove item from cart
curl -X DELETE http://localhost:8000/api/v1/cart/items/ITEM-UUID/ \
  -H "X-Cart-Token: 550e8400-e29b-41d4-a716-446655440000"

# 6. Clear entire cart
curl -X DELETE http://localhost:8000/api/v1/cart/clear/ \
  -H "X-Cart-Token: 550e8400-e29b-41d4-a716-446655440000"
```

#### Authenticated Cart Flow

```bash
# 1. Login to get JWT token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}' \
  | jq -r '.access')

# 2. Get user's cart (auto-created if not exists)
curl http://localhost:8000/api/v1/cart/ \
  -H "Authorization: Bearer $TOKEN"

# 3. Add item to user's cart
curl -X POST http://localhost:8000/api/v1/cart/items/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"variant_id": "VARIANT-UUID-HERE", "quantity": 1}'
```

#### Merging Anonymous Cart on Login

When a user logs in after shopping as anonymous, merge their anonymous cart:

```bash
# Merge anonymous cart into user's cart after login
curl -X POST http://localhost:8000/api/v1/cart/merge/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Cart-Token: 550e8400-e29b-41d4-a716-446655440000"

# Response:
# {
#   "merged_count": 3,
#   "skipped_count": 0,
#   "cart": { ... user's cart with merged items ... }
# }
```

#### Cart Response Structure

```json
{
  "id": "cart-uuid",
  "token": "550e8400-e29b-41d4-a716-446655440000",
  "status": "open",
  "currency": "TRY",
  "is_anonymous": true,
  "items": [
    {
      "id": "item-uuid",
      "variant": {
        "id": "variant-uuid",
        "model_code": "GKO6010",
        "name_tr": "Gazlı Ocak 2 Gözlü",
        "sku": null,
        "size": "",
        "color": "",
        "price": "1500.00",
        "currency": "TRY",
        "stock_qty": 10,
        "is_available": true,
        "product_name": "Gazlı Ocaklar",
        "product_slug": "600-serisi-gazli-ocaklar"
      },
      "quantity": 2,
      "unit_price_snapshot": "1500.00",
      "line_total": "3000.00"
    }
  ],
  "totals": {
    "subtotal": "3000.00",
    "item_count": 2,
    "line_count": 1,
    "currency": "TRY"
  }
}
```

#### Stock Validation

The cart API enforces stock limits:

```bash
# Trying to add more than available stock returns 400:
# {
#   "detail": "Only 3 units available for GKO6010",
#   "available_stock": 3
# }

# Adding out-of-stock items returns 400:
# {
#   "detail": "Variant GKO6010 is out of stock",
#   "available_stock": 0
# }
```

#### PowerShell Examples (Windows)

```powershell
# Create anonymous cart
$response = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/cart/token/"
$cartToken = $response.cart_token

# Add item to cart
$body = @{ variant_id = "VARIANT-UUID"; quantity = 2 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/cart/items/" `
  -Headers @{ "X-Cart-Token" = $cartToken } `
  -ContentType "application/json" `
  -Body $body

# Get cart
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/cart/" `
  -Headers @{ "X-Cart-Token" = $cartToken }
```

### Composing Quote Messages (WhatsApp/Email Ready)

```bash
# Compose a quote message with customer info and items
curl -X POST http://localhost:8000/api/v1/quote/compose \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Mehmet Kaya",
    "company": "Grand Hotel",
    "note": "Kurulum dahil mi?",
    "items": [
      {"model_code": "GKO6010", "qty": 2},
      {"model_code": "GKO6030", "qty": 1}
    ]
  }'
```

Response includes resolved items and a formatted Turkish message:
```json
{
  "items_resolved": [
    {
      "model_code": "GKO6010",
      "qty": 2,
      "name_tr": "Gazlı Ocak 2 Gözlü",
      "product_title_tr": "Gazlı Ocaklar",
      "series_slug": "600",
      "spec_row": [
        {"key": "goz-adedi", "label_tr": "Göz Adedi", "value": "2"}
      ]
    }
  ],
  "message_tr": "📋 Teklif Talebi\n\nMüşteri: Mehmet Kaya (Grand Hotel)\n\n📦 Ürünler:\n• 2x GKO6010 - Gazlı Ocak 2 Gözlü (600 Serisi) - Gazlı Ocaklar [400x600x280]\n• 1x GKO6030 - Gazlı Ocak 6 Gözlü (600 Serisi) - Gazlı Ocaklar [1200x600x280]\n\n📝 Not: Kurulum dahil mi?"
}
```

## Development

### Running without Docker

```bash
# 1. Prerequisites: Python 3.12+, PostgreSQL 16+, Redis 7+

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
.\venv\Scripts\activate    # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env: set DATABASE_URL to your local PostgreSQL, REDIS_URL to local Redis

# 5. Full setup (migrations + data + admin)
python manage.py setup_full

# 6. Run development server
python manage.py runserver
```

### Running Tests

```bash
# With Docker
docker compose exec web python manage.py test

# Without Docker
python manage.py test

# Run full database audit
python manage.py full_database_audit
```

### Management Commands Reference

| Command | Description |
|---------|-------------|
| `setup_full` | Complete one-command setup (categories, brands, products, images, specs, admin) |
| `setup_full --skip-images` | Setup without image upload (faster) |
| `setup_full --dry-run` | Preview what would be done |
| `setup_db` | Categories + catalog PDFs + admin user only |
| `seed_master_hierarchy` | Brands, series, logo groups |
| `upload_product_images` | Bulk image upload from Excel mapping |
| `seed_specs_from_data` | Sync SpecKeys from existing product data |
| `export_full_data` | Export ALL site data to JSON (22 sections, media included) |
| `export_full_data --skip-media-bytes` | Export metadata only (no binary) |
| `import_full_data` | Import full site data from JSON (idempotent) |
| `full_database_audit` | Run data consistency checks |
| `ensure_dev_admin` | Create/update dev admin user (dev mode only) |

## Production Deployment

### Using docker-compose.prod.yml

```bash
# 1. Create production .env
cp .env.example .env.prod
# Edit .env.prod with production values:
#   DJANGO_SECRET_KEY=<strong-random-key>
#   DJANGO_ALLOWED_HOSTS=gastrotech.com
#   POSTGRES_PASSWORD=<secure-password>
#   CORS_ALLOWED_ORIGINS=https://gastrotech.com

# 2. Start production stack
docker compose -f docker-compose.prod.yml up -d

# 3. First-time data setup
docker compose -f docker-compose.prod.yml exec web python manage.py setup_full

# 4. Create production admin user
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### Production Checklist

1. `DJANGO_SETTINGS_MODULE=config.settings.prod` (enforced in docker-compose.prod.yml)
2. Strong `DJANGO_SECRET_KEY` (generate with `python -c "..."`)
3. `DJANGO_DEBUG=0`
4. Proper `DJANGO_ALLOWED_HOSTS` with your domain
5. PostgreSQL with secure password
6. Redis with maxmemory policy
7. HTTPS via Nginx reverse proxy
8. `SECURE_SSL_REDIRECT=1`
9. Configure email settings for notifications
10. Set up Sentry for error tracking (optional)

### Security Notes

- WSGI/ASGI require explicit `DJANGO_SETTINGS_MODULE` - app will NOT start without it
- Cart tokens include IP binding for session security
- Cart operations use `select_for_update()` to prevent race conditions
- Search input limited to 200 characters to prevent abuse
- Blog content is HTML-sanitized (script, iframe, event handlers stripped)
- Honeypot protection on all public form endpoints
- Rate limiting: 60/min anonymous, 300/min authenticated

## User Roles

- **admin**: Full access to all features and admin panel
- **editor**: Limited access for content management

## Environment Variables

See `.env.example` for all available configuration options.

## License

Proprietary - Gastrotech

## Support

For support, contact the development team.
