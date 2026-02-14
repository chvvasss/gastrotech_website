import { http } from "./http";

export interface CategoryCatalogMediaDetails {
  id: string;
  filename: string;
  size_bytes: number | null;
  content_type: string | null;
  file_url: string;
}

export interface CategoryCatalog {
  id: string;
  category: string;
  category_name: string;
  title_tr: string;
  title_en: string;
  description: string;
  media: string;
  media_details: CategoryCatalogMediaDetails | null;
  order: number;
  published: boolean;
  created_at: string;
  updated_at: string;
}

export interface CategoryCatalogCreatePayload {
  category: string;
  title_tr: string;
  title_en?: string;
  description?: string;
  media: string;
  order?: number;
  published?: boolean;
}

export interface CategoryCatalogUpdatePayload {
  title_tr?: string;
  title_en?: string;
  description?: string;
  media?: string;
  order?: number;
  published?: boolean;
  category?: string;
}

export const adminCategoryCatalogsApi = {
  async list(categorySlug?: string): Promise<CategoryCatalog[]> {
    const params = categorySlug ? `?category_slug=${categorySlug}` : "";
    const response = await http.get<CategoryCatalog[] | { results: CategoryCatalog[] }>(
      `/admin/category-catalogs/${params}`
    );
    // Handle both paginated and non-paginated responses
    const data = response.data;
    return Array.isArray(data) ? data : (data.results || []);
  },

  async get(id: string): Promise<CategoryCatalog> {
    const response = await http.get<CategoryCatalog>(
      `/admin/category-catalogs/${id}/`
    );
    return response.data;
  },

  async create(data: CategoryCatalogCreatePayload): Promise<CategoryCatalog> {
    const response = await http.post<CategoryCatalog>(
      `/admin/category-catalogs/`,
      data
    );
    return response.data;
  },

  async update(
    id: string,
    data: CategoryCatalogUpdatePayload
  ): Promise<CategoryCatalog> {
    const response = await http.patch<CategoryCatalog>(
      `/admin/category-catalogs/${id}/`,
      data
    );
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await http.delete(`/admin/category-catalogs/${id}/`);
  },
};
