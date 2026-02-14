"use client";

import { useQuery } from "@tanstack/react-query";
import { navigationApi } from "@/lib/api/navigation";
import type { NavCategory } from "@/types/api";

export const navigationKeys = {
  all: ["navigation"] as const,
  nav: () => [...navigationKeys.all, "nav"] as const,
};

export function useNav() {
  return useQuery<NavCategory[]>({
    queryKey: navigationKeys.nav(),
    queryFn: () => navigationApi.getNav(),
    staleTime: 5 * 60 * 1000, // 5 minutes - navigation doesn't change often
  });
}
