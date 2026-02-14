import { http } from "./http";
import type { ProductDetail, SpecTemplate, PaginatedResponse } from "@/types/api";

// Types for admin product operations
export interface CreateProductPayload {
  name?: string;
  title_tr: string;
  title_en?: string;
  series: string; // slug or UUID
  primary_node?: string; // slug or UUID
  status?: "draft" | "active" | "archived";
  is_featured?: boolean;
  general_features?: string[];
  notes?: string[];
  spec_layout?: string[];
  apply_template_id?: string; // Optional: apply template on create
  apply_template_overwrite?: boolean;
}

export interface PatchProductPayload {
  title_tr?: string;
  title_en?: string;
  status?: "draft" | "active" | "archived";
  is_featured?: boolean;
  general_features?: string[];
  notes?: string[];
  spec_layout?: string[];
  primary_node?: string | null;
  brand?: string | null;
  brand_slug?: string | null;
  pdf_ref?: string;
  long_description?: string;
  seo_title?: string;
  seo_description?: string;
}

export interface ApplyTemplatePayload {
  template_id: string;
  overwrite: boolean;
}

export interface ApplyTemplateResponse {
  updated_fields: string[];
  message: string;
}

export interface AdminProductListItem {
  id: string;
  name: string;
  slug: string;
  title_tr: string;
  title_en: string | null;
  series_slug: string;
  series_name: string;
  category_slug: string;
  category_name: string;
  primary_node_slug: string | null;
  brand_slug: string | null;
  brand_name: string | null;
  status: "draft" | "active" | "archived";
  is_featured: boolean;
  pdf_ref: string | null;
  variants_count: number;
  primary_image_url: string | null;
  created_at: string;
  updated_at: string;
}

// Bulk Brand Update Types
export interface BulkBrandUpdatePayload {
  product_ids?: string[];
  filters?: {
    series?: string;
    category?: string;
    status?: string;
    search?: string;
    brand?: string | "__null__";
  };
  brand_slug: string | null;
  dry_run: boolean;
}

export interface BulkBrandUpdateResponse {
  affected_count: number;
  products_preview?: Array<{
    id: string;
    slug: string;
    title_tr: string;
    current_brand: string | null;
    new_brand: string | null;
  }>;
  dry_run: boolean;
  message: string;
}

export const adminProductsApi = {
  /**
   * List products with filters
   */
  async listProducts(params?: {
    series?: string;
    category?: string;  // Category slug for filtering
    status?: string;
    search?: string;
    ordering?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<AdminProductListItem>> {
    const queryParams = new URLSearchParams();
    if (params?.series) queryParams.set("series", params.series);
    if (params?.category) queryParams.set("category", params.category);
    if (params?.status) queryParams.set("status", params.status);
    if (params?.search) queryParams.set("search", params.search);
    if (params?.ordering) queryParams.set("ordering", params.ordering);
    if (params?.page) queryParams.set("page", params.page.toString());
    if (params?.page_size) queryParams.set("page_size", params.page_size.toString());

    // IMPORTANT: Trailing slash for DRF
    const url = `/admin/products/${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    const response = await http.get<PaginatedResponse<AdminProductListItem>>(url);
    return response.data;
  },

  /**
   * Get product detail
   */
  async getProduct(slugOrId: string): Promise<ProductDetail> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.get<ProductDetail>(`/admin/products/${slugOrId}/`);
    return response.data;
  },

  /**
   * Create a new product
   */
  async createProduct(payload: CreateProductPayload): Promise<ProductDetail> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.post<ProductDetail>("/admin/products/", payload);
    return response.data;
  },

  /**
   * Update product (partial)
   */
  async patchProduct(slugOrId: string, payload: PatchProductPayload): Promise<ProductDetail> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.patch<ProductDetail>(`/admin/products/${slugOrId}/`, payload);
    return response.data;
  },

  /**
   * Delete product
   */
  async deleteProduct(slugOrId: string): Promise<void> {
    // IMPORTANT: Trailing slash for DRF
    await http.delete(`/admin/products/${slugOrId}/`);
  },

  /**
   * Apply spec template to product
   */
  async applyTemplate(
    slugOrId: string,
    payload: ApplyTemplatePayload
  ): Promise<ApplyTemplateResponse> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.post<ApplyTemplateResponse>(
      `/admin/products/${slugOrId}/apply-template/`,
      payload
    );
    return response.data;
  },

  /**
   * List spec templates
   */
  async listTemplates(seriesSlug?: string): Promise<SpecTemplate[]> {
    // IMPORTANT: Trailing slash for DRF
    const url = seriesSlug
      ? `/admin/spec-templates/?series=${encodeURIComponent(seriesSlug)}`
      : "/admin/spec-templates/";
    const response = await http.get<SpecTemplate[]>(url);
    return response.data;
  },

  /**
   * Bulk update brand for multiple products
   */
  async bulkUpdateBrand(payload: BulkBrandUpdatePayload): Promise<BulkBrandUpdateResponse> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.post<BulkBrandUpdateResponse>(
      "/admin/products/bulk-update-brand/",
      payload
    );
    return response.data;
  },
};
