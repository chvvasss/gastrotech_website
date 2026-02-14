"use client";

import { useQuery } from "@tanstack/react-query";
import {
  checkAdminCapabilities,
  type AdminCapabilities,
} from "@/lib/api/capabilities";

/**
 * Hook to check admin API capabilities
 */
export function useAdminCapabilities() {
  return useQuery<AdminCapabilities>({
    queryKey: ["admin-capabilities"],
    queryFn: checkAdminCapabilities,
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: false,
  });
}
