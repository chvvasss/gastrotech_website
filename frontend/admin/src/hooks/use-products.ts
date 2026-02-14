"use client";

import { useQuery } from "@tanstack/react-query";
import { catalogApi, type ProductsParams } from "@/lib/api/catalog";
import type { ProductListItem, PaginatedResponse, Series } from "@/types/api";

export const productKeys = {
  all: ["products"] as const,
  lists: () => [...productKeys.all, "list"] as const,
  list: (params: ProductsParams) => [...productKeys.lists(), params] as const,
};

export const seriesKeys = {
  all: ["series"] as const,
  list: () => [...seriesKeys.all, "list"] as const,
};

export const statsKeys = {
  all: ["stats"] as const,
  range: (range: string) => [...statsKeys.all, range] as const,
};

export function useProducts(params: ProductsParams = {}) {
  return useQuery<PaginatedResponse<ProductListItem>>({
    queryKey: productKeys.list(params),
    queryFn: () => catalogApi.listProducts(params),
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useSeries() {
  return useQuery<Series[]>({
    queryKey: seriesKeys.list(),
    queryFn: () => catalogApi.listSeries(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

import type { DashboardStats } from "@/types/api";

export function useStats(range: "7d" | "14d" | "30d" | "90d" = "30d") {
  return useQuery<DashboardStats>({
    queryKey: statsKeys.range(range),
    queryFn: () => catalogApi.getStats(range),
    staleTime: 60 * 1000, // 1 minute
  });
}
