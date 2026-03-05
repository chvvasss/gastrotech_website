"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Grid3X3 } from "lucide-react";
import { NavCategory } from "@/lib/api/schemas";
import { cn } from "@/lib/utils";
import { ShowcaseCard } from "./category-grid";

/* ================================================================
   BentoCategoryGrid — Category/subcategory grid for listing pages
   Variants:
     "cinematic" — 3-col grid (used on /kategori page)
     "grid"      — 3-col lg, 4-col xl compact grid (subcategories)
     "bento"     — Same as cinematic (default)
   ================================================================ */

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
  const displayCategories = maxVisible
    ? categories.slice(0, maxVisible)
    : categories;
  const remainingCount = maxVisible
    ? categories.length - displayCategories.length
    : 0;

  const compact = variant === "grid";

  return (
    <div
      className={cn(
        "grid gap-2.5 sm:gap-4",
        compact
          ? "grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 lg:gap-4"
          : "grid-cols-2 lg:grid-cols-3 lg:gap-5"
      )}
    >
      {displayCategories.map((category, i) => (
        <motion.div
          key={category.id}
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-30px" }}
          transition={{ duration: 0.4, delay: Math.min(i * 0.05, 0.4) }}
        >
          <ShowcaseCard
            category={category}
            compact={compact}
            priority={i < 4}
          />
        </motion.div>
      ))}

      {showMoreCard && remainingCount > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{
            duration: 0.4,
            delay: Math.min(displayCategories.length * 0.05, 0.4),
          }}
        >
          <MoreCard remainingCount={remainingCount} compact={compact} />
        </motion.div>
      )}
    </div>
  );
}

/* ================================================================
   MoreCard — "See all categories" call-to-action
   ================================================================ */

function MoreCard({
  remainingCount,
  compact = false,
}: {
  remainingCount: number;
  compact?: boolean;
}) {
  return (
    <Link
      href="/kategori"
      className={cn(
        "group flex flex-col items-center justify-center h-full rounded-lg bg-zinc-50 border border-dashed border-zinc-200 hover:border-primary/40 hover:bg-primary/[0.03] transition-all",
        compact ? "aspect-[5/4] p-3" : "aspect-[4/3] p-4 sm:p-6"
      )}
    >
      <div className="w-9 h-9 sm:w-11 sm:h-11 rounded-full bg-primary/10 flex items-center justify-center mb-2 sm:mb-3 group-hover:scale-110 transition-transform">
        <Grid3X3 className="h-4 w-4 sm:h-5 sm:w-5 text-primary" />
      </div>
      <h3 className="font-semibold text-foreground text-xs sm:text-sm">
        Tümünü Gör
      </h3>
      <p className="text-[10px] sm:text-xs text-muted-foreground mt-0.5">
        +{remainingCount} kategori
      </p>
    </Link>
  );
}
