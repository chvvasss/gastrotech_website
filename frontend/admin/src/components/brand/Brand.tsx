"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface BrandProps {
  variant?: "sidebar" | "sidebar-collapsed" | "login" | "header";
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  linkHref?: string;
}

// Much bigger sizes for the logo
const sizes = {
  sm: { icon: 40 },
  md: { icon: 56 },
  lg: { icon: 80 },
  xl: { icon: 120 },
};

export function Brand({
  variant = "sidebar",
  size = "md",
  className,
  linkHref = "/dashboard",
}: BrandProps) {
  const [imgError, setImgError] = useState(false);
  const sizeConfig = sizes[size];

  // Different logos for different states
  // Using absolute paths with /admin prefix because of basePath issues with Next.js Image
  const showIconOnly = variant === "sidebar-collapsed";
  const logoSrc = showIconOnly ? "/admin/favicon.png" : "/admin/brand/logo.png";

  // Custom sizing logic
  let width = sizeConfig.icon;
  let height = sizeConfig.icon;

  if (variant === "sidebar") {
    // Sidebar Expanded: Full Logo (landscape)
    width = 150;
    height = 42;
  } else if (variant === "sidebar-collapsed") {
    // Sidebar Collapsed: Icon Only (square)
    width = 32;
    height = 32;
  }

  const content = (
    <div className={cn(
      "flex items-center justify-center",
      className
    )}>
      <div className="relative shrink-0">
        {!imgError ? (
          <img
            src={logoSrc}
            alt="Gastrotech Admin"
            width={width}
            height={height}
            className="object-contain"
            onError={() => setImgError(true)}
            style={{ width, height, objectFit: 'contain' }}
          />
        ) : (
          <div
            className="rounded-xl bg-primary flex items-center justify-center text-white font-bold"
            style={{
              width: width,
              height: height,
              fontSize: height * 0.4
            }}
          >
            G
          </div>
        )}
      </div>
    </div>
  );

  if (linkHref) {
    return (
      <Link
        href={linkHref}
        className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded-lg"
      >
        {content}
      </Link>
    );
  }

  return content;
}

// Standalone icon component for minimal use cases
export function BrandIcon({ size = 48, className }: { size?: number; className?: string }) {
  const [imgError, setImgError] = useState(false);

  if (imgError) {
    return (
      <div
        className={cn(
          "rounded-xl bg-primary flex items-center justify-center text-white font-bold",
          className
        )}
        style={{ width: size, height: size, fontSize: size * 0.4 }}
      >
        G
      </div>
    );
  }

  return (
    <img
      src="/admin/brand/logo.png"
      alt="GastroTech"
      width={size}
      height={size}
      className={cn("shrink-0 object-contain", className)}
      onError={() => setImgError(true)}
    />
  );
}
