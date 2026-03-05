"use client";

import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles, ChevronRight } from "lucide-react";
import { NavCategory } from "@/lib/api/schemas";
import { getMediaUrl, cn, hexToRgb } from "@/lib/utils";

interface CategoryGridProps {
  categories: NavCategory[];
}

export function CategoryGrid({ categories }: CategoryGridProps) {
  const mainCategories = categories.slice(0, 5);
  const otherCategories = categories.slice(5);

  const getGridClass = (index: number) => {
    switch (index) {
      case 0: return "md:col-start-1 md:row-start-1 md:col-span-1 md:row-span-1";
      case 1: return "md:col-start-2 md:row-start-1 md:col-span-1 md:row-span-2 h-full";
      case 2: return "md:col-start-1 md:row-start-2 md:col-span-1 md:row-span-1";
      case 3: return "md:col-start-3 md:row-start-1 md:col-span-1 md:row-span-1";
      case 4: return "md:col-start-3 md:row-start-2 md:col-span-1 md:row-span-1";
      default: return "col-span-1";
    }
  };

  return (
    <div className="space-y-3">
      {/* Main Cinematic 5-Grid */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 md:grid-rows-2 md:gap-4 auto-rows-[180px] sm:auto-rows-[220px] md:h-[540px]">
        {mainCategories.map((category, index) => (
          <div key={category.id} className={cn("relative w-full h-full", getGridClass(index))}>
            <CategoryCard
              category={category}
              index={index}
              isTall={index === 1}
            />
          </div>
        ))}
      </div>

      {/* Other Categories CTA Bar */}
      {otherCategories.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
        >
          <Link
            href="/kategori"
            className="group flex items-center justify-between px-5 py-4 sm:px-8 sm:py-5 bg-zinc-900 hover:bg-zinc-800 rounded-lg transition-all duration-300 overflow-hidden relative"
          >
            {/* Accent gradient on hover */}
            <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            <div className="flex items-center gap-3 relative z-10">
              <div className="h-7 sm:h-8 w-1 bg-primary rounded-full" />
              <span className="text-white font-semibold text-sm sm:text-base">Diğer Kategorileri Gör</span>
              <span className="text-white/40 text-xs sm:text-sm">({otherCategories.length} kategori)</span>
            </div>
            <ArrowRight className="h-4 w-4 sm:h-5 sm:w-5 text-primary group-hover:translate-x-1 transition-transform relative z-10" />
          </Link>
        </motion.div>
      )}
    </div>
  );
}

function CategoryCard({ category, index, isTall }: { category: NavCategory; index: number; isTall?: boolean }) {
  const accentRgb = category.shadow_color ? hexToRgb(category.shadow_color) : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="category-card group relative h-full w-full overflow-hidden rounded-lg bg-white"
      style={accentRgb ? { '--card-accent': accentRgb } as React.CSSProperties : undefined}
    >
      <Link href={`/kategori/${category.slug}`} className="block h-full w-full">
        {/* Subtle radial gradient background for depth */}
        <div className="absolute inset-0 bg-gradient-to-br from-zinc-50/80 via-white to-zinc-50/40" />

        {/* Product Image */}
        <div className="absolute inset-0 flex items-center justify-center transition-transform duration-700 ease-out group-hover:scale-[1.03]">
          {category.cover_media_url ? (
            <Image
              src={getMediaUrl(category.cover_media_url)}
              alt={category.name}
              fill
              className="object-contain p-4 sm:p-6"
              sizes={isTall ? "(max-width: 768px) 50vw, 33vw" : "(max-width: 768px) 50vw, 25vw"}
            />
          ) : (
            <span className="text-7xl font-black text-zinc-100 select-none">
              {category.name.charAt(0)}
            </span>
          )}
        </div>

        {/* White gradient for text readability */}
        <div className="absolute inset-x-0 bottom-0 h-2/5 bg-gradient-to-t from-white via-white/85 to-transparent pointer-events-none" />

        {/* Subtle color wash */}
        {accentRgb && (
          <div
            className="absolute inset-x-0 bottom-0 h-1/3 pointer-events-none opacity-[0.06] group-hover:opacity-[0.12] transition-opacity duration-500"
            style={{ background: 'linear-gradient(to top, rgb(var(--card-accent)), transparent)' }}
          />
        )}

        {/* Content */}
        <div className="absolute inset-0 flex flex-col justify-end p-3 sm:p-4 md:p-5 z-10">
          {category.is_featured && (
            <div className="absolute right-3 top-3 sm:right-4 sm:top-4 rounded-md px-2.5 py-0.5 sm:px-3 sm:py-1 text-[9px] sm:text-xs font-semibold bg-primary/10 text-primary backdrop-blur-sm">
              <Sparkles className="mr-0.5 sm:mr-1 inline-block h-2.5 w-2.5 sm:h-3 sm:w-3" />
              Öne Çıkan
            </div>
          )}

          <div className="transform transition-transform duration-300 group-hover:-translate-y-1">
            <h3 className={cn(
              "font-bold leading-tight tracking-tight text-foreground",
              isTall ? "text-base sm:text-xl md:text-3xl" : "text-sm sm:text-base md:text-xl"
            )}>
              {category.menu_label || category.name}
            </h3>

            {/* Desktop: slide-in label */}
            <div className="mt-1 sm:mt-2 hidden sm:flex items-center gap-2 opacity-0 translate-y-2 transition-all duration-300 group-hover:opacity-100 group-hover:translate-y-0 text-sm font-medium text-primary">
              <span>İncele</span>
              <ArrowRight className="h-4 w-4" />
            </div>

            {/* Mobile: always-visible small arrow */}
            <div className="mt-0.5 flex sm:hidden items-center gap-1 text-xs text-muted-foreground">
              <ChevronRight className="h-3.5 w-3.5" />
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
