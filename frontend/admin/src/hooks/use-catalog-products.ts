"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminProductsApi } from "@/lib/api/admin-products";
import { productsApi, type ProductsParams } from "@/lib/api/products";
import { adminCatalogApi } from "@/lib/api/admin-catalog";
import type { ProductDetail, PaginatedResponse } from "@/types/api";
import type { AdminProductListItem } from "@/lib/api/admin-products";

export const catalogProductKeys = {
  all: ["catalog-products"] as const,
  lists: () => [...catalogProductKeys.all, "list"] as const,
  list: (params: ProductsParams) => [...catalogProductKeys.lists(), params] as const,
  details: () => [...catalogProductKeys.all, "detail"] as const,
  detail: (slug: string) => [...catalogProductKeys.details(), slug] as const,
};

export function useCatalogProducts(params: ProductsParams = {}) {
  return useQuery<PaginatedResponse<AdminProductListItem>>({
    queryKey: catalogProductKeys.list(params),
    queryFn: () => adminProductsApi.listProducts(params),
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useProductDetail(slug: string | null) {
  return useQuery<ProductDetail>({
    queryKey: catalogProductKeys.detail(slug || ""),
    queryFn: () => adminProductsApi.getProduct(slug!),
    enabled: !!slug,
    staleTime: 60 * 1000,
  });
}

export function useProductMediaUpload(productId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { file: File; alt?: string; is_primary?: boolean }) =>
      adminCatalogApi.productMediaUpload(productId, params.file, {
        alt: params.alt,
        is_primary: params.is_primary,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogProductKeys.details() });
    },
  });
}

export function useProductMediaReorder(productId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (items: Array<{ product_media_id: string; sort_order: number; is_primary?: boolean }>) =>
      adminCatalogApi.productMediaReorder(productId, items),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogProductKeys.details() });
    },
  });
}

export function useProductMediaDelete(productId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (productMediaId: string) =>
      adminCatalogApi.productMediaDelete(productId, productMediaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogProductKeys.details() });
    },
  });
}
