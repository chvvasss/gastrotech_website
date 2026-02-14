import { http } from "./http";
import type { SpecKey, SpecTemplate } from "@/types/api";

// Helper to extract array from potentially paginated response
function extractArray<T>(data: T[] | { results: T[] } | unknown): T[] {
  if (Array.isArray(data)) {
    return data;
  }
  if (data && typeof data === "object" && "results" in data) {
    return (data as { results: T[] }).results;
  }
  return [];
}

export const specKeysApi = {
  /**
   * List all spec keys
   */
  async listSpecKeys(): Promise<SpecKey[]> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.get<SpecKey[] | { results: SpecKey[] }>("/spec-keys/");
    return extractArray<SpecKey>(response.data);
  },

  /**
   * List spec templates (admin endpoint)
   */
  async listTemplates(): Promise<SpecTemplate[]> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.get<SpecTemplate[] | { results: SpecTemplate[] }>("/admin/spec-templates/");
    return extractArray<SpecTemplate>(response.data);
  },

  /**
   * Apply template to product (admin endpoint)
   */
  async applyTemplate(
    productId: string,
    templateId: string,
    overwrite: boolean = false
  ): Promise<{ updated_fields: string[] }> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.post(`/admin/products/${productId}/apply-template/`, {
      template_id: templateId,
      overwrite,
    });
    return response.data;
  },
};
