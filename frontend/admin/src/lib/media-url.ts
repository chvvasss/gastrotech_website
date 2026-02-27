/**
 * Construct a full media URL for displaying images/files in the admin panel.
 *
 * Handles two modes:
 * - Direct mode (NEXT_PUBLIC_BACKEND_URL set): absolute URL to Django backend
 * - Gateway mode (NEXT_PUBLIC_BACKEND_URL empty): relative URL through basePath rewrites
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "";
const BASE_PATH = "/admin";

/**
 * Build a displayable URL for API media paths (e.g. /api/v1/media/{uuid}/file/).
 * Use this for any media URLs returned by the API.
 */
export function getMediaUrl(relativePath: string | null | undefined): string {
  if (!relativePath) return "";
  if (BACKEND_URL) {
    return `${BACKEND_URL}${relativePath}`;
  }
  // Gateway mode: prefix with basePath so Next.js rewrites can intercept
  return `${BASE_PATH}${relativePath}`;
}

/**
 * Build a displayable URL for Django /media/ paths (e.g. /media/info_sheets/qrcodes/xxx.png).
 * Use this for FileField/ImageField URLs that go through Django's MEDIA_URL.
 */
export function getDjangoMediaUrl(relativePath: string | null | undefined): string {
  if (!relativePath) return "";
  if (BACKEND_URL) {
    return `${BACKEND_URL}${relativePath}`;
  }
  // Gateway mode: prefix with basePath so Next.js rewrites can intercept
  return `${BASE_PATH}${relativePath}`;
}
