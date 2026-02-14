import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
    adminBrandsApi,
    type AdminBrand,
    type CreateBrandPayload,
    type UpdateBrandPayload,
} from "@/lib/api/admin-brands";

// =============================================================================
// Brand Hooks
// =============================================================================

export function useBrands(params?: { is_active?: boolean }) {
    return useQuery({
        queryKey: ["admin-brands", params],
        queryFn: () => adminBrandsApi.list(params),
    });
}

export function useBrand(slug: string | null) {
    return useQuery({
        queryKey: ["admin-brand", slug],
        queryFn: () => (slug ? adminBrandsApi.get(slug) : null),
        enabled: !!slug,
    });
}

export function useCreateBrand() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: CreateBrandPayload) => adminBrandsApi.create(payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-brands"] });
        },
    });
}

export function useUpdateBrand() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ slug, payload }: { slug: string; payload: UpdateBrandPayload }) =>
            adminBrandsApi.update(slug, payload),
        onSuccess: (data: AdminBrand) => {
            queryClient.invalidateQueries({ queryKey: ["admin-brands"] });
            queryClient.invalidateQueries({ queryKey: ["admin-brand", data.slug] });
        },
    });
}

export function useDeleteBrand() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (slug: string) => adminBrandsApi.delete(slug),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-brands"] });
        },
    });
}
