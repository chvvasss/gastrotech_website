import { http } from "./http";

/**
 * Admin search result item
 */
export interface SearchResultItem {
  type: "product" | "category" | "series" | "taxonomy" | "variant";
  id: string;
  title: string;
  subtitle: string | null;
  href: string;
  score: number;
}

/**
 * Admin search response
 */
export interface AdminSearchResponse {
  query: string;
  results: SearchResultItem[];
}

/**
 * Admin Search API
 */
export const adminSearchApi = {
  /**
   * Perform global search across catalog entities.
   * 
   * @param query - Search query (minimum 2 characters)
   * @param limit - Maximum results to return (default: 20, max: 50)
   * @returns Search results grouped by type
   */
  async search(query: string, limit: number = 20): Promise<AdminSearchResponse> {
    if (query.length < 2) {
      return { query, results: [] };
    }
    
    const params = new URLSearchParams();
    params.set("q", query);
    if (limit) params.set("limit", limit.toString());
    
    const response = await http.get<AdminSearchResponse>(
      `/admin/search/?${params.toString()}`
    );
    return response.data;
  },
};
