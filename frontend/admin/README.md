# GastroTech Admin Panel

A premium B2B admin panel built with Next.js for managing the GastroTech product catalog and customer inquiries.

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS + shadcn/ui
- **State Management**: TanStack Query
- **Forms**: React Hook Form + Zod
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Drag & Drop**: dnd-kit (installed for future use)

## Getting Started

### Prerequisites

- Node.js 18+
- npm, pnpm, or yarn
- Django backend running on port 8000

### Installation

```bash
# Navigate to admin folder
cd frontend/admin

# Install dependencies
npm install

# Copy environment file
cp env.example .env.local

# Edit .env.local with your backend URL
# NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Start development server
npm run dev
```

The admin panel will be available at `http://localhost:3000`.

### Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (app)/             # Protected app routes
│   │   ├── dashboard/     # Dashboard page
│   │   ├── inquiries/     # Inquiries list & detail
│   │   ├── catalog/       # Product catalog
│   │   └── settings/      # Settings page
│   ├── login/             # Login page
│   └── layout.tsx         # Root layout
├── components/
│   ├── ui/                # shadcn/ui components
│   ├── layout/            # Layout components (AppShell, Sidebar, etc.)
│   └── data-table/        # Data table components
├── hooks/                 # React Query hooks
├── lib/
│   ├── api/               # API client layer
│   └── utils.ts           # Utility functions
└── types/                 # TypeScript types
```

## Features

### Authentication
- JWT-based authentication
- Automatic token refresh
- Protected routes with AuthGuard

### Inquiries Management
- List with filters (status, search)
- Detail view with customer info
- Quote message composer
- Status updates

### Product Catalog
- Product list with filters (status, series)
- Image previews
- Series filtering

### Design System
- Collapsible sidebar
- Breadcrumb navigation
- Responsive layout
- Toast notifications
- Loading skeletons

## Backend Integration

The admin panel expects these API endpoints:

### Auth
- `POST /api/v1/auth/login` - Login (returns JWT)
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user

### Inquiries (Admin)
- `GET /api/v1/admin/inquiries` - List inquiries
- `GET /api/v1/admin/inquiries/:id` - Get inquiry detail
- `PATCH /api/v1/admin/inquiries/:id` - Update inquiry

### Catalog (Public)
- `GET /api/v1/products` - List products
- `GET /api/v1/series` - List series
- `GET /api/v1/categories` - List categories

### Quote
- `POST /api/v1/quote/compose` - Compose quote message

## Configuration

Environment variables in `.env.local`:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## License

Proprietary - GastroTech B2B
