import { useQuery } from "@tanstack/react-query";
import { catalogApi } from "@/lib/api/catalog";

/**
 * Fetch categories list with series and product counts
 */
export function useCategoriesWithCounts(params?: { search?: string }) {
  return useQuery({
    queryKey: ["categories-with-counts", params],
    queryFn: () => catalogApi.listCategoriesWithCounts(params),
  });
}

/**
 * Fetch category detail with series list and counts
 */
export function useCategoryDetail(slug: string, brand?: string) {
  return useQuery({
    queryKey: ["category-detail", slug, brand],
    queryFn: () => catalogApi.getCategoryDetail(slug, brand),
    enabled: !!slug,
  });
}
