# AGENTS.md - Gastrotech B2B Catalog System

## Project Overview
Production-grade B2B product catalog system with:
- **Backend**: Django 5.1 + Django REST Framework + PostgreSQL + Redis
- **Frontend (Public)**: Next.js 14 (App Router) + TypeScript + Tailwind CSS
- **Frontend (Admin)**: Next.js 14 (App Router) + TypeScript + Tailwind CSS

## Directory Structure
```
gastrotech.com_cursor/
├── backend/                    # Django backend
│   ├── apps/
│   │   ├── accounts/          # User authentication
│   │   ├── api/               # API routing
│   │   ├── blog/              # Blog management
│   │   ├── catalog/           # Core catalog (models, views, serializers)
│   │   ├── common/            # Shared utilities (slugify_tr, middleware)
│   │   ├── inquiries/         # Customer inquiries
│   │   ├── ops/               # Import operations
│   │   └── orders/            # Order management
│   ├── config/                # Django settings
│   └── manage.py
├── frontend/
│   ├── public/                # Public-facing Next.js app
│   └── admin/                 # Admin dashboard Next.js app
├── scripts/                   # Utility scripts
└── docs/                      # Documentation
```

## Environment Setup

### Backend (.env)
```bash
# Copy from .env.example or create:
DATABASE_URL=postgres://user:pass@localhost:5432/gastrotech
REDIS_URL=redis://localhost:6379/0
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
JWT_ACCESS_LIFETIME_MIN=30
JWT_REFRESH_LIFETIME_DAYS=7
MAX_MEDIA_UPLOAD_BYTES=10485760
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run development server
python manage.py runserver

# API available at: http://localhost:8000
# Admin panel: http://localhost:8000/admin/
# API docs: http://localhost:8000/api/schema/swagger-ui/
```

## Running the Frontend

### Public Site
```bash
cd frontend/public

# Install dependencies
npm install

# Run development server
npm run dev

# Available at: http://localhost:3000
```

### Admin Dashboard
```bash
cd frontend/admin

# Install dependencies
npm install

# Run development server
npm run dev -- --port 3001

# Available at: http://localhost:3001
```

## Running Tests

### Backend Tests
```bash
cd backend

# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.catalog.tests
python manage.py test apps.ops.tests

# Run with coverage
pip install coverage
coverage run --source='apps' manage.py test
coverage report -m
```

### Frontend Tests
```bash
cd frontend/public  # or frontend/admin

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

## Import System

### Validation (Dry-run)
```bash
# Via API
POST /api/admin/import-jobs/validate/
Content-Type: multipart/form-data
- file: <Excel or CSV file>
- mode: "strict" | "smart"
- kind: "catalog_import"

# Returns: ImportJob with validation report
```

### Commit (Execute)
```bash
# Via API
POST /api/admin/import-jobs/{job_id}/commit/
Content-Type: application/json
{
  "allow_partial": true  # Set true to commit valid rows even with errors
}
```

### Download Template
```bash
GET /api/admin/import-jobs/template/?fmt=xlsx&include_examples=true
```

### Import V5 Template Contract
Required columns for Products sheet:
- `Brand` (brand_slug)
- `Category` (category_slug)
- `Series` (series_slug)
- `Product Name` (name)
- `Product Slug` (slug)
- `Title TR` (title_tr)

Required columns for Variants sheet:
- `Product Slug` (product_slug)
- `Model Code` (model_code)

## Key Domain Rules

### Series Visibility
- Series with 0 products: Hidden from navigation (orphan)
- Series with 1 product: Product appears directly (no series step)
- Series with 2+ products: Visible as grouping

### Series Slug Uniqueness
- Series slugs are unique per category: `(category_id, slug)`
- Same slug can exist in different categories

### Import Modes
- **strict**: Fail on any missing reference (category, brand, series)
- **smart**: Create missing entities as candidates for approval

## Database Verification

### Check series distribution
```sql
SELECT
    CASE
        WHEN cnt = 0 THEN 'empty'
        WHEN cnt = 1 THEN 'singleton'
        ELSE 'multi-product'
    END as type,
    COUNT(*) as series_count
FROM (
    SELECT s.id, COUNT(p.id) as cnt
    FROM catalog_series s
    LEFT JOIN catalog_product p ON p.series_id = s.id AND p.status = 'active'
    GROUP BY s.id
) sub
GROUP BY type;
```

### Check unreachable products
```sql
SELECT COUNT(*) as unreachable_products
FROM catalog_product p
LEFT JOIN catalog_series s ON p.series_id = s.id
WHERE s.id IS NULL;
```

## Build & Deploy

### Backend Build
```bash
cd backend
python manage.py collectstatic --noinput
python manage.py migrate --noinput
```

### Frontend Build
```bash
cd frontend/public
npm run build

cd frontend/admin
npm run build
```

### Health Check
```
GET /api/health/
Response: {"status": "ok", "version": "x.x.x"}
```

## Security Notes

- Rate limiting: Configured in `config/settings/base.py`
- JWT blacklist: Enabled via `rest_framework_simplejwt.token_blacklist`
- Upload validation: Magic bytes + size limits in admin_api.py
- CORS: Configured per environment

## Dependency Auditing

```bash
# Backend
pip install pip-audit
pip-audit

# Frontend
cd frontend/public && npm audit
cd frontend/admin && npm audit
```

## Troubleshooting

### Import fails with "Category not found"
- Ensure category exists or use `mode=smart` to auto-create
- Check for typos in category slug

### Products not appearing
- Check `status = 'active'` for products
- Check series has `is_visible = True` (2+ products)

### Media not loading
- Check Media record exists with valid `bytes`
- Verify `content_type` is correct
- Check ETag/caching headers

### Request ID not in logs
- Ensure `RequestIDMiddleware` is first in MIDDLEWARE
- Check logging config includes `RequestIDFilter`
