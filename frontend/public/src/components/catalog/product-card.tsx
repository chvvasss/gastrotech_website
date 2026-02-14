"use client";

import Link from "next/link";
import Image from "next/image";
import { Eye, ShoppingCart, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import { ProductListItem } from "@/lib/api/schemas";
import { getMediaUrl } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface ProductCardProps {
  product: ProductListItem;
  priority?: boolean;
}

export function ProductCard({ product, priority = false }: ProductCardProps) {
  const hasImage = !!product.primary_image_url;
  const productUrl = `/urun/${product.slug}`;

  return (
    <motion.article
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.3 }}
      className="group relative flex flex-col overflow-hidden rounded-sm border border-border bg-card transition-all duration-300 hover:shadow-xl hover:border-primary"
    >
      {/* Image Container */}
      <div className="relative aspect-[4/3] w-full overflow-hidden bg-muted block">
        <Link href={productUrl} className="absolute inset-0 z-0 h-full w-full block">
          {hasImage ? (
            <>
              <Image
                src={getMediaUrl(product.primary_image_url)}
                alt={product.title_tr || product.slug}
                fill
                sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
                className="object-cover transition-transform duration-500 group-hover:scale-105"
                priority={priority}
              />
              {/* Subtle Gradient Overlay on Hover for text contrast if needed */}
              <div className="absolute inset-0 bg-black/5 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
            </>
          ) : (
            /* Fallback Placeholder */
            <div className="flex h-full w-full flex-col items-center justify-center bg-secondary/10 p-6 text-muted-foreground/30">
              <span className="text-3xl font-bold">
                {(product.title_tr || product.slug || "P").charAt(0).toUpperCase()}
              </span>
            </div>
          )}
        </Link>

        {/* Badges - Red Emphasis */}
        <div className="pointer-events-none absolute left-2 top-2 z-10 flex flex-col gap-1.5">
          {product.is_featured && (
            <Badge variant="secondary" className="rounded-sm bg-primary text-white shadow-sm text-[10px] px-2 h-5 hover:bg-primary">
              Öne Çıkan
            </Badge>
          )}
        </div>

        {/* Quick Actions - Simple & Direct */}
        <div className="absolute bottom-2 right-2 z-20 flex gap-1.5 opacity-0 translate-y-2 transition-all duration-200 group-hover:opacity-100 group-hover:translate-y-0 pointer-events-auto">
          <Link
            href={productUrl}
            className="h-8 w-8 rounded-sm bg-white/90 shadow-sm hover:bg-white text-foreground hover:text-primary flex items-center justify-center"
            aria-label="Ürünü incele"
          >
            <Eye className="h-4 w-4" />
          </Link>
          <Link
            href={`${productUrl}#sepet`}
            className="h-8 w-8 rounded-sm shadow-sm bg-primary hover:bg-primary/90 text-white flex items-center justify-center"
            aria-label="Sepete ekle"
          >
            <ShoppingCart className="h-4 w-4" />
          </Link>
        </div>
      </div>

      {/* Content Section - Compact with Red Accents */}
      <div className="flex flex-1 flex-col p-3.5 group-hover:bg-primary/[0.02] transition-colors">
        {/* Brand & Series Info */}
        <div className="mb-1.5 flex items-center justify-between text-[10px] uppercase tracking-wider text-muted-foreground">
          <div className="flex items-center gap-1.5 truncate">
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {(product as any).brand_name && (
              <span className="font-bold text-primary/80 group-hover:text-primary">
                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                {(product as any).brand_name}
              </span>
            )}
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {(product as any).brand_name && <span className="text-muted-foreground/40">•</span>}
            <span className="truncate">{product.series_name}</span>
          </div>
        </div>

        {/* Product Title - Stronger Contrast */}
        <h3 className="mb-2 line-clamp-2 text-sm font-semibold leading-tight text-foreground transition-colors group-hover:text-primary">
          <Link href={productUrl} className="hover:underline">
            {product.title_tr || product.slug}
          </Link>
        </h3>

        {/* Footer: Variant Count & Link */}
        <div className="mt-auto flex items-center justify-between border-t border-border/50 pt-2.5 text-[11px] text-muted-foreground group-hover:border-primary/20">
          <span>
            {product.variants_count > 0 ? `${product.variants_count} seçenek` : ''}
          </span>
          <Link href={productUrl} className="flex items-center gap-1 font-medium text-primary hover:text-primary/80 transition-colors">
            İncele <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
      </div>
    </motion.article>
  );
}
