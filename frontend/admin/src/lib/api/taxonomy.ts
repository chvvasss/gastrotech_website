import { http } from "./http";
import type { TaxonomyNode } from "@/types/api";

export const taxonomyApi = {
  /**
   * Get taxonomy tree for a series
   */
  async getTree(seriesSlug: string): Promise<TaxonomyNode[]> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.get<TaxonomyNode[]>(
      `/taxonomy/tree/?series=${encodeURIComponent(seriesSlug)}`
    );
    return response.data;
  },

  /**
   * Generate products from leaf nodes (admin endpoint)
   * Supports dry_run for preview
   */
  async generateProductsFromLeafNodes(payload: {
    series: string;
    leaf_slugs: string[];
    dry_run?: boolean;
    status?: "draft" | "active" | "archived";
    template_id?: string;
  }): Promise<{
    created: number;
    skipped_existing: number;
    skipped_non_leaf: number;
    created_slugs: string[];
    skipped_existing_slugs: string[];
    preview: Array<{
      node_slug: string;
      node_path: string;
      expected_slug: string;
      status: "will_create" | "exists";
      existing_product_slug: string | null;
    }>;
    errors: Array<{ slug: string; error: string }>;
    dry_run: boolean;
  }> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.post("/admin/taxonomy/generate-products/", payload);
    return response.data;
  },
};
