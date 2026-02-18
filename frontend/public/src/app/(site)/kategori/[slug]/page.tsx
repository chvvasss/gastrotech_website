/**
 * Category Page - Server Component with SEO Metadata
 * 
 * This page uses the new Product Listing Page (PLP) architecture
 * with faceted filtering, brand bar, and pagination.
 * 
 * Routes:
 * - /kategori/[slug] → PLP with filters
 * - /kategori/[slug]?brands=vital&sort=price_asc → Filtered PLP
 * 
 * SEO:
 * - generateMetadata fetches category for title/description
 * - Canonical URL points to unfiltered category page
 * - Filtered pages include noindex to prevent index bloat
 */

import { Metadata } from "next";
import { notFound } from "next/navigation";
import { PLPClient, PLPLoadingSkeleton } from "./plp-client";

// Revalidate every 5 minutes for category data
export const revalidate = 300;

// Site base URL for canonical
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://gastrotech.com.tr";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// =============================================================================
// Type Definitions
// =============================================================================

type Props = {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
};

interface CategoryResponse {
  id: string;
  name: string;
  slug: string;
  description_short?: string;
  cover_media_url?: string;
  breadcrumbs?: Array<{ name: string; slug: string }>;
}

// =============================================================================
// Data Fetching
// =============================================================================

async function fetchCategoryData(slug: string): Promise<CategoryResponse | null> {
  try {
    // Fetch minimal category data for metadata
    const response = await fetch(`${API_BASE}/api/v1/plp/?category=${slug}&page_size=1`, {
      next: { revalidate: 300 },
    });

    if (!response.ok) {
      if (response.status === 404) return null;
      return null;
    }

    const data = await response.json();
    return data.category || null;
  } catch {
    return null;
  }
}

// =============================================================================
// SEO Metadata
// =============================================================================

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { slug } = await params;
  const search = await searchParams;

  const category = await fetchCategoryData(slug);

  if (!category) {
    return {
      title: "Kategori Bulunamadı | Gastrotech",
      robots: { index: false, follow: false },
    };
  }

  // Check if there are any filter params
  const hasFilters = !!(
    search.brands ||
    search.price_min ||
    search.price_max ||
    search.in_stock ||
    search.sort ||
    (search.page && search.page !== "1")
  );

  // Build breadcrumb path for title
  const breadcrumbPath = category.breadcrumbs?.map(b => b.name).join(" > ") || category.name;

  // Build canonical URL (always unfiltered base category)
  const canonicalUrl = `${SITE_URL}/kategori/${slug}`;

  return {
    title: `${category.name} | Gastrotech Endüstriyel Mutfak`,
    description: category.description_short ||
      `${category.name} kategorisindeki profesyonel mutfak ekipmanları. Gastrotech kalitesiyle endüstriyel mutfak çözümleri.`,

    // Canonical always points to unfiltered page to avoid index bloat
    alternates: {
      canonical: canonicalUrl,
    },

    // Filtered pages should not be indexed (prevents duplicate content)
    robots: hasFilters
      ? { index: false, follow: true }
      : { index: true, follow: true },

    openGraph: {
      title: category.name,
      description: category.description_short || `${category.name} ürünleri`,
      url: canonicalUrl,
      siteName: "Gastrotech",
      locale: "tr_TR",
      type: "website",
      ...(category.cover_media_url && {
        images: [{
          url: `${API_BASE}${category.cover_media_url}`,
          width: 1200,
          height: 630,
          alt: category.name,
        }],
      }),
    },

    twitter: {
      card: "summary_large_image",
      title: category.name,
      description: category.description_short || `${category.name} ürünleri`,
    },
  };
}

// =============================================================================
// Page Component
// =============================================================================

export default async function CategoryPage({ params }: Props) {
  const { slug } = await params;

  // Fetch category to verify it exists
  const category = await fetchCategoryData(slug);

  if (!category) {
    notFound();
  }

  return (
    <PLPClient
      categorySlug={slug}
      categoryName={category.name}
      categoryDescription={category.description_short}
    />
  );
}
