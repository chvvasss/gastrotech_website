import { http } from "./http";
import type { Variant } from "@/types/api";

// Types for admin variant operations
export interface CreateVariantPayload {
  product_slug: string; // Product slug (backend expects product_slug)
  model_code: string;
  name_tr: string;
  name_en?: string;
  dimensions?: string;
  weight_kg?: number;
  list_price?: number;
  specs?: Record<string, string | number | boolean>;
  stock_qty?: number;
}

export interface PatchVariantPayload {
  name_tr?: string;
  name_en?: string;
  dimensions?: string;
  weight_kg?: number | null;
  list_price?: number | null;
  price_override?: number | null;
  specs?: Record<string, string | number | boolean>;
  stock_qty?: number;
}

export interface BulkUpdateVariantItem {
  model_code: string;
  name_tr?: string;
  name_en?: string;
  dimensions?: string;
  weight_kg?: number | null;
  list_price?: number | null;
  specs?: Record<string, string | number | boolean>;
  stock_qty?: number;
}

export interface BulkUpdateResponse {
  updated: number;
  not_found: string[];
  errors: Array<{ model_code: string; error: string }>;
}

export interface AdminVariant extends Variant {
  id: string;
  product_slug: string;
  sku: string | null;
  price_override: number | null;
  size: string | null;
  color: string | null;
  stock_qty: number;
  created_at: string;
  updated_at: string;
}

export const adminVariantsApi = {
  /**
   * List variants with optional product filter
   */
  async listVariants(params?: {
    product?: string;
    search?: string;
  }): Promise<AdminVariant[]> {
    const queryParams = new URLSearchParams();
    if (params?.product) queryParams.set("product", params.product);
    if (params?.search) queryParams.set("search", params.search);

    // IMPORTANT: Trailing slash for DRF
    const url = `/admin/variants/${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    const response = await http.get<AdminVariant[]>(url);
    return response.data;
  },

  /**
   * Get variant by model_code
   */
  async getVariant(modelCode: string): Promise<AdminVariant> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.get<AdminVariant>(`/admin/variants/${encodeURIComponent(modelCode)}/`);
    return response.data;
  },

  /**
   * Create a new variant
   */
  async createVariant(payload: CreateVariantPayload): Promise<AdminVariant> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.post<AdminVariant>("/admin/variants/", payload);
    return response.data;
  },

  /**
   * Update variant (partial)
   */
  async patchVariant(modelCode: string, payload: PatchVariantPayload): Promise<AdminVariant> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.patch<AdminVariant>(
      `/admin/variants/${encodeURIComponent(modelCode)}/`,
      payload
    );
    return response.data;
  },

  /**
   * Delete variant
   */
  async deleteVariant(modelCode: string): Promise<void> {
    // IMPORTANT: Trailing slash for DRF
    await http.delete(`/admin/variants/${encodeURIComponent(modelCode)}/`);
  },

  /**
   * Bulk update variants by model_code
   */
  async bulkUpdate(updates: BulkUpdateVariantItem[]): Promise<BulkUpdateResponse> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.post<BulkUpdateResponse>("/admin/variants/bulk/", {
      updates,
    });
    return response.data;
  },
};
