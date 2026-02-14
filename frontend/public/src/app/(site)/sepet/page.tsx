"use client";

import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Minus, Plus, Trash2, ShoppingBag, FileText, ArrowLeft, ArrowRight, Package, Shield, Truck } from "lucide-react";
import { Container } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useCart } from "@/hooks/use-cart";
import { useSiteSettings } from "@/hooks/use-site-settings";
import { formatPrice, cn } from "@/lib/utils";

const BENEFITS = [
  { icon: Shield, text: "2 Yıl Garanti" },
  { icon: Truck, text: "Ücretsiz Kurulum" },
];

export default function CartPage() {
  const { cart, isLoading, updateItem, removeItem, clear } = useCart();
  const { showPrices } = useSiteSettings();

  const items = cart?.items || [];
  const isEmpty = items.length === 0;

  if (isLoading) {
    return (
      <Container className="py-8 lg:py-12">
        <div className="mb-6 h-10 w-48 rounded animate-shimmer" />
        <div className="grid gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 w-full rounded-sm animate-shimmer" />
            ))}
          </div>
          <div className="h-64 rounded-sm animate-shimmer" />
        </div>
      </Container>
    );
  }

  return (
    <Container className="py-8 lg:py-12">
      {/* Breadcrumb */}
      <motion.nav 
        className="mb-6 text-sm text-muted-foreground"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Link href="/" className="hover:text-primary transition-colors">
          Ana Sayfa
        </Link>
        <span className="mx-2 text-primary/30">/</span>
        <span className="text-foreground font-medium">Sepet</span>
      </motion.nav>

      {/* Page Header */}
      <motion.div 
        className="mb-8 flex items-center justify-between"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-sm bg-primary/10">
            <ShoppingBag className="h-7 w-7 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold lg:text-3xl">Sepetim</h1>
            {!isEmpty && (
              <p className="text-muted-foreground">
                {cart?.totals?.line_count} ürün, {cart?.totals?.item_count} adet
              </p>
            )}
          </div>
        </div>
        {!isEmpty && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => clear()}
            className="text-muted-foreground hover:text-destructive hover:bg-destructive/10"
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Sepeti Temizle
          </Button>
        )}
      </motion.div>

      {isEmpty ? (
        <motion.div 
          className="flex flex-col items-center justify-center rounded-sm border-2 border-dashed bg-gradient-to-br from-muted/30 to-transparent py-20 text-center"
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
          <h2 className="mt-8 text-xl font-semibold">Sepetiniz Boş</h2>
          <p className="mt-2 max-w-sm text-muted-foreground">
            Henüz sepetinize ürün eklemediniz. Ürünlerimizi keşfederek alışverişe başlayın.
          </p>
          <Button 
            asChild 
            size="lg" 
            className="mt-8 shadow-lg shadow-primary/20"
          >
            <Link href="/urunler">
              Ürünleri Keşfet
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </motion.div>
      ) : (
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Cart Items */}
          <motion.div 
            className="lg:col-span-2"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="rounded-sm border bg-card shadow-soft overflow-hidden">
              <AnimatePresence initial={false}>
                {items.map((item, index) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -50 }}
                    transition={{ delay: index * 0.05, duration: 0.3 }}
                    className={cn(
                      "flex gap-4 p-5 sm:p-6",
                      index !== items.length - 1 && "border-b"
                    )}
                  >
                    {/* Product Image/Code */}
                    <div className="relative h-24 w-24 flex-shrink-0 overflow-hidden rounded-sm bg-gradient-to-br from-muted to-muted/50 sm:h-28 sm:w-28">
                      <div className="flex h-full w-full items-center justify-center text-base font-bold text-primary/70">
                        {item.variant.model_code.substring(0, 6)}
                      </div>
                      {/* Corner accent */}
                      <div className="absolute bottom-0 right-0 h-4 w-4 rounded-tl-lg bg-primary/20" />
                    </div>

                    {/* Product Info */}
                    <div className="flex flex-1 flex-col">
                      <div className="flex items-start justify-between">
                        <div>
                          <Link
                            href={`/urun/${item.variant.product_slug}`}
                            className="text-lg font-semibold hover:text-primary transition-colors"
                          >
                            {item.product_name_snapshot || item.variant.product_name}
                          </Link>
                          <p className="mt-1 text-sm text-muted-foreground">
                            Model: <span className="font-medium text-foreground">{item.variant_label_snapshot || item.variant.model_code}</span>
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-9 w-9 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                          onClick={() => removeItem(item.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>

                      <div className="mt-auto flex items-end justify-between pt-4">
                        {/* Quantity Stepper - Premium */}
                        <div className="flex items-center rounded-sm border-2 bg-muted/30 p-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className={cn(
                              "h-9 w-9 rounded-sm",
                              "hover:bg-primary/10 hover:text-primary",
                              "transition-colors"
                            )}
                            onClick={() => updateItem(item.id, item.quantity - 1)}
                            disabled={item.quantity <= 1}
                          >
                            <Minus className="h-4 w-4" />
                          </Button>
                          <motion.span 
                            key={item.quantity}
                            initial={{ scale: 1.2 }}
                            animate={{ scale: 1 }}
                            className="w-12 text-center text-lg font-bold"
                          >
                            {item.quantity}
                          </motion.span>
                          <Button
                            variant="ghost"
                            size="icon"
                            className={cn(
                              "h-9 w-9 rounded-sm",
                              "hover:bg-primary/10 hover:text-primary",
                              "transition-colors"
                            )}
                            onClick={() => updateItem(item.id, item.quantity + 1)}
                          >
                            <Plus className="h-4 w-4" />
                          </Button>
                        </div>

                        {/* Price */}
                        {showPrices && (
                          <div className="text-right">
                            <p className="text-xl font-bold text-foreground">
                              {formatPrice(
                                Number(item.unit_price_snapshot || 0) * item.quantity,
                                item.currency_snapshot
                              )}
                            </p>
                            {item.quantity > 1 && (
                              <p className="text-sm text-muted-foreground">
                                {formatPrice(item.unit_price_snapshot, item.currency_snapshot)} / adet
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>

            {/* Continue Shopping */}
            <motion.div 
              className="mt-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              <Button asChild variant="ghost" size="sm" className="hover:bg-primary/5">
                <Link href="/urunler">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Alışverişe Devam Et
                </Link>
              </Button>
            </motion.div>
          </motion.div>

          {/* Order Summary - Premium Sticky Card */}
          <motion.div 
            className="lg:col-span-1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            <div className="sticky top-24 rounded-sm border-2 bg-gradient-to-br from-card to-primary/5 p-6 shadow-soft">
              <h2 className="mb-5 flex items-center gap-2 text-lg font-bold">
                <div className="h-5 w-1.5 rounded-sm bg-primary" />
                Sepet Özeti
              </h2>

              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Ürün Sayısı</span>
                  <span className="font-medium">{cart?.totals?.line_count} ürün</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Toplam Adet</span>
                  <span className="font-medium">{cart?.totals?.item_count} adet</span>
                </div>
              </div>

              <Separator className="my-5 bg-primary/10" />

              {showPrices ? (
                <>
                  <div className="flex justify-between items-baseline">
                    <span className="text-lg font-semibold">Ara Toplam</span>
                    <span className="text-2xl font-bold text-primary">
                      {formatPrice(cart?.totals?.subtotal, cart?.currency)}
                    </span>
                  </div>

                  {cart?.totals?.has_pricing_gaps && (
                    <div className="mt-4 rounded-sm bg-amber-50 p-4 text-xs text-amber-700 border border-amber-200">
                      <span className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-sm bg-amber-500" />
                        Bazı ürünlerin fiyatı belirtilmemiştir. Teklif alırken kesinleşecektir.
                      </span>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-3">
                  <p className="text-muted-foreground text-sm">
                    Fiyat bilgisi için teklif alın
                  </p>
                </div>
              )}

              <p className="mt-4 rounded-sm bg-muted/50 p-3 text-xs text-muted-foreground">
                B2B sipariş sistemi: Sepetinizdeki ürünler için ekibimiz size özel teklif hazırlayacaktır.
              </p>

              <Separator className="my-5 bg-primary/10" />

              <Button 
                asChild 
                size="lg" 
                className="w-full shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30"
              >
                <Link href="/iletisim">
                  <FileText className="mr-2 h-5 w-5" />
                  Teklif Al
                </Link>
              </Button>

              <p className="mt-3 text-center text-xs text-muted-foreground">
                Teklif alma işlemi ücretsizdir
              </p>

              {/* Benefits */}
              <div className="mt-5 flex justify-center gap-4 border-t pt-5">
                {BENEFITS.map((benefit) => (
                  <div key={benefit.text} className="flex items-center gap-2 text-xs text-muted-foreground">
                    <benefit.icon className="h-4 w-4 text-primary" />
                    {benefit.text}
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </Container>
  );
}
