import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware for URL redirects and fixes.
 *
 * NOTE: API proxying is handled by next.config.ts rewrites (not middleware)
 * because Next.js middleware runs in Edge sandbox which cannot resolve
 * Docker internal DNS hostnames (e.g., http://backend:8000).
 * Rewrites use Node.js runtime and work correctly with Docker networking.
 */
export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const normalizedPath =
    pathname.length > 1 && pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;

  // Debug log (only in development)
  if (process.env.NODE_ENV === "development") {
    console.log(`[Middleware] ${request.method} ${pathname}`);
  }

  // Legacy category redirect: /kategori/pisirme-ekipmanlari?subcategory=firinlar -> /kategori/firinlar
  if (normalizedPath === "/kategori/pisirme-ekipmanlari") {
    const subcategorySlug = request.nextUrl.searchParams.get("subcategory");
    if (subcategorySlug === "firinlar") {
      const url = request.nextUrl.clone();
      url.pathname = `/kategori/${subcategorySlug}`;
      url.searchParams.delete("subcategory");
      return NextResponse.redirect(url, 308);
    }
  }

  // Fix accidental double admin paths (e.g. /admin/admin/catalog/products)
  if (pathname.startsWith("/admin/admin")) {
    const url = request.nextUrl.clone();
    url.pathname = pathname.replace(/^\/admin\/admin/, "/admin");
    if (process.env.NODE_ENV === "development") {
      console.log(`[Middleware] Fixing double admin path: ${pathname} -> ${url.pathname}`);
    }
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

// Only match routes that need middleware processing
// API proxying is handled by next.config.ts rewrites
export const config = {
  matcher: [
    "/admin/admin/:path*",
    "/kategori/:path*"
  ],
};
