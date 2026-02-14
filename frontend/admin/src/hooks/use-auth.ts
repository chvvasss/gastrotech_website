"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { authApi, TokenStore } from "@/lib/api";
import type { LoginRequest, User } from "@/types/api";

export const authKeys = {
  me: ["auth", "me"] as const,
};

export function useMe() {
  // Only run the query if we have tokens
  const hasTokens = typeof window !== "undefined" && TokenStore.hasTokens();

  return useQuery<User>({
    queryKey: authKeys.me,
    queryFn: () => authApi.me(),
    enabled: hasTokens, // Only fetch when tokens exist
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchInterval: false,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onSuccess: (user) => {
      queryClient.setQueryData(authKeys.me, user);
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return useCallback(() => {
    TokenStore.clearTokens();
    queryClient.clear();
    router.replace("/login");
  }, [router, queryClient]);
}
