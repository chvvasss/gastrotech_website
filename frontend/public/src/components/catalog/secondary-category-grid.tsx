"use client";

import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { ChevronRight } from "lucide-react";
import { NavCategory } from "@/lib/api/schemas";
import { getMediaUrl } from "@/lib/utils";

interface SecondaryCategoryGridProps {
    categories: NavCategory[];
}

export function SecondaryCategoryGrid({ categories }: SecondaryCategoryGridProps) {
    if (!categories.length) return null;

    return (
        <div className="mt-8 grid grid-cols-2 gap-2 sm:gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {categories.map((category, index) => (
                <motion.div
                    key={category.id}
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                >
                    <Link
                        href={`/kategori/${category.slug}`}
                        className="group flex items-center h-14 sm:h-20 bg-white border border-border/50 rounded-sm hover:border-primary/50 transition-all overflow-hidden"
                    >
                        {/* Image Section */}
                        <div className="relative w-14 sm:w-20 h-full bg-muted/5 border-r border-border/50 p-1 sm:p-2 shrink-0">
                            {category.cover_media_url ? (
                                <Image
                                    src={getMediaUrl(category.cover_media_url)}
                                    alt={category.name}
                                    fill
                                    className="object-contain p-0.5 sm:p-1 transition-transform duration-300 group-hover:scale-110"
                                    sizes="(max-width: 640px) 56px, 80px"
                                />
                            ) : (
                                <div className="flex h-full w-full items-center justify-center bg-gray-50">
                                    <span className="text-base sm:text-xl font-bold text-gray-200">
                                        {category.name.charAt(0)}
                                    </span>
                                </div>
                            )}
                        </div>

                        {/* Content Section */}
                        <div className="flex-1 px-2 sm:px-4 py-1 sm:py-2 min-w-0 flex justify-between items-center bg-white/50 group-hover:bg-primary/5 h-full transition-colors">
                            <span className="text-[11px] sm:text-sm font-semibold text-foreground group-hover:text-primary truncate pr-1 sm:pr-2 transition-colors">
                                {category.menu_label || category.name}
                            </span>
                            <ChevronRight className="w-3 h-3 sm:w-4 sm:h-4 text-muted-foreground/50 group-hover:text-primary transition-all group-hover:translate-x-1 shrink-0" />
                        </div>
                    </Link>
                </motion.div>
            ))}
        </div>
    );
}
