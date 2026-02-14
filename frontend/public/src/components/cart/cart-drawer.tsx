"use client";

import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Minus, Plus, Trash2, ShoppingBag, FileText, ArrowRight, Package } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useCart } from "@/hooks/use-cart";
import { useSiteSettings } from "@/hooks/use-site-settings";
import { formatPrice, cn } from "@/lib/utils";

interface CartDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CartDrawer({ open, onOpenChange }: CartDrawerProps) {
  const { cart, isLoading, updateItem, removeItem } = useCart();
  const { showPrices } = useSiteSettings();

  const items = cart?.items || [];
  const isEmpty = items.length === 0;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex w-full flex-col sm:max-w-lg border-l-primary/10 bg-gradient-to-b from-background to-muted/30">
        <SheetHeader className="pb-4 border-b">
          <SheetTitle className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-primary/10">
              <ShoppingBag className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1">
              <span className="text-lg font-semibold">Sepetim</span>
              {!isEmpty && (
                <span className="ml-2 inline-flex items-center justify-center rounded-sm bg-primary px-2 py-0.5 text-xs font-bold text-primary-foreground">
                  {cart?.totals?.item_count || 0}
                </span>
              )}
            </div>
          </SheetTitle>
        </SheetHeader>

        {isLoading ? (
          <div className="flex-1 space-y-4 py-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex gap-4 rounded-sm bg-muted/50 p-4 animate-pulse">
                <div className="h-16 w-16 rounded-sm bg-muted" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-3/4 rounded bg-muted" />
                  <div className="h-3 w-1/2 rounded bg-muted" />
                  <div className="h-8 w-24 rounded bg-muted" />
                </div>
              </div>
            ))}
          </div>
        ) : isEmpty ? (
          <motion.div 
            className="flex flex-1 flex-col items-center justify-center gap-6 py-12"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <div className="relative">
              <div className="rounded-sm bg-gradient-to-br from-muted to-muted/50 p-8">
                <Package className="h-16 w-16 text-muted-foreground/30" />
              </div>
              <div className="absolute -bottom-2 -right-2 rounded-sm bg-primary/10 p-2">
                <ShoppingBag className="h-6 w-6 text-primary/50" />
              </div>
            </div>
            <div className="text-center">
              <h3 className="text-lg font-semibold">Sepetiniz Boş</h3>
              <p className="mt-2 max-w-[200px] text-sm text-muted-foreground">
                Ürün ekleyerek profesyonel mutfağınızı oluşturun
              </p>
            </div>
            <Button 
              asChild 
              size="lg"
              className="shadow-md shadow-primary/20"
              onClick={() => onOpenChange(false)}
            >
              <Link href="/urunler">
                Ürünlere Göz At
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </motion.div>
        ) : (
          <>
            <ScrollArea className="flex-1 -mx-6 px-6">
              <div className="space-y-3 py-4">
                <AnimatePresence initial={false}>
                  {items.map((item, index) => (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ delay: index * 0.05, duration: 0.3 }}
                      className={cn(
                        "flex gap-4 rounded-sm border bg-card p-4",
                        "shadow-soft hover:shadow-md",
                        "transition-all duration-200"
                      )}
                    >
                      {/* Product Image/Code */}
                      <div className="relative h-16 w-16 flex-shrink-0 overflow-hidden rounded-sm bg-gradient-to-br from-muted to-muted/50">
                        <div className="flex h-full w-full items-center justify-center text-xs font-bold text-primary/70">
                          {item.variant.model_code.substring(0, 4)}
                        </div>
                        {/* Corner accent */}
                        <div className="absolute bottom-0 right-0 h-3 w-3 rounded-tl-lg bg-primary/20" />
                      </div>

                      {/* Product Info */}
                      <div className="flex flex-1 flex-col justify-between min-w-0">
                        <div>
                          <Link
                            href={`/urun/${item.variant.product_slug}`}
                            onClick={() => onOpenChange(false)}
                            className="line-clamp-1 text-sm font-semibold transition-colors hover:text-primary"
                          >
                            {item.product_name_snapshot || item.variant.product_name}
                          </Link>
                          <p className="text-xs text-muted-foreground">
                            Model: {item.variant_label_snapshot || item.variant.model_code}
                          </p>
                        </div>

                        <div className="flex items-center justify-between mt-3">
                          {/* Quantity Stepper - Premium */}
                          <div className="flex items-center rounded-sm border bg-muted/50 p-0.5">
                            <Button
                              variant="ghost"
                              size="icon"
                              className={cn(
                                "h-7 w-7 rounded-sm",
                                "hover:bg-primary/10 hover:text-primary",
                                "transition-colors"
                              )}
                              onClick={() => updateItem(item.id, item.quantity - 1)}
                              disabled={item.quantity <= 1}
                            >
                              <Minus className="h-3 w-3" />
                            </Button>
                            <motion.span 
                              key={item.quantity}
                              initial={{ scale: 1.2 }}
                              animate={{ scale: 1 }}
                              className="w-8 text-center text-sm font-bold text-foreground"
                            >
                              {item.quantity}
                            </motion.span>
                            <Button
                              variant="ghost"
                              size="icon"
                              className={cn(
                                "h-7 w-7 rounded-sm",
                                "hover:bg-primary/10 hover:text-primary",
                                "transition-colors"
                              )}
                              onClick={() => updateItem(item.id, item.quantity + 1)}
                            >
                              <Plus className="h-3 w-3" />
                            </Button>
                          </div>

                          {/* Remove Button */}
                          <Button
                            variant="ghost"
                            size="icon"
                            className={cn(
                              "h-8 w-8 text-muted-foreground",
                              "hover:text-destructive hover:bg-destructive/10",
                              "transition-all"
                            )}
                            onClick={() => removeItem(item.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      {/* Price */}
                      {showPrices && (
                        <div className="text-right flex flex-col justify-between">
                          <p className="text-base font-bold text-foreground">
                            {formatPrice(
                              Number(item.unit_price_snapshot || 0) * item.quantity,
                              item.currency_snapshot
                            )}
                          </p>
                          {item.quantity > 1 && (
                            <p className="text-[11px] text-muted-foreground">
                              {formatPrice(item.unit_price_snapshot, item.currency_snapshot)}/ad
                            </p>
                          )}
                        </div>
                      )}
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </ScrollArea>

            <Separator className="bg-primary/10" />

            {/* Cart Summary - Premium styling */}
            <div className="rounded-sm bg-gradient-to-br from-muted/50 to-transparent p-4 mt-4">
              <div className="flex justify-between text-sm mb-3">
                <span className="text-muted-foreground">
                  {cart?.totals?.line_count} ürün ({cart?.totals?.item_count} adet)
                </span>
              </div>

              {showPrices && (
                <div className="flex justify-between items-baseline">
                  <span className="font-medium">Toplam</span>
                  <div className="text-right">
                    <span className="text-2xl font-bold text-primary">
                      {formatPrice(cart?.totals?.subtotal, cart?.currency)}
                    </span>
                  </div>
                </div>
              )}

              {!showPrices && (
                <p className="text-sm text-muted-foreground text-center py-2">
                  Fiyat bilgisi için teklif alın
                </p>
              )}

              {showPrices && cart?.totals?.has_pricing_gaps && (
                <p className="mt-3 text-xs text-amber-600 flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-sm bg-amber-500" />
                  Bazı ürünlerin fiyatı teklif ile kesinleşecektir.
                </p>
              )}
            </div>

            <SheetFooter className="flex-col gap-2 pt-4 sm:flex-col">
              <Button 
                asChild 
                className="w-full shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30" 
                size="lg"
              >
                <Link href="/iletisim" onClick={() => onOpenChange(false)}>
                  <FileText className="mr-2 h-5 w-5" />
                  Teklif Al
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                className="w-full border-primary/20 hover:border-primary/40 hover:bg-primary/5"
                size="lg"
              >
                <Link href="/sepet" onClick={() => onOpenChange(false)}>
                  Sepeti Görüntüle
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </SheetFooter>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
