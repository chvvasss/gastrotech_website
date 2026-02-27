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

  const isServer = typeof window === "undefined";

  // Client-side: strip any absolute backend URL to use relative proxy path
  // This ensures images go through Next.js rewrites instead of hitting
  // unreachable Docker-internal hostnames like http://backend:8000
  if (!isServer && path.startsWith("http")) {
    try {
      const url = new URL(path);
      return url.pathname + url.search;
    } catch {
      return path;
    }
  }

  if (path.startsWith("http")) return path;

  // Server-side: prepend base URL for direct backend access (Docker internal)
  // Client-side: use relative URL so Next.js rewrites proxy to backend
  const base = isServer ? (process.env.NEXT_PUBLIC_API_BASE_URL || "") : "";
  return `${base}${path}`;
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
