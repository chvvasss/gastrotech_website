import { http } from "./http";
import type {
  ProductListItem,
  ProductDetail,
  ProductStatus,
  PaginatedResponse,
} from "@/types/api";

export interface ProductsParams {
  page?: number;
  page_size?: number;
  status?: ProductStatus;
  series?: string;
  category?: string;  // Category slug for filtering
  node?: string;
  search?: string;
  is_featured?: boolean;
  ordering?: string;
  cursor?: string;
}


export const productsApi = {
  /**
   * List products with filters and pagination
   */
  async listProducts(
    params: ProductsParams = {}
  ): Promise<PaginatedResponse<ProductListItem>> {
    const queryParams = new URLSearchParams();

    if (params.page) queryParams.set("page", params.page.toString());
    if (params.page_size) queryParams.set("page_size", params.page_size.toString());
    if (params.status) queryParams.set("status", params.status);
    if (params.series) queryParams.set("series", params.series);
    if (params.node) queryParams.set("node", params.node);
    if (params.search) queryParams.set("search", params.search);
    if (params.is_featured !== undefined) queryParams.set("is_featured", params.is_featured.toString());
    if (params.ordering) queryParams.set("ordering", params.ordering);
    if (params.cursor) queryParams.set("cursor", params.cursor);

    // IMPORTANT: Trailing slash for DRF
    const url = `/products/${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    const response = await http.get<PaginatedResponse<ProductListItem>>(url);
    return response.data;
  },

  /**
   * Get product detail by slug
   */
  async getProductDetail(slug: string): Promise<ProductDetail> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.get<ProductDetail>(`/products/${encodeURIComponent(slug)}/`);
    return response.data;
  },
  /**
   * Delete a product by slug
   */
  async deleteProduct(slug: string): Promise<void> {
    await http.delete(`/products/${encodeURIComponent(slug)}/`);
  },
};
