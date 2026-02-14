"use client";

import Image from "next/image";
import { cn } from "@/lib/utils";

interface MarqueeProps {
  items: string[];
  speed?: "slow" | "normal" | "fast";
  className?: string;
}

export function Marquee({ items, speed = "normal", className }: MarqueeProps) {
  const speedDuration = {
    slow: "60s",
    normal: "30s",
    fast: "15s",
  };

  // Duplicate items for seamless loop
  const duplicatedItems = [...items, ...items];

  return (
    <div
      className={cn(
        "relative overflow-hidden whitespace-nowrap",
        className
      )}
      aria-label="Referanslar"
    >
      {/* Gradient masks - Hidden on mobile to prevent overflow, visible on lg */}
      <div className="pointer-events-none absolute left-0 top-0 z-10 h-full w-20 bg-gradient-to-r from-background to-transparent hidden lg:block" />
      <div className="pointer-events-none absolute right-0 top-0 z-10 h-full w-20 bg-gradient-to-l from-background to-transparent hidden lg:block" />

      {/* Scrolling content - NO hover pause */}
      <div
        className="inline-flex animate-marquee motion-reduce:animate-none motion-reduce:flex motion-reduce:flex-wrap motion-reduce:justify-center motion-reduce:gap-8"
        style={{
          animationDuration: speedDuration[speed],
        }}
      >
        {duplicatedItems.map((item, index) => {
          const isImage = item.startsWith("/") || item.startsWith("http");
          return (
            <div
              key={`${item}-${index}`}
              className={cn(
                "relative mx-8 flex items-center justify-center transition-all duration-300 opacity-70 hover:opacity-100 lg:mx-12",
                isImage ? "h-12 w-32 lg:h-16 lg:w-40 grayscale hover:grayscale-0" : "h-auto w-auto"
              )}
            >
              {isImage ? (
                <Image
                  src={item}
                  alt={`Reference ${index}`}
                  fill
                  className="object-contain"
                  sizes="(max-width: 768px) 128px, 160px"
                />
              ) : (
                <span className="text-xl font-bold text-muted-foreground whitespace-nowrap">
                  {item}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Static grid fallback for reduced motion
export function ReferenceGrid({ items }: { items: string[] }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
      {items.map((item, index) => (
        <div
          key={`${item}-${index}`}
          className="relative flex h-20 items-center justify-center rounded-sm border bg-muted/50 px-4 py-6"
        >
          <div className="relative h-12 w-full opacity-70 grayscale transition-all hover:opacity-100 hover:grayscale-0">
            <Image
              src={item}
              alt={`Reference ${index}`}
              fill
              className="object-contain"
              sizes="(max-width: 768px) 128px, 160px"
            />
          </div>
        </div>
      ))}
    </div>
  );
}
