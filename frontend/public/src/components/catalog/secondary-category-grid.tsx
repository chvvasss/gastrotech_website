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
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
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
                        className="group flex items-center h-20 bg-white border border-border/50 rounded-sm hover:border-primary/50 hover:shadow-sm transition-all overflow-hidden"
                    >
                        {/* Image Section */}
                        <div className="relative w-20 h-full bg-muted/5 border-r border-border/50 p-2 shrink-0">
                            {category.cover_media_url ? (
                                <Image
                                    src={getMediaUrl(category.cover_media_url)}
                                    alt={category.name}
                                    fill
                                    className="object-contain p-1 transition-transform duration-300 group-hover:scale-110"
                                    sizes="80px"
                                />
                            ) : (
                                <div className="flex h-full w-full items-center justify-center bg-gray-50">
                                    <span className="text-xl font-bold text-gray-200">
                                        {category.name.charAt(0)}
                                    </span>
                                </div>
                            )}
                        </div>

                        {/* Content Section */}
                        <div className="flex-1 px-4 py-2 min-w-0 flex justify-between items-center bg-white/50 group-hover:bg-primary/5 h-full transition-colors">
                            <span className="text-sm font-semibold text-foreground group-hover:text-primary truncate pr-2 transition-colors">
                                {category.menu_label || category.name}
                            </span>
                            <ChevronRight className="w-4 h-4 text-muted-foreground/50 group-hover:text-primary transition-all group-hover:translate-x-1 shrink-0" />
                        </div>
                    </Link>
                </motion.div>
            ))}
        </div>
    );
}
