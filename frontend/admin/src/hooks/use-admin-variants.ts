"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { 
  adminVariantsApi, 
  type CreateVariantPayload, 
  type PatchVariantPayload,
  type BulkUpdateVariantItem 
} from "@/lib/api/admin-variants";
import { catalogProductKeys } from "./use-catalog-products";

/**
 * Hook to create a new variant
 */
export function useCreateVariant(productSlug?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateVariantPayload) =>
      adminVariantsApi.createVariant(payload),
    onSuccess: () => {
      // Invalidate product detail to refresh variants list
      if (productSlug) {
        queryClient.invalidateQueries({ queryKey: catalogProductKeys.detail(productSlug) });
      }
      queryClient.invalidateQueries({ queryKey: catalogProductKeys.lists() });
    },
  });
}

/**
 * Hook to patch/update a variant
 */
export function usePatchVariant(productSlug?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ modelCode, payload }: { modelCode: string; payload: PatchVariantPayload }) =>
      adminVariantsApi.patchVariant(modelCode, payload),
    onSuccess: () => {
      if (productSlug) {
        queryClient.invalidateQueries({ queryKey: catalogProductKeys.detail(productSlug) });
      }
    },
  });
}

/**
 * Hook to delete a variant
 */
export function useDeleteVariant(productSlug?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (modelCode: string) =>
      adminVariantsApi.deleteVariant(modelCode),
    onSuccess: () => {
      if (productSlug) {
        queryClient.invalidateQueries({ queryKey: catalogProductKeys.detail(productSlug) });
      }
      queryClient.invalidateQueries({ queryKey: catalogProductKeys.lists() });
    },
  });
}

/**
 * Hook to bulk update variants
 */
export function useBulkUpdateVariants(productSlug?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (updates: BulkUpdateVariantItem[]) =>
      adminVariantsApi.bulkUpdate(updates),
    onSuccess: () => {
      if (productSlug) {
        queryClient.invalidateQueries({ queryKey: catalogProductKeys.detail(productSlug) });
      }
      queryClient.invalidateQueries({ queryKey: catalogProductKeys.lists() });
    },
  });
}
