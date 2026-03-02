// Custom image loader for Next.js <Image> component.
//
// Problem: _next/image rejects relative /api/* paths with 400 because the
//   internal self-fetch goes through rewrites to Docker-internal hostnames
//   that may not resolve correctly in the _next/image context.
//
// Solution: This loader converts /api/v1/media/* paths to absolute
//   http://backend:8000/... URLs and routes them through _next/image.
//   The _next/image handler runs SERVER-SIDE so it CAN reach backend:8000.
//   The browser only ever sees /_next/image?url=... (same-origin, no mixed content).
//
// For non-media paths (local assets like /placeholder.svg), the default
//   _next/image behavior is preserved.

const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://backend:8000";

interface ImageLoaderParams {
  src: string;
  width: number;
  quality?: number;
}

export default function gastrotechImageLoader({
  src,
  width,
  quality,
}: ImageLoaderParams): string {
  const q = quality || 75;

  // Backend media: convert to absolute URL for _next/image server-side fetch
  if (src.startsWith("/api/v1/media/")) {
    return `/_next/image?url=${encodeURIComponent(BACKEND_URL + src)}&w=${width}&q=${q}`;
  }

  // Everything else: standard _next/image with the path as-is
  return `/_next/image?url=${encodeURIComponent(src)}&w=${width}&q=${q}`;
}
