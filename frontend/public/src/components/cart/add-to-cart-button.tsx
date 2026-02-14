"use client";

import { ShoppingCart, Loader2, Check } from "lucide-react";
import { useState } from "react";
import { Button, ButtonProps } from "@/components/ui/button";
import { useCart } from "@/hooks/use-cart";
import { cn } from "@/lib/utils";

interface AddToCartButtonProps extends Omit<ButtonProps, "onClick"> {
  variantId: string;
  quantity?: number;
  showIcon?: boolean;
  showText?: boolean;
}

export function AddToCartButton({
  variantId,
  quantity = 1,
  showIcon = true,
  showText = true,
  className,
  size = "default",
  variant = "default",
  ...props
}: AddToCartButtonProps) {
  const { addItem, isAddingItem, isLoading: isCartLoading } = useCart();
  const [justAdded, setJustAdded] = useState(false);

  const handleClick = async () => {
    if (!variantId || isAddingItem || isCartLoading) return;
    try {
      await addItem(variantId, quantity);
      setJustAdded(true);
      setTimeout(() => setJustAdded(false), 2000);
    } catch {
      // Errors are surfaced via toasts; avoid stale success UI
      setJustAdded(false);
    }
  };

  return (
    <Button
      onClick={handleClick}
      disabled={isAddingItem || isCartLoading || !variantId}
      className={cn(className)}
      size={size}
      variant={variant}
      {...props}
    >
      {isAddingItem ? (
        <Loader2 className={cn("h-4 w-4 animate-spin", showText && "mr-2")} />
      ) : justAdded ? (
        <Check className={cn("h-4 w-4", showText && "mr-2")} />
      ) : showIcon ? (
        <ShoppingCart className={cn("h-4 w-4", showText && "mr-2")} />
      ) : null}
      {showText && (justAdded ? "Eklendi!" : "Sepete Ekle")}
    </Button>
  );
}
