import type { NextConfig } from "next";

// Gateway URL'ler - Tek domain stratejisi için
const DJANGO_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://backend:8000";
const ADMIN_URL = process.env.ADMIN_INTERNAL_URL || "http://frontend-admin:3001";

// Security headers for all routes
const securityHeaders = [
  { key: "X-DNS-Prefetch-Control", value: "on" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
  { key: "X-XSS-Protection", value: "1; mode=block" },
  { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
];

const nextConfig: NextConfig = {
  // Force trailing slashes on all URLs - required for Django compatibility
  // Django URLs are defined with trailing slash (e.g., /api/v1/auth/login/)
  // Without this, Next.js rewrites strip the trailing slash causing 404
  trailingSlash: true,

  // Disable source maps in production for security
  productionBrowserSourceMaps: false,

  // Enable standalone output for Docker
  output: "standalone",

  images: {
    formats: ["image/avif", "image/webp"],
    minimumCacheTTL: 60 * 60 * 24 * 30,
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/api/v1/media/**",
      },
      {
        protocol: "http",
        hostname: "127.0.0.1",
        port: "8000",
        pathname: "/api/v1/media/**",
      },
      {
        protocol: "https",
        hostname: "api.gastrotech.com.tr",
        pathname: "/api/v1/media/**",
      },
      {
        protocol: "https",
        hostname: "*.ngrok-free.dev",
        pathname: "/api/v1/media/**",
      },
    ],
  },
  async rewrites() {
    return [
      // =====================
      // ADMIN PANEL PROXY
      // /admin/* -> ADMIN Next.js (3000)
      {
        source: "/admin",
        destination: `http://frontend-admin:3001/admin`,
      },
      {
        source: "/admin/:path*",
        destination: `http://frontend-admin:3001/admin/:path*`,
      },

      // =====================
      // DJANGO API PROXY
      // trailingSlash: true ensures URLs have trailing slashes for Django
      // Rewrites use Node.js runtime (not Edge sandbox) so Docker DNS works
      // =====================
      {
        source: "/api/:path*",
        destination: `http://backend:8000/api/:path*/`,
      },

      // =====================
      // DJANGO STATIC/MEDIA PROXY
      // /static/* ve /media/* -> Django (8000)
      // =====================
      {
        source: "/static/:path*",
        destination: `http://backend:8000/static/:path*`,
      },
      {
        source: "/media/:path*",
        destination: `http://backend:8000/media/:path*`,
      },
    ];
  },
  async redirects() {
    return [
      // Legacy "catalog" -> simple categories
      {
        source: "/katalog",
        destination: "/kategori",
        permanent: true,
      },
      {
        source: "/urunler/:slug",
        destination: "/kategori/:slug",
        permanent: true,
      },
      // 1. Specific case: If query has 'category', redirect to /kategori/[slug]
      // This preserves other params (brand, series) automatically in query string?
      // Next.js passes query params if they are NOT used in destination keys.
      // But :slug IS used.
      // We rely on Next.js default behavior (passing remaining params).
      {
        source: "/urunler",
        has: [
          {
            type: "query",
            key: "category",
            value: "(?<slug>.*)",
          },
        ],
        destination: "/kategori/:slug",
        permanent: true,
      },
      {
        source: "/products",
        has: [
          {
            type: "query",
            key: "category",
            value: "(?<slug>.*)",
          },
        ],
        destination: "/kategori/:slug",
        permanent: true,
      },
      // 2. Generic case: No category param -> redirect to Categories Listing
      {
        source: "/urunler",
        destination: "/kategori",
        permanent: true,
      },
      {
        source: "/products",
        destination: "/kategori",
        permanent: true,
      },
      {
        source: "/product",
        destination: "/kategori",
        permanent: true,
      },
      {
        source: "/catalog/products",
        destination: "/kategori",
        permanent: true,
      },
    ];
  },
  async headers() {
    return [
      {
        // Apply security headers to all routes
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
