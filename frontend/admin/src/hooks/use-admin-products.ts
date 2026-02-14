"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { adminProductsApi, type PatchProductPayload, type CreateProductPayload, type ApplyTemplatePayload } from "@/lib/api/admin-products";
import { catalogProductKeys } from "./use-catalog-products";
import { productKeys } from "./use-products";

/**
 * Hook to create a new product
 */
export function useCreateProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateProductPayload) =>
      adminProductsApi.createProduct(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogProductKeys.lists() });
      queryClient.invalidateQueries({ queryKey: productKeys.lists() });
    },
  });
}

/**
 * Hook to patch/update a product
 */
export function usePatchProduct(slugOrId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: PatchProductPayload) =>
      adminProductsApi.patchProduct(slugOrId, payload),
    onSuccess: (data) => {
      // Invalidate both the specific product detail and the lists
      queryClient.invalidateQueries({ queryKey: catalogProductKeys.detail(slugOrId) });
      queryClient.invalidateQueries({ queryKey: catalogProductKeys.detail(data.slug) });
      queryClient.invalidateQueries({ queryKey: catalogProductKeys.lists() });
      queryClient.invalidateQueries({ queryKey: productKeys.lists() });
    },
  });
}

/**
 * Hook to delete a product
 */
export function useDeleteProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (slugOrId: string) =>
      adminProductsApi.deleteProduct(slugOrId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogProductKeys.lists() });
      queryClient.invalidateQueries({ queryKey: productKeys.lists() });
    },
  });
}

/**
 * Hook to apply a spec template to a product
 */
export function useApplyTemplate(slugOrId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ApplyTemplatePayload) =>
      adminProductsApi.applyTemplate(slugOrId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogProductKeys.detail(slugOrId) });
    },
  });
}

/**
 * Hook to list spec templates
 */
export function useSpecTemplates(seriesSlug?: string) {
  // This is a simple query - re-export from products API
  return adminProductsApi.listTemplates(seriesSlug);
}
