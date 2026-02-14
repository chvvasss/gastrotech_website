import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const DJANGO_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * Middleware to proxy API requests to Django
 * This bypasses Next.js rewrites which strip trailing slashes
 * Django requires trailing slashes on all endpoints
 */
export async function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
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

  // Only process /api/* requests for Django proxy
  if (pathname.startsWith("/api/")) {
    if (process.env.NODE_ENV === "development") {
      console.log(`[Middleware] Proxying to Django: ${pathname}`);
    }
    // Ensure trailing slash for Django for all endpoints (including /file), except static files with extensions
    let djangoPath = pathname;
    if (!djangoPath.endsWith("/") && !djangoPath.includes(".")) {
      djangoPath = `${djangoPath}/`;
    }

    const djangoUrl = `${DJANGO_URL}${djangoPath}${search}`;

    // Get request body for non-GET requests
    let body: string | undefined;
    if (request.method !== "GET" && request.method !== "HEAD") {
      try {
        body = await request.text();
      } catch {
        body = undefined;
      }
    }

    // Forward headers (excluding host)
    const headers: Record<string, string> = {};
    request.headers.forEach((value, key) => {
      if (key.toLowerCase() !== "host") {
        headers[key] = value;
      }
    });

    try {
      const response = await fetch(djangoUrl, {
        method: request.method,
        headers: headers,
        body: body,
      });

      // Get response body
      // Using streaming response below

      // Create response with Django's response
      const responseHeaders = new Headers();
      response.headers.forEach((value, key) => {
        // Skip headers that Next.js manages
        if (!["transfer-encoding", "connection", "content-length", "content-encoding"].includes(key.toLowerCase())) {
          responseHeaders.set(key, value);
        }
      });

      return new NextResponse(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
      });
    } catch (error) {
      console.error("Django proxy error:", error);
      return NextResponse.json(
        { error: "Backend unavailable" },
        { status: 502 }
      );
    }
  }

  return NextResponse.next();
}

// Run middleware on API routes AND double admin paths
export const config = {
  matcher: [
    "/api/:path*",
    "/admin/admin/:path*",
    "/kategori/:path*"
  ],
};
