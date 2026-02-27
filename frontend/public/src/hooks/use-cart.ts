"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import {
  createCartToken,
  fetchCart,
  addToCart as apiAddToCart,
  updateCartItem as apiUpdateCartItem,
  removeCartItem as apiRemoveCartItem,
  clearCart as apiClearCart,
  ApiError,
} from "@/lib/api";
import { useToast } from "./use-toast";
import { Cart } from "@/lib/api/schemas";

const CART_TOKEN_KEY = "gastrotech_cart_token_v1";

// Mutex for cart session creation to prevent race conditions
let isCreatingSession = false;
let sessionPromise: Promise<{ cart_token: string; cart: Cart }> | null = null;

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(CART_TOKEN_KEY);
}

function storeToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(CART_TOKEN_KEY, token);
}

function clearStoredToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(CART_TOKEN_KEY);
}

export function useCart() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const resetCartSession = async () => {
    clearStoredToken();
    const result = await createCartToken();
    storeToken(result.cart_token);
    queryClient.setQueryData(["cart"], result.cart);
    return result;
  };

  const ensureCartSession = async (): Promise<{ token: string; cart?: Cart }> => {
    const existingToken = getStoredToken();
    if (existingToken) {
      const cachedCart = queryClient.getQueryData<Cart>(["cart"]);
      return { token: existingToken, cart: cachedCart };
    }

    // Use mutex to prevent multiple concurrent token creations
    if (isCreatingSession && sessionPromise) {
      const result = await sessionPromise;
      return { token: result.cart_token, cart: result.cart };
    }

    isCreatingSession = true;
    sessionPromise = createCartToken();

    try {
      const result = await sessionPromise;
      storeToken(result.cart_token);
      queryClient.setQueryData(["cart"], result.cart);
      return { token: result.cart_token, cart: result.cart };
    } finally {
      isCreatingSession = false;
      sessionPromise = null;
    }
  };

  // Fetch cart
  const { data: cart, isLoading } = useQuery({
    queryKey: ["cart"],
    queryFn: async () => {
      const currentToken = getStoredToken();
      if (!currentToken) {
        const result = await createCartToken();
        storeToken(result.cart_token);
        return result.cart;
      }
      try {
        return await fetchCart(currentToken);
      } catch (error) {
        if (error instanceof ApiError && error.isNotFound) {
          const result = await resetCartSession();
          toast({
            title: "Sepet yenilendi",
            description: "Oturum süresi doldu, lütfen tekrar deneyin.",
          });
          return result.cart;
        }
        throw error;
      }
    },
    staleTime: 30 * 1000, // 30 seconds
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status === 404) {
        // Token invalid, create new cart
        clearStoredToken();
        return failureCount < 1;
      }
      return failureCount < 3;
    },
  });

  // Add to cart mutation
  const addMutation = useMutation({
    mutationFn: async ({
      variantId,
      quantity = 1,
    }: {
      variantId: string;
      quantity?: number;
    }) => {
      const { token } = await ensureCartSession();
      try {
        return await apiAddToCart(token, variantId, quantity);
      } catch (error) {
        if (error instanceof ApiError && error.isNotFound) {
          await resetCartSession();
          throw new Error("cart_reset");
        }
        throw error;
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["cart"], data);
      toast({
        title: "Ürün eklendi",
        description: "Ürün sepete eklendi.",
      });
    },
    onError: (error) => {
      console.error("[useCart] Add item error:", error);

      if (error instanceof ApiError && error.isConflict) {
        toast({
          title: "Stok yetersiz",
          description: "İstenen miktar stokta mevcut değil.",
          variant: "destructive",
        });
      } else if (error instanceof ApiError) {
        // Log detailed API error
        console.error(`[useCart] API Error ${error.status}:`, error.body);
        toast({
          title: "Hata",
          description: error.body || `Ürün eklenirken bir hata oluştu (${error.status}).`,
          variant: "destructive",
        });
      } else {
        toast({
          title: "Hata",
          description: error instanceof Error ? error.message : "Ürün eklenirken bir hata oluştu.",
          variant: "destructive",
        });
      }
      if (error instanceof Error && error.message === "cart_reset") {
        toast({
          title: "Sepet yenilendi",
          description: "Lütfen ürünü tekrar ekleyin.",
        });
      }
    },
  });

  // Update quantity mutation
  const updateMutation = useMutation({
    mutationFn: async ({
      itemId,
      quantity,
    }: {
      itemId: string;
      quantity: number;
    }) => {
      const { token } = await ensureCartSession();
      try {
        return await apiUpdateCartItem(token, itemId, quantity);
      } catch (error) {
        if (error instanceof ApiError && error.isNotFound) {
          await resetCartSession();
          throw new Error("cart_reset");
        }
        throw error;
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["cart"], data);
    },
    onError: (error) => {
      if (error instanceof ApiError && error.isConflict) {
        toast({
          title: "Stok yetersiz",
          description: "İstenen miktar stokta mevcut değil.",
          variant: "destructive",
        });
      }
      if (error instanceof Error && error.message === "cart_reset") {
        toast({
          title: "Sepet yenilendi",
          description: "Lütfen miktarı yeniden güncelleyin.",
        });
      }
    },
  });

  // Remove item mutation
  const removeMutation = useMutation({
    mutationFn: async (itemId: string) => {
      const { token } = await ensureCartSession();
      try {
        return await apiRemoveCartItem(token, itemId);
      } catch (error) {
        if (error instanceof ApiError && error.isNotFound) {
          await resetCartSession();
          throw new Error("cart_reset");
        }
        throw error;
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["cart"], data);
      toast({
        title: "Ürün kaldırıldı",
        description: "Ürün sepetten kaldırıldı.",
      });
    },
    onError: (error) => {
      if (error instanceof Error && error.message === "cart_reset") {
        toast({
          title: "Sepet yenilendi",
          description: "Lütfen işlemi yeniden deneyin.",
        });
      }
    },
  });

  // Clear cart mutation
  const clearMutation = useMutation({
    mutationFn: async () => {
      const { token } = await ensureCartSession();
      try {
        return await apiClearCart(token);
      } catch (error) {
        if (error instanceof ApiError && error.isNotFound) {
          const result = await resetCartSession();
          return result.cart;
        }
        throw error;
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["cart"], data);
    },
  });

  const addItem = useCallback(
    (variantId: string, quantity = 1) => {
      return addMutation.mutateAsync({ variantId, quantity });
    },
    [addMutation]
  );

  const updateItem = useCallback(
    (itemId: string, quantity: number) => {
      return updateMutation.mutateAsync({ itemId, quantity });
    },
    [updateMutation]
  );

  const removeItem = useCallback(
    (itemId: string) => {
      return removeMutation.mutateAsync(itemId);
    },
    [removeMutation]
  );

  const clear = useCallback(() => {
    return clearMutation.mutateAsync();
  }, [clearMutation]);

  return {
    cart,
    isLoading,
    isAddingItem: addMutation.isPending,
    addItem,
    updateItem,
    removeItem,
    clear,
    token: getStoredToken(),
  };
}
