import { http } from "./http";

// =============================================================================
// Admin Spec Key API
// =============================================================================

export interface AdminSpecKey {
    id: string; // UUID
    slug: string;
    label_tr: string;
    label_en: string | null;
    unit: string | null;
    value_type: "text" | "int" | "decimal" | "bool";
    sort_order: number;
    icon_media: string | null; // Media ID
    created_at: string;
    updated_at: string;
}

export interface CreateSpecKeyPayload {
    slug: string;
    label_tr: string;
    label_en?: string;
    unit?: string;
    value_type?: "text" | "int" | "decimal" | "bool";
    sort_order?: number;
    icon_media?: string | null;
}

export interface UpdateSpecKeyPayload extends Partial<CreateSpecKeyPayload> { }

export const adminSpecsApi = {
    /**
     * List all spec keys
     */
    async list(params?: { search?: string }): Promise<AdminSpecKey[]> {
        const queryParams = new URLSearchParams();
        if (params?.search) queryParams.set("search", params.search);

        // Spec keys are usually not paginated heavily, but we handle standard DRF response
        const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
        const response = await http.get<AdminSpecKey[] | { results: AdminSpecKey[] }>(`/admin/spec-keys/${query}`);

        const data = response.data;
        return Array.isArray(data) ? data : (data.results || []);
    },

    /**
     * Get single spec key
     */
    async get(slug: string): Promise<AdminSpecKey> {
        const response = await http.get<AdminSpecKey>(`/admin/spec-keys/${slug}/`);
        return response.data;
    },

    /**
     * Create new spec key
     */
    async create(payload: CreateSpecKeyPayload): Promise<AdminSpecKey> {
        const response = await http.post<AdminSpecKey>("/admin/spec-keys/", payload);
        return response.data;
    },

    /**
     * Update spec key
     */
    async update(slug: string, payload: UpdateSpecKeyPayload): Promise<AdminSpecKey> {
        const response = await http.patch<AdminSpecKey>(`/admin/spec-keys/${slug}/`, payload);
        return response.data;
    },

    /**
     * Delete spec key
     */
    async delete(slug: string): Promise<void> {
        await http.delete(`/admin/spec-keys/${slug}/`);
    },

    /**
     * Bulk reorder spec keys
     */
    async reorder(slugs: string[]): Promise<void> {
        await http.post("/admin/spec-keys/reorder/", { slugs });
    }
};
