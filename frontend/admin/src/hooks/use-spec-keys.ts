"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { specKeysApi } from "@/lib/api/spec-keys";
import { catalogProductKeys } from "./use-catalog-products";
import type { SpecKey, SpecTemplate } from "@/types/api";

export const specKeysKeys = {
  all: ["spec-keys"] as const,
  list: () => [...specKeysKeys.all, "list"] as const,
  templates: () => [...specKeysKeys.all, "templates"] as const,
};

/**
 * Hook to list all spec keys
 */
export function useSpecKeys() {
  return useQuery<SpecKey[]>({
    queryKey: specKeysKeys.list(),
    queryFn: () => specKeysApi.listSpecKeys(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to list spec templates
 */
export function useSpecTemplates() {
  return useQuery<SpecTemplate[]>({
    queryKey: specKeysKeys.templates(),
    queryFn: () => specKeysApi.listTemplates(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to apply a template to a product
 */
export function useApplySpecTemplate(productSlug: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ productId, templateId, overwrite }: { 
      productId: string; 
      templateId: string; 
      overwrite: boolean 
    }) => specKeysApi.applyTemplate(productId, templateId, overwrite),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogProductKeys.detail(productSlug) });
    },
  });
}
