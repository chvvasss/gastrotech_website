import { http } from "./http";
import type { Category, Series, TaxonomyNode } from "@/types/api";

// =============================================================================
// Admin Taxonomy API - Full CRUD operations
// =============================================================================

// -----------------------------------------------------------------------------
// Category CRUD
// -----------------------------------------------------------------------------

export interface AdminCategory extends Category {
    id: string;
    parent: string | null;
    cover_media: string | null;
    products_count?: number;
    series_count?: number;
    series?: AdminSeries[];
    created_at: string;
    updated_at: string;
}

export interface CreateCategoryPayload {
    name: string;
    slug?: string;
    menu_label?: string;
    description_short?: string;
    order?: number;
    is_featured?: boolean;
    cover_media?: string | null;
    parent_slug?: string | null;
}

export interface UpdateCategoryPayload extends Partial<CreateCategoryPayload> { }

export const adminCategoriesApi = {
    /**
     * List all categories
     */
    async list(params?: { parent?: string | "null" }): Promise<AdminCategory[]> {
        const queryParams = new URLSearchParams();
        if (params?.parent) queryParams.set("parent", params.parent);
        const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
        const response = await http.get<AdminCategory[] | { results: AdminCategory[] }>(`/admin/categories/${query}`);
        // Handle both paginated and non-paginated responses
        const data = response.data;
        return Array.isArray(data) ? data : (data.results || []);
    },

    /**
     * Get single category by slug
     */
    async get(slug: string): Promise<AdminCategory> {
        const response = await http.get<AdminCategory>(`/admin/categories/${slug}/`);
        return response.data;
    },

    /**
     * Create new category
     */
    async create(payload: CreateCategoryPayload): Promise<AdminCategory> {
        const response = await http.post<AdminCategory>("/admin/categories/", payload);
        return response.data;
    },

    /**
     * Update category
     */
    async update(slug: string, payload: UpdateCategoryPayload): Promise<AdminCategory> {
        const response = await http.patch<AdminCategory>(`/admin/categories/${slug}/`, payload);
        return response.data;
    },

    /**
     * Delete category
     */
    async delete(slug: string): Promise<void> {
        await http.delete(`/admin/categories/${slug}/`);
    },
};

// -----------------------------------------------------------------------------
// Series CRUD
// -----------------------------------------------------------------------------

export interface AdminSeries extends Series {
    id: string;
    category: string;
    cover_media: string | null;
    cover_media_url: string | null;
    products_count?: number;
    created_at: string;
    updated_at: string;
}

export interface CreateSeriesPayload {
    name: string;
    slug?: string;
    category_slug: string;
    description_short?: string;
    order?: number;
    is_featured?: boolean;
    cover_media?: string | null;
}

export interface UpdateSeriesPayload extends Partial<Omit<CreateSeriesPayload, "category_slug">> {
    category_slug?: string;
}

export const adminSeriesApi = {
    /**
     * List all series
     */
    async list(params?: { category?: string }): Promise<AdminSeries[]> {
        const queryParams = new URLSearchParams();
        if (params?.category) queryParams.set("category", params.category);
        const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
        const response = await http.get<AdminSeries[] | { results: AdminSeries[] }>(`/admin/series/${query}`);
        // Handle both paginated and non-paginated responses
        const data = response.data;
        return Array.isArray(data) ? data : (data.results || []);
    },

    /**
     * Get single series by slug
     */
    async get(slug: string): Promise<AdminSeries> {
        const response = await http.get<AdminSeries>(`/admin/series/${slug}/`);
        return response.data;
    },

    /**
     * Create new series
     */
    async create(payload: CreateSeriesPayload): Promise<AdminSeries> {
        const response = await http.post<AdminSeries>("/admin/series/", payload);
        return response.data;
    },

    /**
     * Update series
     */
    async update(slug: string, payload: UpdateSeriesPayload): Promise<AdminSeries> {
        const response = await http.patch<AdminSeries>(`/admin/series/${slug}/`, payload);
        return response.data;
    },

    /**
     * Delete series
     */
    async delete(slug: string): Promise<void> {
        await http.delete(`/admin/series/${slug}/`);
    },
};

// -----------------------------------------------------------------------------
// TaxonomyNode CRUD
// -----------------------------------------------------------------------------

export interface AdminTaxonomyNode {
    id: string;
    name: string;
    slug: string;
    series: string;
    series_slug: string;
    parent: string | null;
    parent_id: string | null;
    order: number;
    full_path: string;
    depth: number;
    is_leaf: boolean;
    created_at: string;
    updated_at: string;
}

export interface CreateTaxonomyNodePayload {
    name: string;
    slug?: string;
    series_slug: string;
    parent_id?: string | null;
    order?: number;
}

export interface UpdateTaxonomyNodePayload {
    name?: string;
    slug?: string;
    parent_id?: string | null;
    order?: number;
}

export const adminTaxonomyNodesApi = {
    /**
     * List taxonomy nodes
     */
    async list(params?: {
        series?: string;
        parent?: string | "null";
        leaf_only?: boolean;
    }): Promise<AdminTaxonomyNode[]> {
        const queryParams = new URLSearchParams();
        if (params?.series) queryParams.set("series", params.series);
        if (params?.parent) queryParams.set("parent", params.parent);
        if (params?.leaf_only) queryParams.set("leaf_only", "true");
        const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
        const response = await http.get<AdminTaxonomyNode[] | { results: AdminTaxonomyNode[] }>(`/admin/taxonomy-nodes/${query}`);
        // Handle both paginated and non-paginated responses
        const data = response.data;
        return Array.isArray(data) ? data : (data.results || []);
    },

    /**
     * Get single taxonomy node by ID
     */
    async get(id: string): Promise<AdminTaxonomyNode> {
        const response = await http.get<AdminTaxonomyNode>(`/admin/taxonomy-nodes/${id}/`);
        return response.data;
    },

    /**
     * Create new taxonomy node
     */
    async create(payload: CreateTaxonomyNodePayload): Promise<AdminTaxonomyNode> {
        const response = await http.post<AdminTaxonomyNode>("/admin/taxonomy-nodes/", payload);
        return response.data;
    },

    /**
     * Update taxonomy node
     */
    async update(id: string, payload: UpdateTaxonomyNodePayload): Promise<AdminTaxonomyNode> {
        const response = await http.patch<AdminTaxonomyNode>(`/admin/taxonomy-nodes/${id}/`, payload);
        return response.data;
    },

    /**
     * Delete taxonomy node
     */
    async delete(id: string): Promise<void> {
        await http.delete(`/admin/taxonomy-nodes/${id}/`);
    },
};
