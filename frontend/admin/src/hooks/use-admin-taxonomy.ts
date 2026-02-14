import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
    adminCategoriesApi,
    adminSeriesApi,
    adminTaxonomyNodesApi,
    type AdminCategory,
    type AdminSeries,
    type AdminTaxonomyNode,
    type CreateCategoryPayload,
    type UpdateCategoryPayload,
    type CreateSeriesPayload,
    type UpdateSeriesPayload,
    type CreateTaxonomyNodePayload,
    type UpdateTaxonomyNodePayload,
} from "@/lib/api/admin-taxonomy";

// =============================================================================
// Category Hooks
// =============================================================================

export function useCategories(params?: { parent?: string | "null" }) {
    return useQuery({
        queryKey: ["admin-categories", params],
        queryFn: () => adminCategoriesApi.list(params),
    });
}

export function useCategory(slug: string | null) {
    return useQuery({
        queryKey: ["admin-category", slug],
        queryFn: () => (slug ? adminCategoriesApi.get(slug) : null),
        enabled: !!slug,
    });
}

export function useCreateCategory() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: CreateCategoryPayload) => adminCategoriesApi.create(payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
            queryClient.invalidateQueries({ queryKey: ["nav"] });
        },
    });
}

export function useUpdateCategory() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ slug, payload }: { slug: string; payload: UpdateCategoryPayload }) =>
            adminCategoriesApi.update(slug, payload),
        onSuccess: (data: AdminCategory) => {
            queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
            queryClient.invalidateQueries({ queryKey: ["admin-category", data.slug] });
            queryClient.invalidateQueries({ queryKey: ["nav"] });
        },
    });
}

export function useDeleteCategory() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (slug: string) => adminCategoriesApi.delete(slug),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
            queryClient.invalidateQueries({ queryKey: ["nav"] });
        },
    });
}

// =============================================================================
// Series Hooks
// =============================================================================

export function useAdminSeries(params?: { category?: string }) {
    return useQuery({
        queryKey: ["admin-series", params],
        queryFn: () => adminSeriesApi.list(params),
    });
}

export function useAdminSeriesDetail(slug: string | null) {
    return useQuery({
        queryKey: ["admin-series-detail", slug],
        queryFn: () => (slug ? adminSeriesApi.get(slug) : null),
        enabled: !!slug,
    });
}

export function useCreateSeries() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: CreateSeriesPayload) => adminSeriesApi.create(payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-series"] });
            queryClient.invalidateQueries({ queryKey: ["nav"] });
        },
    });
}

export function useUpdateSeries() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ slug, payload }: { slug: string; payload: UpdateSeriesPayload }) =>
            adminSeriesApi.update(slug, payload),
        onSuccess: (data: AdminSeries) => {
            queryClient.invalidateQueries({ queryKey: ["admin-series"] });
            queryClient.invalidateQueries({ queryKey: ["admin-series-detail", data.slug] });
            queryClient.invalidateQueries({ queryKey: ["nav"] });
        },
    });
}

export function useDeleteSeries() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (slug: string) => adminSeriesApi.delete(slug),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-series"] });
            queryClient.invalidateQueries({ queryKey: ["nav"] });
        },
    });
}

// =============================================================================
// TaxonomyNode Hooks
// =============================================================================

export function useAdminTaxonomyNodes(params?: {
    series?: string;
    parent?: string | "null";
    leaf_only?: boolean;
}) {
    return useQuery({
        queryKey: ["admin-taxonomy-nodes", params],
        queryFn: () => adminTaxonomyNodesApi.list(params),
        enabled: !!params?.series,
    });
}

export function useAdminTaxonomyNode(id: string | null) {
    return useQuery({
        queryKey: ["admin-taxonomy-node", id],
        queryFn: () => (id ? adminTaxonomyNodesApi.get(id) : null),
        enabled: !!id,
    });
}

export function useCreateTaxonomyNode() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: CreateTaxonomyNodePayload) => adminTaxonomyNodesApi.create(payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-taxonomy-nodes"] });
            queryClient.invalidateQueries({ queryKey: ["taxonomy-tree"] });
        },
    });
}

export function useUpdateTaxonomyNode() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, payload }: { id: string; payload: UpdateTaxonomyNodePayload }) =>
            adminTaxonomyNodesApi.update(id, payload),
        onSuccess: (data: AdminTaxonomyNode) => {
            queryClient.invalidateQueries({ queryKey: ["admin-taxonomy-nodes"] });
            queryClient.invalidateQueries({ queryKey: ["admin-taxonomy-node", data.id] });
            queryClient.invalidateQueries({ queryKey: ["taxonomy-tree"] });
        },
    });
}

export function useDeleteTaxonomyNode() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => adminTaxonomyNodesApi.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-taxonomy-nodes"] });
            queryClient.invalidateQueries({ queryKey: ["taxonomy-tree"] });
        },
    });
}
