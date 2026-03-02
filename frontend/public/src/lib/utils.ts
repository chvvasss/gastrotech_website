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

  // If absolute URL, extract just the pathname
  if (path.startsWith("http")) {
    try {
      const url = new URL(path);
      path = url.pathname + url.search;
    } catch {
      return path;
    }
  }

  // Rewrite /api/v1/media/* to /media-proxy/* so Next.js Image Optimization
  // accepts it. The /_next/image handler rejects local /api/* URLs (400).
  // A dedicated rewrite rule maps /media-proxy/* back to the Django backend.
  if (path.startsWith("/api/v1/media/")) {
    return path.replace("/api/v1/media/", "/media-proxy/");
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
