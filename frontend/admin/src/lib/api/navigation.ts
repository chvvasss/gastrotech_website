import { http } from "./http";
import type { NavCategory } from "@/types/api";

export const navigationApi = {
  /**
   * Get navigation structure (categories with nested series)
   */
  async getNav(): Promise<NavCategory[]> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.get<NavCategory[]>("/nav/");
    return response.data;
  },
};
