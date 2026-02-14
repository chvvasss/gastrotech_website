import { http } from "./http";

// =============================================================================
// Admin Brands API - Full CRUD operations
// =============================================================================

export interface AdminBrand {
    id: string;
    name: string;
    slug: string;
    logo_media: string | null;
    logo_media_url: string | null;
    description: string;
    website_url: string;
    is_active: boolean;
    order: number;
    products_count?: number;
    created_at: string;
    updated_at: string;
}

export interface CreateBrandPayload {
    name: string;
    slug?: string;
    logo_media?: string | null;
    description?: string;
    website_url?: string;
    is_active?: boolean;
    order?: number;
}

export interface UpdateBrandPayload extends Partial<CreateBrandPayload> { }

export const adminBrandsApi = {
    /**
     * List all brands
     */
    async list(params?: { is_active?: boolean }): Promise<AdminBrand[]> {
        const queryParams = new URLSearchParams();
        if (params?.is_active !== undefined) {
            queryParams.set("is_active", String(params.is_active));
        }
        const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
        const response = await http.get<AdminBrand[] | { results: AdminBrand[] }>(`/admin/brands/${query}`);
        const data = response.data;
        return Array.isArray(data) ? data : (data.results || []);
    },

    /**
     * Get single brand by slug
     */
    async get(slug: string): Promise<AdminBrand> {
        const response = await http.get<AdminBrand>(`/admin/brands/${slug}/`);
        return response.data;
    },

    /**
     * Create new brand
     */
    async create(payload: CreateBrandPayload): Promise<AdminBrand> {
        const response = await http.post<AdminBrand>("/admin/brands/", payload);
        return response.data;
    },

    /**
     * Update brand
     */
    async update(slug: string, payload: UpdateBrandPayload): Promise<AdminBrand> {
        const response = await http.patch<AdminBrand>(`/admin/brands/${slug}/`, payload);
        return response.data;
    },

    /**
     * Delete brand
     */
    async delete(slug: string): Promise<void> {
        await http.delete(`/admin/brands/${slug}/`);
    },
};
