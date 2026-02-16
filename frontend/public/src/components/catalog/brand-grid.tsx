"use client";

import Image from "next/image";
import { Brand } from "@/lib/api/schemas";
import { getMediaUrl } from "@/lib/utils";
import { Package } from "lucide-react";

interface BrandGridProps {
    brands: Brand[];
    onSelect?: (brandSlug: string) => void;
    isLoading?: boolean;
}

export function BrandGrid({ brands, onSelect, isLoading = false }: BrandGridProps) {
    if (isLoading) {
        return (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="aspect-[4/3] animate-pulse rounded-sm bg-muted" />
                ))}
            </div>
        );
    }

    if (brands.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-12 text-center">
                <Package className="h-12 w-12 text-muted-foreground/20" />
                <p className="mt-4 text-sm text-muted-foreground">
                    Bu bölümde henüz marka bulunmuyor.
                </p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {brands.map((brand) => (
                <div
                    key={brand.id}
                    className="group cursor-pointer overflow-hidden rounded-sm border bg-card text-card-foreground shadow-sm transition-all hover:shadow-lg"
                    onClick={() => onSelect?.(brand.slug)}
                >
                    {/* Image / Logo Area */}
                    <div className="flex aspect-[4/3] items-center justify-center bg-muted/20 p-8 transition-colors group-hover:bg-muted/30">
                        {brand.logo_url ? (
                            <div className="relative h-full w-full">
                                <Image
                                    src={getMediaUrl(brand.logo_url)}
                                    alt={brand.name}
                                    fill
                                    className="object-contain transition-transform duration-300 group-hover:scale-110"
                                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                                />
                            </div>
                        ) : (
                            <span className="text-3xl font-bold text-muted-foreground/20 select-none">
                                {brand.name}
                            </span>
                        )}
                    </div>

                    {/* Content Area */}
                    <div className="p-6">
                        <h3 className="mb-2 text-xl font-bold tracking-tight text-foreground">
                            {brand.name}
                        </h3>

                        {brand.description && (
                            <p className="mb-4 line-clamp-2 text-sm text-muted-foreground">
                                {brand.description}
                            </p>
                        )}

                        <div className="flex items-center gap-1.5 text-sm font-medium text-primary transition-colors group-hover:text-primary/80">
                            Ürünleri Gör
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="16"
                                height="16"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className="transition-transform group-hover:translate-x-1"
                            >
                                <path d="M5 12h14" />
                                <path d="m12 5 7 7-7 7" />
                            </svg>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
