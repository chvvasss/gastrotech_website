/**
 * Central API endpoint definitions for Gastrotech Public Site.
 * 
 * All backend routes are defined here for easy maintenance.
 * Change these values if backend routes change.
 * 
 * NOTE: We use absolute URLs to the backend for both SSR and client-side.
 * CORS is configured on the backend to allow requests from frontend origins.
 * This is more reliable than Next.js rewrites which can cause redirect issues.
 */

// Use absolute URL for SSR, relative URL for client-side to leverage middleware proxy
const isServer = typeof window === "undefined";
const API_BASE = isServer
  ? (process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000")
  : "";

export const ENDPOINTS = {
  // Navigation
  NAV: `${API_BASE}/api/v1/nav/`,

  // Categories
  CATEGORIES: `${API_BASE}/api/v1/categories`,
  CATEGORIES_TREE: `${API_BASE}/api/v1/categories/tree/`,
  categoryDetail: (slug: string) => `${API_BASE}/api/v1/categories/${slug}/`,

  // Series
  SERIES: `${API_BASE}/api/v1/series/`,
  seriesByCategory: (
    categorySlug: string,
    brandSlug?: string,
    includeDescendants?: boolean
  ) => {
    const params = new URLSearchParams();
    params.set("category", categorySlug);
    if (brandSlug) params.set("brand", brandSlug);
    if (includeDescendants === true) params.set("include_descendants", "true");
    return `${API_BASE}/api/v1/series/?${params.toString()}`;
  },

  // Brands
  BRANDS: `${API_BASE}/api/v1/brands/`,

  // Taxonomy
  taxonomyTree: (seriesSlug: string) =>
    `${API_BASE}/api/v1/taxonomy/tree/?series=${seriesSlug}`,

  // Products
  PRODUCTS: `${API_BASE}/api/v1/products/`,
  productDetail: (slug: string) =>
    `${API_BASE}/api/v1/products/${slug}/`,
  productsSearch: (params: ProductSearchParams) => {
    const searchParams = new URLSearchParams();
    if (params.series) searchParams.set("series", params.series);
    if (params.node) searchParams.set("node", params.node);
    if (params.category) searchParams.set("category", params.category);
    if (params.brand) searchParams.set("brand", params.brand);
    if (params.include_descendants === true) {
      searchParams.set("include_descendants", "true");
    }
    if (params.search) searchParams.set("search", params.search);
    if (params.cursor) searchParams.set("cursor", params.cursor);
    if (params.page_size) searchParams.set("page_size", params.page_size.toString());
    if (params.sort) searchParams.set("sort", params.sort);
    return `${API_BASE}/api/v1/products/?${searchParams.toString()}`;
  },

  // Spec Keys
  SPEC_KEYS: `${API_BASE}/api/v1/spec-keys/`,

  // Media
  mediaFile: (id: string) => `${API_BASE}/api/v1/media/${id}/file/`,

  // Common
  COMMON_CONFIG: `${API_BASE}/api/v1/common/config/`,

  // Catalog Assets
  CATALOG_ASSETS: `${API_BASE}/api/v1/catalog-assets/`,

  // Category Catalogs (catalog mode)
  CATEGORY_CATALOGS: `${API_BASE}/api/v1/category-catalogs/`,
  categoryCatalogs: (slug: string) =>
    `${API_BASE}/api/v1/category-catalogs/?category=${slug}`,

  // Variant Lookup
  variantsByCodes: (codes: string[]) =>
    `${API_BASE}/api/v1/variants/by-codes/?codes=${codes.join(",")}`,

  // Cart
  CART_TOKEN: `${API_BASE}/api/v1/cart/token/`,
  CART: `${API_BASE}/api/v1/cart/`,
  CART_ITEMS: `${API_BASE}/api/v1/cart/items/`,
  cartItemDetail: (itemId: string) =>
    `${API_BASE}/api/v1/cart/items/${itemId}/`,
  CART_CLEAR: `${API_BASE}/api/v1/cart/clear/`,
  CART_MERGE: `${API_BASE}/api/v1/cart/merge/`,

  // Inquiries
  INQUIRIES: `${API_BASE}/api/v1/inquiries/`,
  QUOTE_VALIDATE: `${API_BASE}/api/v1/quote/validate/`,
  QUOTE_COMPOSE: `${API_BASE}/api/v1/quote/compose/`,

  // Blog
  BLOG: `${API_BASE}/api/v1/blog/`,
  BLOG_DETAIL: (slug: string) => `${API_BASE}/api/v1/blog/${slug}/`,
  BLOG_CATEGORIES: `${API_BASE}/api/v1/blog/categories/`,
  BLOG_FEATURED: `${API_BASE}/api/v1/blog/featured/`,
} as const;

export interface ProductSearchParams {
  series?: string;
  node?: string;
  category?: string;
  brand?: string;
  include_descendants?: boolean;
  search?: string;
  cursor?: string;
  page_size?: number;
  sort?: "newest" | "featured" | "title_asc";
}

// PLP (Product Listing Page) endpoint parameters
export interface PLPSearchParams {
  category: string;
  brands?: string[];
  categories?: string[]; // Subcategory filtering
  series?: string[];
  attrs?: string; // format: "key:value,key2:value2"
  price_min?: number;
  price_max?: number;
  in_stock?: boolean;
  sort?: "name_asc" | "name_desc" | "price_asc" | "price_desc" | "newest";
  page?: number;
  page_size?: number;
}

// Build PLP URL
export function plpSearch(params: PLPSearchParams): string {
  const searchParams = new URLSearchParams();
  searchParams.set("category", params.category);
  if (params.brands && params.brands.length > 0) {
    searchParams.set("brands", params.brands.join(","));
  }
  if (params.categories && params.categories.length > 0) {
    searchParams.set("categories", params.categories.join(","));
  }
  if (params.series && params.series.length > 0) {
    searchParams.set("series", params.series.join(","));
  }
  if (params.attrs) {
    searchParams.set("attrs", params.attrs);
  }
  if (params.price_min !== undefined) {
    searchParams.set("price_min", params.price_min.toString());
  }
  if (params.price_max !== undefined) {
    searchParams.set("price_max", params.price_max.toString());
  }
  if (params.in_stock) {
    searchParams.set("in_stock", "true");
  }
  if (params.sort) {
    searchParams.set("sort", params.sort);
  }
  if (params.page && params.page > 1) {
    searchParams.set("page", params.page.toString());
  }
  if (params.page_size) {
    searchParams.set("page_size", params.page_size.toString());
  }
  return `${API_BASE}/api/v1/plp/?${searchParams.toString()}`;
}
