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

  // If running on client, strip backend absolute URLs (localhost) to use relative proxy path
  // This fixes images not loading on mobile/ngrok when backend returns absolute localhost URLs
  if (typeof window !== "undefined" && path.startsWith("http")) {
    const cleanPath = path.replace(/^http:\/\/(localhost|127\.0\.0\.1):8000/, "");
    // Only use the clean path if we actually stripped the domain (it implies it was a backend URL)
    // and the result is a path starting with /
    if (cleanPath !== path && cleanPath.startsWith("/")) {
      return cleanPath;
    }
  }

  if (path.startsWith("http")) return path;

  // For relative paths, prepend base url (which is empty on client, absolute on server)
  // This logic relies on endpoints.ts or env vars setting the base correctly
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "";
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
