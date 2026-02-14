import Link from "next/link";
import { ChevronRight, Home } from "lucide-react";
import { cn } from "@/lib/utils";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  return (
    <nav
      className={cn("flex items-center gap-1.5 text-small", className)}
      aria-label="Breadcrumb"
    >
      <Link
        href="/dashboard"
        className="flex items-center text-stone-400 hover:text-primary transition-fast"
      >
        <Home className="h-3.5 w-3.5" />
      </Link>
      {items.map((item, index) => (
        <div key={index} className="flex items-center gap-1.5">
          <ChevronRight className="h-3.5 w-3.5 text-stone-300" />
          {item.href ? (
            <Link
              href={item.href}
              className="text-stone-500 hover:text-primary transition-fast"
            >
              {item.label}
            </Link>
          ) : (
            <span className="text-stone-700 font-medium">{item.label}</span>
          )}
        </div>
      ))}
    </nav>
  );
}
