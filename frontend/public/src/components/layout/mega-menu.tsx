"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { NavCategory } from "@/lib/api/schemas";
import { getMediaUrl } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ArrowRight, Sparkles } from "lucide-react";
import { Container } from "@/components/layout/container";
import { motion } from "framer-motion";

interface MegaMenuPanelProps {
  categories: NavCategory[];
  position: { top: number; left: number; width: number };
  onClose: () => void;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}

export function MegaMenuPanel({
  categories,
  position,
  onClose,
  onMouseEnter,
  onMouseLeave,
}: MegaMenuPanelProps) {
  const [maxHeight, setMaxHeight] = useState(600);

  useEffect(() => {
    const calculateHeight = () => {
      const viewportHeight = window.innerHeight;
      const availableHeight = viewportHeight - position.top - 16;
      setMaxHeight(Math.max(400, Math.min(availableHeight, viewportHeight * 0.9)));
    };

    calculateHeight();
    window.addEventListener("resize", calculateHeight);
    return () => window.removeEventListener("resize", calculateHeight);
  }, [position.top]);

  return (
    <motion.div
      className="fixed left-0 right-0 z-[100] border-t bg-white/95 shadow-xl backdrop-blur-md will-change-transform"
      style={{ top: position.top }}
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -5 }}
      transition={{ duration: 0.15, ease: "easeOut" }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <ScrollArea className="w-full" style={{ maxHeight }}>
        <Container className="py-4">
          {/* Header Row */}
          <div className="mb-4 flex items-center justify-between border-b border-border/40 pb-2">
            <h3 className="text-lg font-bold tracking-tight text-foreground">Ürün Kategorileri</h3>
            <Link
              href="/kategori"
              onClick={onClose}
              className="group flex items-center gap-1 text-sm font-medium text-primary hover:text-primary/80"
            >
              Tümünü Gör
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </div>

          {/* Categories Grid - Rich Visual List */}
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-5">
            {categories.map((category) => (
              <Link
                key={category.id}
                href={`/kategori/${category.slug}`}
                onClick={onClose}
                className="group flex items-start gap-3 rounded-sm border border-transparent p-2 transition-all hover:bg-muted/50 hover:border-border/50 hover:shadow-sm"
              >
                {/* Larger Thumbnail (80px) */}
                <div className="relative h-20 w-20 shrink-0 overflow-hidden rounded-sm bg-white shadow-sm border border-border/20">
                  {category.cover_media_url ? (
                    <Image
                      src={getMediaUrl(category.cover_media_url)}
                      alt={category.name}
                      fill
                      className="object-cover transition-transform duration-500 group-hover:scale-110 transform-gpu"
                      sizes="80px"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center bg-muted/30 text-muted-foreground">
                      <span className="text-xl font-bold opacity-30">{category.name.charAt(0)}</span>
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="flex min-w-0 flex-1 flex-col justify-center gap-1.5 py-1">
                  <div className="flex items-start gap-1.5">
                    <span className="line-clamp-2 text-sm font-semibold leading-tight text-foreground group-hover:text-primary">
                      {category.menu_label || category.name}
                    </span>
                    {category.is_featured && (
                      <Sparkles className="h-3 w-3 shrink-0 text-amber-500 fill-amber-500 mt-0.5" />
                    )}
                  </div>

                  {category.series.length > 0 ? (
                    <span className="line-clamp-2 text-[11px] text-muted-foreground leading-relaxed group-hover:text-muted-foreground/80">
                      {category.series.slice(0, 3).map(s => s.name).join(", ")}
                    </span>
                  ) : (
                    <span className="text-[11px] text-muted-foreground font-medium opacity-60 group-hover:opacity-100 group-hover:text-primary/70 transition-all">
                      Ürünleri İncele
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>

          {/* Footer Compact */}
          <div className="mt-4 flex items-center justify-between rounded-sm bg-muted/30 px-4 py-3">
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium">Proje Hizmetlerimiz</span>
              <span className="hidden text-xs text-muted-foreground sm:inline">360° endüstriyel mutfak çözümleri.</span>
            </div>
            <div className="flex gap-2">
              <Link href="/referanslar" onClick={onClose}>
                <span className="text-xs font-medium hover:underline hover:text-primary">Referanslar</span>
              </Link>
              <div className="h-4 w-px bg-border/50" />
              <Link href="/iletisim" onClick={onClose}>
                <span className="text-xs font-medium hover:underline hover:text-primary">Teklif Al</span>
              </Link>
            </div>
          </div>
        </Container>
      </ScrollArea>
    </motion.div>
  );
}

export { MegaMenuPanel as MegaMenu };
