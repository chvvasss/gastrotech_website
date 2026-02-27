import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware - ONLY handles redirects and path fixes.
 *
 * API proxy is handled by rewrites in next.config.ts (Node.js runtime)
 * because Edge Runtime cannot resolve Docker-internal DNS like "backend:8000".
 */
export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Legacy category redirect: /kategori/pisirme-ekipmanlari?subcategory=firinlar -> /kategori/firinlar
  const normalizedPath =
    pathname.length > 1 && pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;

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
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/admin/admin/:path*",
    "/kategori/:path*",
  ],
};
