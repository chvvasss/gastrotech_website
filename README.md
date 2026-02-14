# GastroTech Website

Endüstriyel mutfak ekipmanları B2B katalog ve e-ticaret platformu.

## Proje Yapısı

```
gastrotech_website/
├── backend/          # Django 5.1 REST API (port 8000)
├── frontend/
│   ├── public/       # Next.js herkese açık site (port 3000)
│   └── admin/        # Next.js admin paneli (port 3001, /admin altında)
├── docs/             # Proje dokümantasyonu
└── scripts/          # Yardımcı scriptler
```

## Gereksinimler

- **Python** 3.11+
- **Node.js** 18+ (npm dahil)
- **Git LFS** (katalog PDF'leri için)

## Kurulum (Sıfırdan)

### 1. Repo'yu klonla

```bash
git clone https://github.com/chvvasss/gastrotech_website.git
cd gastrotech_website
```

> Git LFS kurulu olmalı. PDF dosyaları otomatik indirilir.
> Kurulu değilse: https://git-lfs.github.com adresinden indir, sonra `git lfs pull` çalıştır.

### 2. Backend kurulumu

```bash
cd backend

# Sanal ortam oluştur ve aktive et
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Bağımlılıkları kur
pip install -r requirements.txt

# .env dosyasını oluştur
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux

# Veritabanını oluştur
python manage.py migrate

# Kategorileri, katalog PDF'lerini ve admin kullanıcıyı kur
python manage.py setup_db
```

Bu komut otomatik olarak:
- 8 ana kategoriyi oluşturur
- 14 katalog PDF'ini veritabanına yükler
- Kategorilere katalogları bağlar
- Admin kullanıcı oluşturur

> PDF yüklemesi ~1 dk sürebilir. Hızlı kurulum için `python manage.py setup_db --skip-pdfs`

### 3. Frontend (Public Site) kurulumu

```bash
cd frontend/public

# Bağımlılıkları kur
npm install

# .env dosyasını oluştur
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux

# Geliştirme sunucusunu başlat
npm run dev
```

### 4. Frontend (Admin Panel) kurulumu

```bash
cd frontend/admin

# Bağımlılıkları kur
npm install

# .env dosyasını oluştur
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux

# Geliştirme sunucusunu başlat
npm run dev
```

## Çalıştırma

3 terminal aç ve sırasıyla çalıştır:

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate
python manage.py runserver
```

**Terminal 2 - Public Site:**
```bash
cd frontend/public
npm run dev
```

**Terminal 3 - Admin Panel:**
```bash
cd frontend/admin
npm run dev
```

## Erişim Adresleri

| Servis | URL | Açıklama |
|--------|-----|----------|
| Public Site | http://localhost:3000 | Herkese açık katalog sitesi |
| Admin Panel | http://localhost:3000/admin | Yönetim paneli (gateway üzerinden) |
| Admin (direkt) | http://localhost:3001/admin | Admin panel direkt erişim |
| Django API | http://localhost:8000/api/v1/ | REST API |
| Django Admin | http://localhost:8000/admin/ | Django yerleşik admin |

## Giriş Bilgileri (Development)

| Kullanıcı | Şifre |
|-----------|-------|
| admin@gastrotech.com | admin123 |

## Ortam Değişkenleri

### Backend (.env)
```env
DJANGO_SECRET_KEY=change-me-in-production
DJANGO_DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

### Frontend Public (.env)
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
ADMIN_INTERNAL_URL=http://127.0.0.1:3001
```

### Frontend Admin (.env)
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
DJANGO_URL=http://127.0.0.1:8000
```

## Teknolojiler

- **Backend:** Django 5.1, Django REST Framework, SQLite (dev) / PostgreSQL (prod)
- **Frontend:** Next.js 15/16, React, TypeScript, Tailwind CSS
- **Medya:** PostgreSQL binary storage (Media modeli)
- **Auth:** JWT (SimpleJWT)
