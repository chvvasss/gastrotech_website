"use client";

import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { NavCategory } from "@/lib/api/schemas";
import { getMediaUrl, cn, hexToRgb } from "@/lib/utils";

/* ================================================================
   CategoryGrid — Homepage showcase (max 6 categories + CTA bar)
   ================================================================ */

interface CategoryGridProps {
  categories: NavCategory[];
}

export function CategoryGrid({ categories }: CategoryGridProps) {
  const visible = categories.slice(0, 6);
  const remaining = categories.length - visible.length;

  return (
    <div className="space-y-3 sm:space-y-4">
      <div className="grid grid-cols-2 gap-2.5 sm:gap-4 lg:grid-cols-3 lg:gap-5">
        {visible.map((category, i) => (
          <motion.div
            key={category.id}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ duration: 0.45, delay: i * 0.06 }}
          >
            <ShowcaseCard category={category} priority={i < 3} />
          </motion.div>
        ))}
      </div>

      {remaining > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, delay: 0.25 }}
        >
          <Link
            href="/kategori"
            className="group flex items-center justify-between px-4 py-3.5 sm:px-6 sm:py-5 bg-zinc-900 hover:bg-zinc-800 rounded-lg transition-colors"
          >
            <div className="flex items-center gap-2.5">
              <div className="h-5 w-[3px] bg-primary rounded-full" />
              <span className="text-white font-semibold text-sm sm:text-base">
                Tüm Kategoriler
              </span>
              <span className="text-white/40 text-xs">+{remaining}</span>
            </div>
            <ArrowRight className="h-4 w-4 text-primary group-hover:translate-x-1 transition-transform" />
          </Link>
        </motion.div>
      )}
    </div>
  );
}

/* ================================================================
   ShowcaseCard — Unified category card (exported for reuse)
   ================================================================ */

interface ShowcaseCardProps {
  category: NavCategory;
  priority?: boolean;
  compact?: boolean;
}

export function ShowcaseCard({
  category,
  priority = false,
  compact = false,
}: ShowcaseCardProps) {
  const accentRgb = category.shadow_color
    ? hexToRgb(category.shadow_color)
    : null;
  const seriesCount =
    category.visible_series?.length || category.series?.length || 0;
  const childCount = category.children?.length || 0;
  const subtitle =
    seriesCount > 0
      ? `${seriesCount} ürün serisi`
      : childCount > 0
        ? `${childCount} alt kategori`
        : null;

  return (
    <Link
      href={`/kategori/${category.slug}`}
      className="category-card group flex flex-col h-full rounded-lg overflow-hidden bg-white"
      style={
        accentRgb
          ? ({ "--card-accent": accentRgb } as React.CSSProperties)
          : undefined
      }
    >
      {/* ── Image Area ── */}
      <div
        className={cn(
          "relative overflow-hidden",
          compact ? "aspect-[5/4]" : "aspect-[4/3]"
        )}
      >
        {/* Radial gradient background — subtle accent tint when available */}
        <div
          className="absolute inset-0"
          style={{
            background: accentRgb
              ? `radial-gradient(ellipse at 50% 35%, rgb(${accentRgb} / 0.04) 0%, #fafaf9 55%, #f3f3f2 100%)`
              : "radial-gradient(ellipse at 50% 35%, #fafafa 0%, #f5f5f4 55%, #f0f0ee 100%)",
          }}
        />

        {category.cover_media_url ? (
          <Image
            src={getMediaUrl(category.cover_media_url)}
            alt={category.name}
            fill
            priority={priority}
            className={cn(
              "object-contain relative z-[1] transition-transform duration-700 ease-out group-hover:scale-[1.06]",
              compact ? "p-3 sm:p-5 lg:p-6" : "p-4 sm:p-6 lg:p-8"
            )}
            sizes={
              compact
                ? "(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
                : "(max-width: 640px) 50vw, (max-width: 1024px) 50vw, 33vw"
            }
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center z-[1]">
            <span
              className={cn(
                "font-black text-zinc-200/60 select-none",
                compact ? "text-3xl sm:text-5xl" : "text-4xl sm:text-6xl"
              )}
            >
              {category.name.charAt(0)}
            </span>
          </div>
        )}

        {category.is_featured && (
          <div className="absolute top-2 right-2 sm:top-3 sm:right-3 z-[2] bg-primary text-white text-[10px] sm:text-xs font-semibold px-2 py-0.5 sm:px-2.5 sm:py-1 rounded-full">
            Öne Çıkan
          </div>
        )}
      </div>

      {/* ── Info Section ── */}
      <div className="relative flex items-center gap-2 px-3 py-2 sm:px-4 sm:py-3 border-t border-zinc-100/80 bg-white">
        {/* Accent side bar */}
        <div className="accent-bar absolute left-0 top-2 bottom-2 w-[3px] rounded-r-full" />

        <div className="flex-1 min-w-0 pl-1.5 sm:pl-2">
          <h3
            className={cn(
              "font-bold text-foreground leading-tight truncate",
              compact
                ? "text-[11px] sm:text-xs lg:text-sm"
                : "text-xs sm:text-sm lg:text-[15px]"
            )}
          >
            {category.menu_label || category.name}
          </h3>
          {subtitle && (
            <span className="text-[10px] sm:text-[11px] text-muted-foreground/60 leading-none mt-0.5 hidden sm:block">
              {subtitle}
            </span>
          )}
        </div>

        <ArrowRight className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-muted-foreground/30 group-hover:text-primary group-hover:translate-x-0.5 transition-all duration-300 shrink-0" />
      </div>
    </Link>
  );
}
