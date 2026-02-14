import { http } from "./http";

// =============================================================================
// Admin Catalog Assets API
// =============================================================================

export interface AdminCatalogAsset {
    id: string;
    title_tr: string;
    title_en: string | null;
    media: string; // Media UUID
    media_details?: {
        id: string;
        file_url: string;
        filename: string;
        size_bytes: number;
    };
    is_primary: boolean;
    order: number;
    published: boolean;
    created_at: string;
    updated_at: string;
}

export interface CreateCatalogAssetPayload {
    title_tr: string;
    title_en?: string;
    media: string;
    is_primary?: boolean;
    order?: number;
    published?: boolean;
}

export interface UpdateCatalogAssetPayload extends Partial<CreateCatalogAssetPayload> { }

export const adminAssetsApi = {
    /**
     * List all catalog assets
     */
    async list(): Promise<AdminCatalogAsset[]> {
        const response = await http.get<AdminCatalogAsset[] | { results: AdminCatalogAsset[] }>(`/admin/catalog-assets/`);
        const data = response.data;
        return Array.isArray(data) ? data : (data.results || []);
    },

    /**
     * Get single catalog asset
     */
    async get(id: string): Promise<AdminCatalogAsset> {
        const response = await http.get<AdminCatalogAsset>(`/admin/catalog-assets/${id}/`);
        return response.data;
    },

    /**
     * Create new catalog asset
     */
    async create(payload: CreateCatalogAssetPayload): Promise<AdminCatalogAsset> {
        const response = await http.post<AdminCatalogAsset>("/admin/catalog-assets/", payload);
        return response.data;
    },

    /**
     * Update catalog asset
     */
    async update(id: string, payload: UpdateCatalogAssetPayload): Promise<AdminCatalogAsset> {
        const response = await http.patch<AdminCatalogAsset>(`/admin/catalog-assets/${id}/`, payload);
        return response.data;
    },

    /**
     * Delete catalog asset
     */
    async delete(id: string): Promise<void> {
        await http.delete(`/admin/catalog-assets/${id}/`);
    },
};
