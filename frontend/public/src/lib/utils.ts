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

export function getMediaUrl(path: string | null | undefined): string {
  if (!path) return "/placeholder.svg";

  // If absolute URL, extract just the pathname so the request goes through
  // Next.js rewrites (which proxy /api/* to the Django backend).
  // This avoids hitting unreachable Docker-internal hostnames like
  // http://backend:8000 from the browser or from the Image Optimization API.
  if (path.startsWith("http")) {
    try {
      const url = new URL(path);
      return url.pathname + url.search;
    } catch {
      return path;
    }
  }

  // Relative paths are returned as-is; Next.js rewrites handle proxying
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
