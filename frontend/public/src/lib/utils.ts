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

  // Absolute URL from backend (e.g. http://backend:8000/api/v1/media/...)
  // Strip to relative so the browser fetches via Next.js rewrite proxy
  if (path.startsWith("http")) {
    try {
      const url = new URL(path);
      return url.pathname + url.search;
    } catch {
      return path;
    }
  }

  // Already relative (e.g. /api/v1/media/uuid/file/) — return as-is
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
