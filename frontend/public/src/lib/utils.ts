import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: number | string | null | undefined, currency = "TRY"): string {
  if (price == null) return "—";
  const numPrice = typeof price === "string" ? parseFloat(price) : price;
  if (isNaN(numPrice)) return "—";

  return new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(numPrice);
}

// Backend base URL for image optimization.
// _next/image handler runs server-side and CAN reach backend:8000 in Docker.
// The browser never fetches this directly — it goes through /_next/image?url=...
const BACKEND_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://backend:8000";

export function getMediaUrl(path: string | null | undefined): string {
  if (!path) return "/placeholder.svg";

  // Already an absolute URL — use as-is (remotePatterns will validate)
  if (path.startsWith("http")) {
    return path;
  }

  // Relative API path (e.g. /api/v1/media/uuid/file/) — make absolute so
  // _next/image can fetch directly from backend without going through rewrites
  if (path.startsWith("/api/v1/media/")) {
    return `${BACKEND_BASE_URL}${path}`;
  }

  return path;
}

export function slugify(text: string): string {
  return text
    .toString()
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^\w\-]+/g, "")
    .replace(/\-\-+/g, "-")
    .replace(/^-+/, "")
    .replace(/-+$/, "");
}
