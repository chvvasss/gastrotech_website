/**
 * Construct a full media URL for displaying images/files in the admin panel.
 *
 * On the client side, always uses relative paths so that Next.js rewrites
 * proxy requests to the Django backend. This avoids mixed-content and
 * localhost connection errors in production.
 *
 * On the server side, uses NEXT_PUBLIC_BACKEND_URL if available for
 * direct backend access (e.g. in Docker internal network).
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "";
const BASE_PATH = "/admin";

/**
 * Build a displayable URL for API media paths (e.g. /api/v1/media/{uuid}/file/).
 * Use this for any media URLs returned by the API.
 */
export function getMediaUrl(relativePath: string | null | undefined): string {
  if (!relativePath) return "";

  const isServer = typeof window === "undefined";

  // Client-side: strip any absolute backend URL to use relative proxy path
  if (!isServer && relativePath.startsWith("http")) {
    try {
      const url = new URL(relativePath);
      return `${BASE_PATH}${url.pathname}${url.search}`;
    } catch {
      // fall through
    }
  }

  // Client-side: always use relative paths through basePath rewrites
  if (!isServer) {
    if (relativePath.startsWith("/")) {
      return `${BASE_PATH}${relativePath}`;
    }
    return `${BASE_PATH}/${relativePath}`;
  }

  // Server-side: use absolute URL for direct backend access
  if (BACKEND_URL) {
    return `${BACKEND_URL}${relativePath}`;
  }
  return `${BASE_PATH}${relativePath}`;
}

/**
 * Build a displayable URL for Django /media/ paths (e.g. /media/info_sheets/qrcodes/xxx.png).
 * Use this for FileField/ImageField URLs that go through Django's MEDIA_URL.
 */
export function getDjangoMediaUrl(relativePath: string | null | undefined): string {
  if (!relativePath) return "";

  const isServer = typeof window === "undefined";

  // Client-side: strip any absolute backend URL to use relative proxy path
  if (!isServer && relativePath.startsWith("http")) {
    try {
      const url = new URL(relativePath);
      return `${BASE_PATH}${url.pathname}${url.search}`;
    } catch {
      // fall through
    }
  }

  // Client-side: always use relative paths through basePath rewrites
  if (!isServer) {
    if (relativePath.startsWith("/")) {
      return `${BASE_PATH}${relativePath}`;
    }
    return `${BASE_PATH}/${relativePath}`;
  }

  // Server-side: use absolute URL for direct backend access
  if (BACKEND_URL) {
    return `${BACKEND_URL}${relativePath}`;
  }
  return `${BASE_PATH}${relativePath}`;
}
