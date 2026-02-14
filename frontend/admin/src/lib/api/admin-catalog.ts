import { http } from "./http";
import type {
  MediaUploadResponse,
  ProductMediaUploadResponse,
} from "@/types/api";

export const adminCatalogApi = {
  /**
   * Upload media file
   */
  async mediaUpload(file: File): Promise<MediaUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    // IMPORTANT: Trailing slash for DRF
    const response = await http.post<MediaUploadResponse>(
      "/admin/media/upload/",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  /**
   * Upload media for a product
   */
  async productMediaUpload(
    productId: string,
    file: File,
    options?: { alt?: string; is_primary?: boolean }
  ): Promise<ProductMediaUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    if (options?.alt) formData.append("alt", options.alt);
    if (options?.is_primary) formData.append("is_primary", "true");

    // IMPORTANT: Trailing slash for DRF
    const response = await http.post<ProductMediaUploadResponse>(
      `/admin/products/${productId}/media/upload/`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  /**
   * Reorder product media
   */
  async productMediaReorder(
    productId: string,
    items: Array<{
      product_media_id: string;
      sort_order: number;
      is_primary?: boolean;
    }>
  ): Promise<{ updated: number; message: string }> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.patch(
      `/admin/products/${productId}/media/reorder/`,
      { items }
    );
    return response.data;
  },

  /**
   * Delete product media
   */
  async productMediaDelete(
    productId: string,
    productMediaId: string
  ): Promise<void> {
    // IMPORTANT: Trailing slash for DRF
    await http.delete(`/admin/products/${productId}/media/${productMediaId}/`);
  },

  /**
   * Generate products from leaf taxonomy nodes
   */
  async generateProductsFromLeafNodes(payload: {
    series: string;
    leaf_slugs: string[];
  }): Promise<{
    created: number;
    skipped_existing: number;
    skipped_non_leaf: number;
    created_slugs: string[];
    errors: Array<{ slug: string; error: string }>;
  }> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.post("/admin/taxonomy/generate-products/", payload);
    return response.data;
  },

  /**
   * Bulk Upload: Upload Excel file
   */
  async bulkUpload(file: File, dryRun: boolean): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("dry_run", String(dryRun));

    // IMPORTANT: Trailing slash for DRF
    const response = await http.post("/admin/bulk-upload/", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  /**
   * Bulk Upload: Download Template
   */
  async downloadBulkTemplate(): Promise<Blob> {
    // IMPORTANT: Trailing slash and responseType blob
    const response = await http.get("/admin/bulk-upload/template/", {
      responseType: "blob",
    });
    return response.data;
  },
};
