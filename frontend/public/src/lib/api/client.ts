import { ENDPOINTS, ProductSearchParams } from "./endpoints";
import {
  NavCategory,
  NavCategorySchema,
  Category,
  CategorySchema,
  CategoryCatalog,
  CategoryCatalogSchema,
  Series,
  SeriesSchema,
  TaxonomyNode,
  TaxonomyNodeSchema,
  ProductListResponse,
  ProductListResponseSchema,
  ProductDetail,
  ProductDetailSchema,
  CatalogAsset,
  CatalogAssetSchema,
  Cart,
  CartSchema,
  CartTokenResponse,
  CartTokenResponseSchema,
  InquiryCreate,
  InquiryResponse,
  InquiryResponseSchema,
  BlogCategory,
  BlogCategorySchema,
  BlogPostListItem,
  BlogPostListSchema,
  BlogPostDetail,
  BlogPostDetailSchema,
  BlogPostListResponse,
  BlogPostListResponseSchema,
} from "./schemas";
import { z } from "zod";

// ============================================================================
// HTTP Client
// ============================================================================

interface FetchOptions extends RequestInit {
  cartToken?: string;
}

// Debug mode for development
const DEBUG_API = process.env.NODE_ENV === "development";

async function fetchJSON<T>(url: string, options: FetchOptions = {}): Promise<T> {
  const { cartToken, ...fetchOptions } = options;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    // Ngrok browser warning bypass - required for external device access
    "ngrok-skip-browser-warning": "true",
    ...(fetchOptions.headers || {}),
  };

  if (cartToken) {
    (headers as Record<string, string>)["X-Cart-Token"] = cartToken;
  }

  // Debug logging
  if (DEBUG_API) {
    const isServer = typeof window === "undefined";
    console.log(`[API ${isServer ? "SSR" : "Client"}] ${fetchOptions.method || "GET"} ${url}`);
  }

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
    });

    if (!response.ok) {
      const errorBody = await response.text().catch(() => "");

      // Debug logging for errors
      if (DEBUG_API) {
        console.error(`[API Error] ${response.status} ${response.statusText} - ${url}`);
        if (errorBody) console.error(`[API Error Body]`, errorBody.substring(0, 500));
      }

      // Try to parse JSON error
      let parsedError = errorBody;
      try {
        const jsonError = JSON.parse(errorBody);
        if (jsonError.detail) {
          parsedError = jsonError.detail;
        } else if (jsonError.error) {
          parsedError = jsonError.error;
        }
      } catch {
        // Not JSON, use raw text
      }

      throw new ApiError(response.status, response.statusText, parsedError);
    }

    return response.json();
  } catch (error) {
    // Network errors
    if (DEBUG_API && !(error instanceof ApiError)) {
      console.error(`[API Network Error] ${url}`, error);
    }
    throw error;
  }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: string
  ) {
    super(`API Error: ${status} ${statusText}`);
    this.name = "ApiError";
  }

  get isNotFound() {
    return this.status === 404;
  }

  get isConflict() {
    return this.status === 409;
  }
}

// ============================================================================
// Helper: Extract array from paginated or direct array response
// ============================================================================

function createPaginatedOrArraySchema<T extends z.ZodTypeAny>(itemSchema: T) {
  return z.union([
    z.array(itemSchema),
    z.object({
      count: z.number().optional(),
      next: z.string().nullable().optional(),
      previous: z.string().nullable().optional(),
      results: z.array(itemSchema),
    }),
  ]);
}

function extractResults<T>(parsed: T[] | { results: T[] }): T[] {
  if (Array.isArray(parsed)) {
    return parsed;
  }
  return parsed.results;
}

// ============================================================================
// Navigation API
// ============================================================================

const NavResponseSchema = createPaginatedOrArraySchema(NavCategorySchema);

export async function fetchNav(): Promise<NavCategory[]> {
  const data = await fetchJSON<unknown>(ENDPOINTS.NAV);
  const parsed = NavResponseSchema.parse(data);
  return extractResults(parsed);
}

// ============================================================================
// Categories API
// ============================================================================

const CategoriesResponseSchema = createPaginatedOrArraySchema(CategorySchema);

export async function fetchCategoriesTree(): Promise<Category[]> {
  const data = await fetchJSON<unknown>(ENDPOINTS.CATEGORIES_TREE);
  const parsed = CategoriesResponseSchema.parse(data);
  return extractResults(parsed);
}

export async function fetchCategoryChildren(parentSlug: string): Promise<Category[]> {
  const data = await fetchJSON<unknown>(`${ENDPOINTS.CATEGORIES}/${parentSlug}/children/`);
  const parsed = CategoriesResponseSchema.parse(data);
  return extractResults(parsed);
}

// Import CategoryDetail types
import { CategoryDetail, CategoryDetailSchema } from "./schemas";
export { type CategoryDetail } from "./schemas";

export async function fetchCategoryDetail(slug: string): Promise<CategoryDetail> {
  const data = await fetchJSON<unknown>(ENDPOINTS.categoryDetail(slug));
  return CategoryDetailSchema.parse(data);
}


// ============================================================================
// Series API
// ============================================================================

const SeriesResponseSchema = createPaginatedOrArraySchema(SeriesSchema);

export async function fetchSeries(
  categorySlug?: string,
  brandSlug?: string,
  includeDescendants?: boolean
): Promise<Series[]> {
  const url = categorySlug
    ? ENDPOINTS.seriesByCategory(categorySlug, brandSlug, includeDescendants)
    : ENDPOINTS.SERIES;
  const data = await fetchJSON<unknown>(url);
  const parsed = SeriesResponseSchema.parse(data);
  return extractResults(parsed);
}

// ============================================================================
// Brands API
// ============================================================================

// ============================================================================
// Brands API
// ============================================================================

import { Brand } from "./schemas";
export { type Brand } from "./schemas";

export async function fetchBrands(
  seriesSlug?: string,
  categorySlug?: string,
  includeDescendants?: boolean
): Promise<Brand[]> {
  const params = new URLSearchParams();
  if (seriesSlug) params.append("series", seriesSlug);
  if (categorySlug) params.append("category", categorySlug);
  if (includeDescendants === true) params.append("include_descendants", "true");

  const queryString = params.toString();
  const url = queryString ? `${ENDPOINTS.BRANDS}?${queryString}` : ENDPOINTS.BRANDS;

  const data = await fetchJSON<Brand[]>(url);
  return data;
}

// ============================================================================
// Taxonomy API
// ============================================================================

const TaxonomyResponseSchema = createPaginatedOrArraySchema(TaxonomyNodeSchema);

export async function fetchTaxonomyTree(seriesSlug: string): Promise<TaxonomyNode[]> {
  const data = await fetchJSON<unknown>(ENDPOINTS.taxonomyTree(seriesSlug));
  const parsed = TaxonomyResponseSchema.parse(data);
  return extractResults(parsed);
}

// ============================================================================
// Products API
// ============================================================================

export async function fetchProducts(params: ProductSearchParams = {}): Promise<ProductListResponse> {
  const data = await fetchJSON<unknown>(ENDPOINTS.productsSearch(params));
  return ProductListResponseSchema.parse(data);
}

export async function fetchProductDetail(slug: string): Promise<ProductDetail> {
  const data = await fetchJSON<unknown>(ENDPOINTS.productDetail(slug), { cache: "no-store" });
  return ProductDetailSchema.parse(data);
}

// ============================================================================
// Catalog Assets API
// ============================================================================

export async function fetchCatalogAssets(): Promise<CatalogAsset[]> {
  const data = await fetchJSON<unknown[]>(ENDPOINTS.CATALOG_ASSETS);
  return z.array(CatalogAssetSchema).parse(data);
}

export async function fetchCategoryCatalogs(categorySlug: string): Promise<CategoryCatalog[]> {
  const data = await fetchJSON<unknown[]>(ENDPOINTS.categoryCatalogs(categorySlug));
  return z.array(CategoryCatalogSchema).parse(data);
}

export async function fetchAllCategoryCatalogs(): Promise<CategoryCatalog[]> {
  const data = await fetchJSON<unknown[]>(ENDPOINTS.CATEGORY_CATALOGS);
  return z.array(CategoryCatalogSchema).parse(data);
}

// ============================================================================
// Cart API
// ============================================================================

export async function createCartToken(): Promise<CartTokenResponse> {
  const data = await fetchJSON<unknown>(ENDPOINTS.CART_TOKEN, {
    method: "POST",
  });
  return CartTokenResponseSchema.parse(data);
}

export async function fetchCart(cartToken: string): Promise<Cart> {
  const data = await fetchJSON<unknown>(ENDPOINTS.CART, {
    cartToken,
  });
  return CartSchema.parse(data);
}

export async function addToCart(
  cartToken: string,
  variantId: string,
  quantity: number = 1
): Promise<Cart> {
  // Ensure variantId is a valid UUID string
  if (!variantId || variantId.length === 0) {
    throw new Error("Variant ID is required");
  }

  const data = await fetchJSON<unknown>(ENDPOINTS.CART_ITEMS, {
    method: "POST",
    cartToken,
    body: JSON.stringify({ variant_id: variantId, quantity }),
  });
  return CartSchema.parse(data);
}

export async function updateCartItem(
  cartToken: string,
  itemId: string,
  quantity: number
): Promise<Cart> {
  const data = await fetchJSON<unknown>(ENDPOINTS.cartItemDetail(itemId), {
    method: "PATCH",
    cartToken,
    body: JSON.stringify({ quantity }),
  });
  return CartSchema.parse(data);
}

export async function removeCartItem(
  cartToken: string,
  itemId: string
): Promise<Cart> {
  const data = await fetchJSON<unknown>(ENDPOINTS.cartItemDetail(itemId), {
    method: "DELETE",
    cartToken,
  });
  return CartSchema.parse(data);
}

export async function clearCart(cartToken: string): Promise<Cart> {
  const data = await fetchJSON<unknown>(ENDPOINTS.CART_CLEAR, {
    method: "DELETE",
    cartToken,
  });
  return CartSchema.parse(data);
}

// ============================================================================
// Inquiries API
// ============================================================================

export async function createInquiry(data: InquiryCreate): Promise<InquiryResponse> {
  const response = await fetchJSON<unknown>(ENDPOINTS.INQUIRIES, {
    method: "POST",
    body: JSON.stringify(data),
  });
  return InquiryResponseSchema.parse(response);
}

// ============================================================================
// Blog API
// ============================================================================

export interface BlogSearchParams {
  category?: string;
  tag?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export async function fetchBlogPosts(params: BlogSearchParams = {}): Promise<BlogPostListResponse> {
  const searchParams = new URLSearchParams();
  if (params.category) searchParams.set("category", params.category);
  if (params.tag) searchParams.set("tag", params.tag);
  if (params.search) searchParams.set("search", params.search);
  if (params.page) searchParams.set("page", params.page.toString());
  if (params.page_size) searchParams.set("page_size", params.page_size.toString());

  const data = await fetchJSON<unknown>(`${ENDPOINTS.BLOG}?${searchParams.toString()}`);

  // Handle paginated response structure for schema parsing
  const parsed = BlogPostListResponseSchema.parse(data);

  // Ensure we return a consistent structure even if union schema matched array
  if (Array.isArray(parsed)) {
    return { results: parsed };
  }
  return parsed as BlogPostListResponse;
}

export async function fetchBlogPost(slug: string): Promise<BlogPostDetail> {
  const data = await fetchJSON<unknown>(ENDPOINTS.BLOG_DETAIL(slug));
  return BlogPostDetailSchema.parse(data);
}

export async function fetchBlogCategories(): Promise<BlogCategory[]> {
  const data = await fetchJSON<unknown>(ENDPOINTS.BLOG_CATEGORIES);
  // Re-use logic for potentially paginated/array response if backend changes
  // But usually categories list is simple array or results array
  const schema = createPaginatedOrArraySchema(BlogCategorySchema);
  const parsed = schema.parse(data);
  return extractResults(parsed);
}

export async function fetchFeaturedPosts(): Promise<BlogPostListItem[]> {
  const data = await fetchJSON<unknown>(ENDPOINTS.BLOG_FEATURED);
  const schema = createPaginatedOrArraySchema(BlogPostListSchema);
  const parsed = schema.parse(data);
  return extractResults(parsed);
}

// ============================================================================
// PLP (Product Listing Page) API
// ============================================================================

import { PLPResponse, PLPResponseSchema } from "./schemas";
import { PLPSearchParams, plpSearch } from "./endpoints";

export async function fetchPLP(params: PLPSearchParams): Promise<PLPResponse> {
  const url = plpSearch(params);
  const data = await fetchJSON<unknown>(url);
  return PLPResponseSchema.parse(data);
}
