import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  adminCategoryCatalogsApi,
  type CategoryCatalogCreatePayload,
  type CategoryCatalogUpdatePayload,
} from "@/lib/api/admin-category-catalogs";

const QUERY_KEY = "admin-category-catalogs";

export function useAdminCategoryCatalogs(categorySlug?: string) {
  return useQuery({
    queryKey: [QUERY_KEY, categorySlug],
    queryFn: () => adminCategoryCatalogsApi.list(categorySlug),
  });
}

export function useCreateCategoryCatalog() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CategoryCatalogCreatePayload) =>
      adminCategoryCatalogsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
    },
  });
}

export function useUpdateCategoryCatalog() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CategoryCatalogUpdatePayload }) =>
      adminCategoryCatalogsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
    },
  });
}

export function useDeleteCategoryCatalog() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => adminCategoryCatalogsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
    },
  });
}
