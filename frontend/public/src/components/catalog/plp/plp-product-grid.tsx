"use client";

import Image from "next/image";
import Link from "next/link";
import { PLPProduct } from "@/lib/api/schemas";
import { getMediaUrl } from "@/lib/utils";
import { Package, Check } from "lucide-react";

interface PLPProductGridProps {
    products: PLPProduct[];
    isLoading?: boolean;
}

function PLPProductCard({ product }: { product: PLPProduct }) {
    return (
        <Link
            href={`/urun/${product.slug}`}
            className="group relative flex flex-col bg-white rounded-sm border border-border/40 hover:border-primary/50 hover:shadow-xl transition-all duration-300 overflow-hidden"
        >
            {/* Stock badge */}
            {product.in_stock && (
                <div className="absolute top-3 right-3 z-10">
                    <span className="inline-flex items-center rounded-sm bg-destructive text-white px-2 py-1 text-[10px] font-bold tracking-wider shadow-sm">
                        STOKTA
                    </span>
                </div>
            )}

            {/* Image Area */}
            <div className="relative aspect-square w-full bg-white p-4 group-hover:bg-[#fcfcfc] transition-colors duration-300">
                {product.hero_image_url ? (
                    <Image
                        src={getMediaUrl(product.hero_image_url)}
                        alt={product.title_tr ?? product.name}
                        fill
                        className="object-contain mix-blend-multiply transition-transform duration-500 group-hover:scale-105"
                        sizes="(max-width: 640px) 50vw, (max-width: 1024px) 25vw, 20vw"
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center">
                        <Package className="h-10 w-10 text-muted-foreground/20" />
                    </div>
                )}
            </div>

            {/* Content Area */}
            <div className="flex flex-1 flex-col p-4 pt-2 text-center">
                {/* Brand - Subtle Grey */}
                {product.brand && (
                    <span className="mb-1 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
                        {product.brand.name}
                    </span>
                )}

                {/* Title - BOLD and DISTINCT */}
                <h3 className="mb-2 line-clamp-2 text-sm font-bold leading-tight text-foreground min-h-[2.5em] group-hover:text-primary transition-colors">
                    {product.title_tr ?? product.name}
                </h3>

                {/* Separator - Red accent on hover */}
                <div className="w-12 h-0.5 bg-border mx-auto my-1.5 group-hover:bg-primary/20 transition-colors" />

                {/* Price hidden - Catalog mode always active */}
            </div>

            {/* Bottom Accent Bar - Removed per request */}
        </Link>
    );
}

export function PLPProductGrid({ products, isLoading = false }: PLPProductGridProps) {
    if (isLoading) {
        return (
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-4">
                {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="aspect-[3/5] rounded-sm bg-muted/10 animate-pulse" />
                ))}
            </div>
        );
    }

    if (products.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-24 text-center border rounded-sm border-dashed border-border bg-muted/5">
                <div className="h-16 w-16 mb-4 flex items-center justify-center bg-white rounded-full shadow-sm border border-border">
                    <Package className="h-8 w-8 text-primary/50" />
                </div>
                <h3 className="text-base font-bold text-foreground">
                    Ürün Bulunamadı
                </h3>
                <p className="mt-2 text-sm text-muted-foreground max-w-xs mx-auto">
                    Kriterlerinize uygun ürün bulunamadı. Filtreleri temizleyip tekrar deneyiniz.
                </p>
            </div>
        );
    }

    // Grid System
    return (
        <div className="grid grid-cols-1 gap-x-8 gap-y-12 sm:grid-cols-2 lg:grid-cols-3">
            {products.map((product) => (
                <PLPProductCard key={product.id} product={product} />
            ))}
        </div>
    );
}
