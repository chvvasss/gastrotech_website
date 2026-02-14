"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminSpecsApi, CreateSpecKeyPayload, UpdateSpecKeyPayload } from "@/lib/api/admin-specs";

export const adminSpecsKeys = {
    all: ["admin-specs"] as const,
    list: (params?: { search?: string }) => [...adminSpecsKeys.all, "list", params] as const,
    detail: (slug: string) => [...adminSpecsKeys.all, "detail", slug] as const,
};

export function useAdminSpecs(params?: { search?: string }) {
    return useQuery({
        queryKey: adminSpecsKeys.list(params),
        queryFn: () => adminSpecsApi.list(params),
    });
}

export function useAdminSpec(slug: string | null) {
    return useQuery({
        queryKey: adminSpecsKeys.detail(slug || ""),
        queryFn: () => adminSpecsApi.get(slug!),
        enabled: !!slug,
    });
}

export function useCreateSpecKey() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: CreateSpecKeyPayload) => adminSpecsApi.create(payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: adminSpecsKeys.all });
        },
    });
}

export function useUpdateSpecKey() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ slug, payload }: { slug: string; payload: UpdateSpecKeyPayload }) =>
            adminSpecsApi.update(slug, payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: adminSpecsKeys.all });
        },
    });
}

export function useDeleteSpecKey() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (slug: string) => adminSpecsApi.delete(slug),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: adminSpecsKeys.all });
        },
    });
}

export function useReorderSpecKeys() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (slugs: string[]) => adminSpecsApi.reorder(slugs),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: adminSpecsKeys.all });
        },
    });
}
