# Gastrotech Public Website

Modern, responsive public website for Gastrotech industrial kitchen equipment.

## 🔧 Recent Fixes (Problem Fix Sprint)

### ✅ A) CORS Fix - X-Cart-Token Header Allowed
**Problem**: Browser preflight blocked `/api/v1/cart/` requests because `x-cart-token` wasn't in `Access-Control-Allow-Headers`.

**Solution** (Backend):
- Added `x-cart-token` and `x-idempotency-key` to `CORS_ALLOW_HEADERS` in:
  - `config/settings/base.py`
  - `config/settings/dev.py`

```python
# config/settings/dev.py & base.py
from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = (
    *default_headers,
    "x-cart-token",
    "x-idempotency-key",
)
```

**Frontend**: Already using `X-Cart-Token` header (standardized).

### ✅ B) Cart Variant ID Fix
**Problem**: Frontend sent `model_code` but backend expects `variant_id` (UUID).

**Solution**:
- Backend: Added `id` field to `VariantSerializer` in `apps/catalog/serializers.py`
- Frontend: Updated `VariantSchema` to include `id: z.string()`
- Frontend: Changed all `AddToCartButton` to use `variant.id` instead of `variant.model_code`

### ✅ C) Next/Image Warning Fix
**Problem**: Logo images had width/height mismatch causing aspect ratio warnings.

**Solution**: Changed logo images in Header and Footer to use `fill` prop with container sizing:
```tsx
<Link href="/" className="relative h-8 w-[144px] lg:h-10 lg:w-[180px]">
  <Image src="/brand/logo.png" alt="Gastrotech" fill className="object-contain object-left" />
</Link>
```

### ✅ D) Mega Menu SSR-Safe & Collision Detection
**Problem**: Mega menu could cause layout shift and had SSR issues with `window` access.

**Solution**:
- Wrapped `window` access in `useEffect` for SSR safety
- Added viewport-aware positioning with `resize` listener
- Portal-based rendering prevents parent overflow issues

### ✅ E) Catalog Removed
- All "Katalog İndir" buttons removed from Header, Footer, Hero
- `/katalog` route deleted with redirect to `/urunler`

---

## 🎨 Design Enhancements

### Brand Red (#BE2328) Usage
- Active nav indicator bar
- Section title accent bars
- Footer top gradient line
- Footer section underlines
- Explorer step badges
- Featured chips & badges
- Focus rings

### Key UI Components
- **Hero**: Full-photo with dark overlay, "Teklif Al" + "Ürünleri Keşfet" CTAs
- **Explorer**: Category → Series → Taxonomy stepper with product preview
- **ProductCard**: "İncele" + "Sepete Ekle" buttons
- **Cart Flow**: Drawer + `/sepet` page → "Teklif Al"

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+ (for backend)

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

### Frontend Setup
```bash
cd frontend/public
npm install
cp env.example .env.local
# Edit .env.local if needed
npm run dev
```

Site: http://localhost:3001

---

## 📋 API Contract Verification

### Endpoints (All verified with trailing slashes)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/nav/` | GET | Navigation categories with series |
| `/api/v1/categories/tree/` | GET | Category hierarchy |
| `/api/v1/series/` | GET | Series list (filter: `?category=slug`) |
| `/api/v1/taxonomy/tree/` | GET | Taxonomy tree (requires `?series=slug`) |
| `/api/v1/products/` | GET | Product list (cursor pagination) |
| `/api/v1/products/<slug>/` | GET | Product detail with variants |
| `/api/v1/cart/token/` | POST | Create anonymous cart |
| `/api/v1/cart/` | GET | Get cart (header: `X-Cart-Token`) |
| `/api/v1/cart/items/` | POST | Add item (`variant_id`, `quantity`) |
| `/api/v1/cart/items/<id>/` | PATCH/DELETE | Update/remove item |
| `/api/v1/cart/clear/` | DELETE | Clear cart |
| `/api/v1/inquiries/` | POST | Create quote request |

### Header Standard
- **Cart Token**: `X-Cart-Token` (standardized, lowercase in CORS config: `x-cart-token`)
- **Idempotency**: `Idempotency-Key` for POST /items/ and /merge/

### Variant ID
- Backend returns `id` (UUID) in variant objects
- Frontend uses `variant.id` for cart operations (not `model_code`)

---

## 🏗️ Project Structure

```
src/
├── app/
│   ├── (site)/
│   │   ├── page.tsx           # Home
│   │   ├── urunler/           # Products
│   │   ├── kategori/[slug]/   # Category
│   │   ├── seri/[slug]/       # Series
│   │   ├── urun/[slug]/       # Product detail
│   │   ├── sepet/             # Cart page
│   │   ├── iletisim/          # Contact/Quote
│   │   └── teklif-basarili/   # Quote success
│   └── globals.css
├── components/
│   ├── layout/                # Header, Footer, MegaMenu
│   ├── catalog/               # ProductCard, CategoryGrid, Explorer
│   └── cart/                  # CartDrawer, AddToCartButton
├── lib/api/
│   ├── endpoints.ts           # Central endpoint definitions
│   ├── schemas.ts             # Zod validation
│   └── client.ts              # API functions
└── hooks/
    ├── use-cart.ts            # Cart state
    └── use-toast.ts           # Notifications
```

---

## ✅ Smoke Test Checklist

After running both backend and frontend:

- [ ] `/api/v1/nav/` returns categories (check Network tab)
- [ ] Products load on home page and `/urunler`
- [ ] Cart icon shows badge when items added
- [ ] "Sepete Ekle" on product detail works
- [ ] Cart drawer opens with items
- [ ] `/sepet` page shows cart contents
- [ ] "Teklif Al" form submits successfully
- [ ] No CORS errors in console
- [ ] No Next/Image warnings
- [ ] Mega menu doesn't cause layout shift
