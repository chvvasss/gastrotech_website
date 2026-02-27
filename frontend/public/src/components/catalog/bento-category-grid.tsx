"use client";

import Link from "next/link";
import Image from "next/image";
import { motion, useMotionTemplate, useMotionValue } from "framer-motion";
import { Grid3X3, ChevronsRight, ArrowRight, Sparkles } from "lucide-react";
import { NavCategory } from "@/lib/api/schemas";
import { getMediaUrl, cn } from "@/lib/utils";

interface BentoCategoryGridProps {
    categories: NavCategory[];
    maxVisible?: number;
    showMoreCard?: boolean;
    variant?: "bento" | "grid" | "cinematic";
}

export function BentoCategoryGrid({
    categories,
    maxVisible,
    showMoreCard = false,
    variant = "bento",
}: BentoCategoryGridProps) {
    const displayCategories = maxVisible ? categories.slice(0, maxVisible) : categories;
    const remainingCount = categories.length - displayCategories.length;

    // Cinematic variant - Like homepage + wide bar + 3-col grid
    if (variant === "cinematic") {
        const topCategories = categories.slice(0, 5);     // First 5 for cinematic grid
        const wideCategory = categories[5];               // 6th for wide bar
        const bottomCategories = categories.slice(6);     // Rest for 3-col grid

        return (
            <div className="space-y-4 origin-top scale-[0.85]">
                {/* Cinematic 5-Grid (Tall Middle) */}
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3 md:grid-rows-2 auto-rows-[280px] md:h-[600px]">
                    {topCategories.map((category, index) => {
                        const gridClass = getCinematicGridClass(index);
                        return (
                            <motion.div
                                key={category.id}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.5, delay: index * 0.1 }}
                                className={cn("relative w-full h-full", gridClass)}
                            >
                                <CinematicCard category={category} isTall={index === 1} />
                            </motion.div>
                        );
                    })}
                </div>

                {/* Wide Bar */}
                {wideCategory && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5, delay: 0.3 }}
                    >
                        <WideCard category={wideCategory} />
                    </motion.div>
                )}

                {/* 3-Column Grid - Same cinematic style */}
                {bottomCategories.length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 auto-rows-[280px]">
                        {bottomCategories.map((category, index) => (
                            <motion.div
                                key={category.id}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.4, delay: index * 0.08 }}
                                className="h-full"
                            >
                                <CinematicCard category={category} />
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>
        );
    }

    // Grid variant - Balanced Brick Pattern
    if (variant === "grid") {
        return (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 auto-rows-[200px] md:auto-rows-[220px]">
                {categories.map((category, index) => {
                    const patternIndex = index % 6;
                    let spanClass = "col-span-1";
                    if (patternIndex === 0 || patternIndex === 5) {
                        spanClass += " sm:col-span-2 lg:col-span-2";
                    } else {
                        spanClass += " sm:col-span-1 lg:col-span-1";
                    }

                    return (
                        <motion.div
                            key={category.id}
                            initial={{ opacity: 0, scale: 0.98 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.4, delay: index * 0.05 }}
                            className={cn(spanClass, "group")}
                        >
                            <CatalogCard category={category} className="h-full" />
                        </motion.div>
                    );
                })}
            </div>
        );
    }

    // Bento variant for homepage
    const cat1 = displayCategories[0];
    const cat2 = displayCategories[1];
    const cat3 = displayCategories[2];
    const cat4 = displayCategories[3];
    const cat5 = displayCategories[4];

    return (
        <div className="mx-auto w-full">
            {/* Mobile: Horizontal Snap Scroll Carousel */}
            <div className="md:hidden overflow-hidden -mx-6">
                <div className="px-6 overflow-x-auto pb-6 scrollbar-hide snap-x snap-mandatory flex gap-4">
                    {categories.slice(0, 5).map((cat) => (
                        <div key={cat.id} className="snap-center shrink-0 w-[85vw] max-w-[320px]">
                            <LargeCard category={cat} height="h-[300px]" />
                        </div>
                    ))}
                    {showMoreCard && (
                        <div className="snap-center shrink-0 w-[150px]">
                            <MoreCard remainingCount={Math.max(0, categories.length - 5)} />
                        </div>
                    )}
                </div>
            </div>

            {/* Desktop: Bento Grid */}
            <div className="hidden md:grid grid-cols-3 grid-rows-2 gap-4 h-[520px]">
                <div className="col-span-1 row-span-2">
                    {cat1 ? <LargeCard category={cat1} /> : <div className="h-full min-h-[280px] rounded-sm bg-muted animate-pulse" />}
                </div>
                <div className="col-span-1 row-span-2">
                    {cat2 ? <LargeCard category={cat2} /> : <div className="h-full min-h-[280px] rounded-sm bg-muted animate-pulse" />}
                </div>
                <div className="col-span-1 row-span-2 flex flex-col gap-4 h-full">
                    <div className="flex-1 min-h-[120px]">
                        {cat3 ? <SmallCard category={cat3} /> : <div className="h-full rounded-sm bg-muted animate-pulse" />}
                    </div>
                    <div className="flex-1 min-h-[120px]">
                        {cat4 ? <SmallCard category={cat4} /> : <div className="h-full rounded-sm bg-muted/50" />}
                    </div>
                    <div className="flex-1 min-h-[120px]">
                        {showMoreCard && remainingCount > 0 ? (
                            <MoreCard remainingCount={remainingCount + (cat5 ? 1 : 0)} />
                        ) : cat5 ? (
                            <SmallCard category={cat5} />
                        ) : (
                            <div className="h-full rounded-sm bg-muted/50" />
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

/* ============================================
   HELPER FUNCTIONS
   ============================================ */
function getCinematicGridClass(index: number) {
    switch (index) {
        case 0: return "md:col-start-1 md:row-start-1 md:col-span-1 md:row-span-1";
        case 1: return "md:col-start-2 md:row-start-1 md:col-span-1 md:row-span-2 h-full"; // Tall
        case 2: return "md:col-start-1 md:row-start-2 md:col-span-1 md:row-span-1";
        case 3: return "md:col-start-3 md:row-start-1 md:col-span-1 md:row-span-1";
        case 4: return "md:col-start-3 md:row-start-2 md:col-span-1 md:row-span-1";
        default: return "col-span-1";
    }
}

/* ============================================
   CINEMATIC CARD (Like homepage)
   ============================================ */
function CinematicCard({ category, isTall }: { category: NavCategory; isTall?: boolean }) {
    const mouseX = useMotionValue(0);
    const mouseY = useMotionValue(0);

    function handleMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent) {
        const { left, top } = currentTarget.getBoundingClientRect();
        mouseX.set(clientX - left);
        mouseY.set(clientY - top);
    }

    return (
        <div
            className="group relative h-full w-full overflow-hidden rounded-sm bg-muted"
            onMouseMove={handleMouseMove}
        >
            <Link href={`/kategori/${category.slug}`} className="block h-full w-full">
                {/* Background Image */}
                <div className="absolute inset-0 transition-transform duration-700 ease-out group-hover:scale-110">
                    {category.cover_media_url ? (
                        <Image
                            src={getMediaUrl(category.cover_media_url)}
                            alt={category.name}
                            fill
                            className="object-cover"
                            sizes={isTall ? "(max-width: 768px) 100vw, 33vw" : "(max-width: 768px) 100vw, 33vw"}
                        />
                    ) : (
                        <div className="flex h-full w-full items-center justify-center bg-zinc-900">
                            <span className="text-9xl font-black text-white/5 opacity-50 select-none">
                                {category.name.charAt(0)}
                            </span>
                        </div>
                    )}
                </div>

                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-60 transition-opacity duration-300 group-hover:opacity-80" />

                {/* Spotlight Effect */}
                <motion.div
                    className="pointer-events-none absolute -inset-px opacity-0 transition duration-300 group-hover:opacity-100"
                    style={{
                        background: useMotionTemplate`
                            radial-gradient(
                                600px circle at ${mouseX}px ${mouseY}px,
                                rgba(255,255,255,0.1),
                                transparent 80%
                            )
                        `,
                    }}
                />

                {/* Content */}
                <div className="absolute inset-0 flex flex-col justify-end p-6">
                    {category.is_featured && (
                        <div className="absolute right-4 top-4 rounded-sm bg-white/20 px-3 py-1 text-xs font-semibold text-white backdrop-blur-md">
                            <Sparkles className="mr-1 inline-block h-3 w-3" />
                            Öne Çıkan
                        </div>
                    )}

                    <div className="transform transition-transform duration-300 group-hover:-translate-y-1">
                        <h3 className={cn(
                            "font-bold text-white leading-tight drop-shadow-md",
                            isTall ? "text-3xl md:text-4xl" : "text-xl md:text-2xl"
                        )}>
                            {category.menu_label || category.name}
                        </h3>

                        <div className="mt-3 flex items-center gap-2 opacity-0 transform translate-y-2 transition-all duration-300 group-hover:opacity-100 group-hover:translate-y-0 text-white/90 text-sm font-medium">
                            <span>İncele</span>
                            <ArrowRight className="h-4 w-4" />
                        </div>
                    </div>
                </div>
            </Link>
        </div>
    );
}

/* ============================================
   WIDE CARD (Full width bar)
   ============================================ */
function WideCard({ category }: { category: NavCategory }) {
    const mouseX = useMotionValue(0);
    const mouseY = useMotionValue(0);

    function handleMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent) {
        const { left, top } = currentTarget.getBoundingClientRect();
        mouseX.set(clientX - left);
        mouseY.set(clientY - top);
    }

    return (
        <div
            className="group relative h-[280px] md:h-[260px] w-full overflow-hidden rounded-sm bg-muted"
            onMouseMove={handleMouseMove}
        >
            <Link href={`/kategori/${category.slug}`} className="block h-full w-full">
                {/* Background Image */}
                <div className="absolute inset-0 transition-transform duration-700 ease-out group-hover:scale-105">
                    {category.cover_media_url ? (
                        <Image
                            src={getMediaUrl(category.cover_media_url)}
                            alt={category.name}
                            fill
                            className="object-cover"
                            sizes="100vw"
                        />
                    ) : (
                        <div className="flex h-full w-full items-center justify-center bg-zinc-900">
                            <span className="text-9xl font-black text-white/5 opacity-50 select-none">
                                {category.name.charAt(0)}
                            </span>
                        </div>
                    )}
                </div>

                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/50 to-transparent opacity-70 transition-opacity duration-300 group-hover:opacity-85" />

                {/* Spotlight Effect */}
                <motion.div
                    className="pointer-events-none absolute -inset-px opacity-0 transition duration-300 group-hover:opacity-100"
                    style={{
                        background: useMotionTemplate`
                            radial-gradient(
                                800px circle at ${mouseX}px ${mouseY}px,
                                rgba(255,255,255,0.08),
                                transparent 70%
                            )
                        `,
                    }}
                />

                {/* Content */}
                <div className="absolute inset-0 flex items-center p-8">
                    <div className="transform transition-transform duration-300 group-hover:translate-x-2">
                        <h3 className="text-2xl md:text-3xl font-bold text-white leading-tight drop-shadow-md">
                            {category.menu_label || category.name}
                        </h3>

                        {category.children && category.children.length > 0 && (
                            <p className="mt-1 text-sm text-white/60">
                                {category.children.length} alt kategori
                            </p>
                        )}

                        <div className="mt-3 flex items-center gap-2 text-white/90 text-sm font-medium">
                            <span>Ürünleri İncele</span>
                            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                        </div>
                    </div>
                </div>

                {/* Right side decorative accent */}
                <div className="absolute right-0 top-0 bottom-0 w-1 bg-primary opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </Link>
        </div>
    );
}



/* ============================================
   EXISTING CARDS (kept for bento/grid variants)
   ============================================ */
function CatalogCard({ category, className }: { category: NavCategory, className?: string }) {
    return (
        <Link
            href={`/kategori/${category.slug}`}
            className={cn(
                "group block bg-white border border-border/50 rounded-sm hover:border-primary/50 hover:shadow-md transition-all duration-300 overflow-hidden h-full flex flex-col",
                className
            )}
        >
            <div className="relative flex-1 bg-white p-4 min-h-[140px]">
                {category.cover_media_url ? (
                    <Image
                        src={getMediaUrl(category.cover_media_url)}
                        alt={category.name}
                        fill
                        className="object-contain p-2 transition-transform duration-500 group-hover:scale-105"
                        sizes="(max-width: 640px) 50vw, 25vw"
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center">
                        <span className="text-4xl font-black text-gray-100">
                            {category.name.charAt(0)}
                        </span>
                    </div>
                )}
            </div>

            <div className="px-4 py-3 border-t border-border/50 bg-muted/5">
                <div className="flex items-center justify-between gap-2">
                    <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide leading-tight">
                        {category.menu_label || category.name}
                    </h3>
                    <ChevronsRight
                        className="h-4 w-4 text-primary/50 flex-shrink-0 group-hover:text-primary group-hover:translate-x-1 transition-all"
                    />
                </div>
            </div>
        </Link>
    );
}

function LargeCard({ category, height = "h-full" }: { category: NavCategory, height?: string }) {
    return (
        <Link
            href={`/kategori/${category.slug}`}
            className={cn(
                "group relative flex flex-col overflow-hidden rounded-sm bg-white border border-border/40 hover:border-primary/50 transition-all hover:shadow-lg",
                height
            )}
        >
            <div className="absolute inset-0 bg-white p-6">
                {category.cover_media_url ? (
                    <Image
                        src={getMediaUrl(category.cover_media_url)}
                        alt={category.name}
                        fill
                        className="object-contain p-6 transition-transform duration-700 ease-out group-hover:scale-110"
                        sizes="(max-width: 768px) 100vw, 33vw"
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center bg-primary/5">
                        <span className="text-8xl font-black text-primary/10">{category.name.charAt(0)}</span>
                    </div>
                )}
            </div>

            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-60 group-hover:opacity-80 transition-opacity duration-300" />

            <div className="relative mt-auto p-6 text-white transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300">
                <h3 className="text-2xl font-bold leading-tight mb-2">{category.menu_label || category.name}</h3>
                <div className="flex items-center gap-2 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-300 -translate-x-4 group-hover:translate-x-0 delay-75">
                    <span>İncele</span>
                    <ArrowRight className="h-4 w-4" />
                </div>
            </div>
        </Link>
    );
}

function SmallCard({ category }: { category: NavCategory }) {
    return (
        <Link
            href={`/kategori/${category.slug}`}
            className="group relative flex flex-row items-center h-full overflow-hidden rounded-sm bg-white border border-border/40 hover:border-primary/50 transition-all hover:shadow-md"
        >
            <div className="relative w-1/3 h-full bg-white p-2">
                {category.cover_media_url ? (
                    <Image
                        src={getMediaUrl(category.cover_media_url)}
                        alt={category.name}
                        fill
                        className="object-contain p-1 transition-transform duration-500 group-hover:scale-110"
                        sizes="15vw"
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center bg-primary/5">
                        <span className="text-3xl font-black text-primary/10">{category.name.charAt(0)}</span>
                    </div>
                )}
            </div>

            <div className="flex-1 p-4 bg-muted/5 h-full flex items-center justify-between border-l border-border/50 group-hover:bg-primary/5 transition-colors">
                <h3 className="text-sm font-bold text-foreground group-hover:text-primary transition-colors pr-2">
                    {category.menu_label || category.name}
                </h3>
                <ChevronsRight
                    className="h-4 w-4 text-primary/30 flex-shrink-0 group-hover:text-primary group-hover:translate-x-1 transition-all"
                />
            </div>
        </Link>
    );
}

function MoreCard({ remainingCount }: { remainingCount: number }) {
    return (
        <Link
            href="/kategori"
            className="group flex flex-col items-center justify-center h-full rounded-sm bg-muted/20 border border-dashed border-border hover:border-primary/50 hover:bg-primary/5 transition-all p-6 text-center"
        >
            <div className="w-10 h-10 rounded-sm bg-primary/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <Grid3X3 className="h-5 w-5 text-primary" />
            </div>
            <h3 className="font-semibold text-foreground text-sm">Tümünü Gör</h3>
            <p className="text-xs text-muted-foreground mt-1">+{remainingCount} kategori</p>
        </Link>
    );
}
