"use client";

import Link from "next/link";
import Image from "next/image";
import { motion, useMotionTemplate, useMotionValue } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { NavCategory } from "@/lib/api/schemas";
import { getMediaUrl, cn } from "@/lib/utils";

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
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3 md:grid-rows-2 auto-rows-[220px] md:h-[500px]">
        {mainCategories.map((category, index) => (
          <div key={category.id} className={cn("relative w-full h-full", getGridClass(index))}>
            <ModernCategoryCard
              category={category}
              index={index}
              isTall={index === 1}
            />
          </div>
        ))}
      </div>

      {/* Other Categories - Single CTA Bar */}
      {otherCategories.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
        >
          <Link
            href="/kategori"
            className="group flex items-center justify-between px-8 py-6 bg-zinc-900 hover:bg-zinc-800 rounded-sm transition-all duration-300"
          >
            <div className="flex items-center gap-3">
              <div className="h-8 w-1 bg-primary rounded-sm" />
              <span className="text-white font-semibold">Diğer Kategorileri Gör</span>
              <span className="text-white/50 text-sm">({otherCategories.length} kategori)</span>
            </div>
            <ArrowRight className="h-5 w-5 text-primary group-hover:translate-x-1 transition-transform" />
          </Link>
        </motion.div>
      )}
    </div>
  );
}

function ModernCategoryCard({ category, index, isTall }: { category: NavCategory; index: number; isTall?: boolean }) {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  function handleMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent) {
    const { left, top } = currentTarget.getBoundingClientRect();
    mouseX.set(clientX - left);
    mouseY.set(clientY - top);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
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
              sizes={isTall ? "(max-width: 768px) 100vw, 33vw" : "(max-width: 768px) 100vw, 25vw"}
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-zinc-900">
              <span className="text-7xl font-black text-white/5 opacity-50 select-none">
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
        <div className="absolute inset-0 flex flex-col justify-end p-5">
          {category.is_featured && (
            <div className="absolute right-4 top-4 rounded-sm bg-white/20 px-3 py-1 text-xs font-semibold text-white backdrop-blur-md">
              <Sparkles className="mr-1 inline-block h-3 w-3" />
              Öne Çıkan
            </div>
          )}

          <div className="transform transition-transform duration-300 group-hover:-translate-y-1">
            <h3 className={cn(
              "font-bold text-white leading-tight drop-shadow-md",
              isTall ? "text-3xl md:text-4xl" : "text-lg md:text-xl"
            )}>
              {category.menu_label || category.name}
            </h3>

            <div className="mt-2 flex items-center gap-2 opacity-0 transform translate-y-2 transition-all duration-300 group-hover:opacity-100 group-hover:translate-y-0 text-white/90 text-sm font-medium">
              <span>İncele</span>
              <ArrowRight className="h-4 w-4" />
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
