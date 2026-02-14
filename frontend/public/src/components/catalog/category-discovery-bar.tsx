"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { ChevronDown, ArrowRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { NavCategory } from "@/lib/api/schemas";
import { getMediaUrl } from "@/lib/utils";

interface CategoryDiscoveryBarProps {
    categories: NavCategory[];
}

export function CategoryDiscoveryBar({ categories }: CategoryDiscoveryBarProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    // Get remaining categories (after first 5 in main grid)
    const remainingCategories = categories.slice(5);
    const totalRemaining = remainingCategories.length;

    if (totalRemaining <= 0) return null;

    return (
        <div className="mt-10">
            {/* Toggle Button */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="group w-full flex items-center justify-center gap-3 py-4 px-6 bg-white border border-border rounded-sm transition-all duration-300 hover:border-primary/40 hover:shadow-md"
            >
                <span className="text-sm font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                    {isExpanded ? "Kategorileri Gizle" : `${totalRemaining} Kategori Daha`}
                </span>
                <motion.div
                    animate={{ rotate: isExpanded ? 180 : 0 }}
                    transition={{ duration: 0.3 }}
                >
                    <ChevronDown className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                </motion.div>
            </button>

            {/* Expandable Grid */}
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.4, ease: "easeInOut" }}
                        className="overflow-hidden"
                    >
                        <div className="pt-6 pb-2">
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                                {remainingCategories.map((category, index) => (
                                    <motion.div
                                        key={category.id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: index * 0.05 }}
                                    >
                                        <Link
                                            href={`/kategori/${category.slug}`}
                                            className="group/card flex flex-col items-center p-4 bg-white border border-border rounded-sm transition-all duration-300 hover:border-primary/40 hover:shadow-lg hover:-translate-y-1"
                                        >
                                            {/* Category Image */}
                                            <div className="relative h-16 w-16 mb-3 rounded-sm overflow-hidden bg-muted">
                                                {category.cover_media_url ? (
                                                    <Image
                                                        src={getMediaUrl(category.cover_media_url)}
                                                        alt={category.name}
                                                        fill
                                                        className="object-cover transition-transform duration-300 group-hover/card:scale-110"
                                                    />
                                                ) : (
                                                    <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-zinc-100 to-zinc-200 text-lg font-bold text-muted-foreground">
                                                        {category.name.charAt(0)}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Category Name */}
                                            <span className="text-sm font-medium text-center text-foreground group-hover/card:text-primary transition-colors line-clamp-2">
                                                {category.name}
                                            </span>
                                        </Link>
                                    </motion.div>
                                ))}
                            </div>

                            {/* View All Link */}
                            <div className="mt-6 text-center">
                                <Link
                                    href="/kategori"
                                    className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:text-primary/80 transition-colors"
                                >
                                    Tüm Kategorileri Görüntüle
                                    <ArrowRight className="h-4 w-4" />
                                </Link>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
