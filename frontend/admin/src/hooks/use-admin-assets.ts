"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminAssetsApi, CreateCatalogAssetPayload, UpdateCatalogAssetPayload } from "@/lib/api/admin-assets";
import { mediaApi } from "@/lib/api/media";

export const adminAssetsKeys = {
    all: ["admin-assets"] as const,
    list: () => [...adminAssetsKeys.all, "list"] as const,
    detail: (id: string) => [...adminAssetsKeys.all, "detail", id] as const,
};

export function useAdminAssets() {
    return useQuery({
        queryKey: adminAssetsKeys.list(),
        queryFn: () => adminAssetsApi.list(),
    });
}

export function useCreateCatalogAsset() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (payload: CreateCatalogAssetPayload) => adminAssetsApi.create(payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: adminAssetsKeys.all });
        },
    });
}

export function useUpdateCatalogAsset() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, payload }: { id: string; payload: UpdateCatalogAssetPayload }) =>
            adminAssetsApi.update(id, payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: adminAssetsKeys.all });
        },
    });
}

export function useDeleteCatalogAsset() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => adminAssetsApi.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: adminAssetsKeys.all });
        },
    });
}

export function useRefUploadMedia() {
    return useMutation({
        mutationFn: (file: File) => mediaApi.upload(file),
    });
}
