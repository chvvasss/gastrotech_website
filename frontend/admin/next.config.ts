import type { NextConfig } from "next";

const DJANGO_URL = process.env.DJANGO_URL || "http://backend:8000";

// Security headers for admin panel (stricter than public)
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
  // Enable React strict mode for better development experience
  reactStrictMode: true,

  // Disable source maps in production for security
  productionBrowserSourceMaps: false,

  // Enable standalone output for Docker
  output: "standalone",

  // CRITICAL: Prevent Next.js from stripping trailing slashes
  // Without this, POST requests to /api/v1/auth/login/ become /api/v1/auth/login
  // which causes Django 404 (APPEND_SLASH=False) or RuntimeError (APPEND_SLASH=True)
  skipTrailingSlashRedirect: true,

  experimental: {
    serverActions: {
      bodySizeLimit: '50mb',
    },
  },

  // =====================
  // GATEWAY ROUTING: Admin /admin altında çalışacak
  // Gateway (PUBLIC 3001) üzerinden /admin/* istekleri buraya yönlendirilir
  // basePath otomatik olarak asset'leri de /admin altına alır
  // assetPrefix gerekmez - basePath yeterli
  // =====================
  basePath: "/admin",

  // Ngrok için gerekli image domain'leri
  images: {
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
        pathname: "/**",
      },
    ],
  },

  // API Proxy - Admin kendi başına Django'ya bağlanır
  // basePath ile çalışırken, kaynak path'ler basePath SONRASI path'lerdir
  // Yani /admin/api/v1/... isteği için source: "/api/:path*" yazılır
  async rewrites() {
    return [
      // Django API proxy
      // IMPORTANT: Trailing slash in destination ensures Django receives
      // correct URLs (all Django URL patterns require trailing slashes).
      // Next.js rewrites strip trailing slashes from :path*, so we
      // explicitly add it back in the destination.
      {
        source: "/api/:path*",
        destination: `${DJANGO_URL}/api/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        // Apply security headers to all admin routes
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;

