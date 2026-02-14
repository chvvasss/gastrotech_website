import { http } from "./http";
import type {
  ProductListItem,
  ProductStatus,
  PaginatedResponse,
  Series,
  Category,
  CategoryWithCounts,
  CategoryDetail,
  DashboardStats,
} from "@/types/api";

export interface ProductsParams {
  page?: number;
  page_size?: number;
  status?: ProductStatus | "";
  series?: string;
  search?: string;
  ordering?: string;
}

export const catalogApi = {
  async listProducts(
    params: ProductsParams = {}
  ): Promise<PaginatedResponse<ProductListItem>> {
    const queryParams = new URLSearchParams();

    if (params.page) queryParams.set("page", params.page.toString());
    if (params.page_size)
      queryParams.set("page_size", params.page_size.toString());
    if (params.status) queryParams.set("status", params.status);
    if (params.series) queryParams.set("series", params.series);
    if (params.search) queryParams.set("search", params.search);
    if (params.ordering) queryParams.set("ordering", params.ordering);

    // IMPORTANT: Trailing slash for DRF
    const url = `/products/${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    const response = await http.get<PaginatedResponse<ProductListItem>>(url);
    return response.data;
  },

  async listSeries(): Promise<Series[]> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.get<Series[] | { results: Series[] }>("/series/");
    // Handle both array response and paginated response
    const data = response.data;
    if (Array.isArray(data)) {
      return data;
    }
    // If it's a paginated response, extract the results
    if (data && typeof data === "object" && "results" in data) {
      return data.results;
    }
    return [];
  },

  async listCategories(): Promise<Category[]> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.get<Category[] | { results: Category[] }>("/categories/");
    // Handle both array response and paginated response
    const data = response.data;
    if (Array.isArray(data)) {
      return data;
    }
    // If it's a paginated response, extract the results
    if (data && typeof data === "object" && "results" in data) {
      return data.results;
    }
    return [];
  },

  async listCategoriesWithCounts(params?: { search?: string }): Promise<CategoryWithCounts[]> {
    const queryParams = new URLSearchParams();
    queryParams.set("include_counts", "true");
    if (params?.search) queryParams.set("search", params.search);

    // IMPORTANT: Trailing slash for DRF
    const url = `/categories/?${queryParams.toString()}`;
    const response = await http.get<CategoryWithCounts[] | { results: CategoryWithCounts[] }>(url);

    // Handle both array response and paginated response
    const data = response.data;
    if (Array.isArray(data)) {
      return data;
    }
    // If it's a paginated response, extract the results
    if (data && typeof data === "object" && "results" in data) {
      return data.results;
    }
    return [];
  },

  async getCategoryDetail(slug: string, brand?: string): Promise<CategoryDetail> {
    const queryParams = new URLSearchParams();
    if (brand) queryParams.set("brand", brand);

    // IMPORTANT: Trailing slash for DRF
    const url = `/categories/${slug}/${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    const response = await http.get<CategoryDetail>(url);
    return response.data;
  },

  /**
   * Get dashboard stats with optional date range
   */
  async getStats(range: "7d" | "14d" | "30d" | "90d" = "30d"): Promise<DashboardStats> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.get<DashboardStats>(`/admin/stats/?range=${range}`);
    return response.data;
  },

  // Brands
  async listBrands(params?: { category?: string; is_active?: boolean }): Promise<any[]> {
    const queryParams = new URLSearchParams();
    if (params?.category) queryParams.set("category", params.category);
    if (params?.is_active !== undefined)
      queryParams.set("is_active", params.is_active.toString());

    const url = `/brands/${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    const response = await http.get<any[]>(url);
    return response.data;
  },

  async getBrand(slug: string): Promise<any> {
    const response = await http.get<any>(`/brands/${slug}/`);
    return response.data;
  },

  async updateBrandCategories(
    slug: string,
    categories: Array<{
      category: string;
      is_active: boolean;
      order: number;
    }>
  ): Promise<any> {
    const response = await http.put<any>(`/brands/${slug}/categories/`, {
      categories,
    });
    return response.data;
  },
};
