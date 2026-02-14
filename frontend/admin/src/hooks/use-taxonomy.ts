"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { taxonomyApi } from "@/lib/api/taxonomy";
import type { TaxonomyNode } from "@/types/api";

export const taxonomyKeys = {
  all: ["taxonomy"] as const,
  tree: (seriesSlug: string) => [...taxonomyKeys.all, "tree", seriesSlug] as const,
};

export function useTaxonomyTree(seriesSlug: string | null) {
  return useQuery<TaxonomyNode[]>({
    queryKey: taxonomyKeys.tree(seriesSlug || ""),
    queryFn: () => taxonomyApi.getTree(seriesSlug!),
    enabled: !!seriesSlug,
    staleTime: 60 * 1000, // 1 minute
  });
}

export interface GenerateProductsPayload {
  series: string;
  leaf_slugs: string[];
  dry_run?: boolean;
  status?: "draft" | "active" | "archived";
  template_id?: string;
}

export function useGenerateProductsFromLeafNodes() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: GenerateProductsPayload) =>
      taxonomyApi.generateProductsFromLeafNodes(payload),
    onSuccess: (data) => {
      // Only invalidate if not dry_run
      if (!data.dry_run) {
        queryClient.invalidateQueries({ queryKey: ["products"] });
        queryClient.invalidateQueries({ queryKey: ["catalog-products"] });
      }
    },
  });
}
