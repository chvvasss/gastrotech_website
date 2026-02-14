"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface PaginationProps {
    currentPage: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
    onPageChange: (page: number) => void;
}

export function Pagination({
    currentPage,
    totalPages,
    hasNext,
    hasPrev,
    onPageChange,
}: PaginationProps) {
    if (totalPages <= 1) return null;

    // Calculate visible page numbers
    const getPageNumbers = () => {
        const pages: (number | "ellipsis")[] = [];
        const maxVisible = 7;

        if (totalPages <= maxVisible) {
            // Show all pages
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            // Always show first page
            pages.push(1);

            if (currentPage > 3) {
                pages.push("ellipsis");
            }

            // Show pages around current
            const start = Math.max(2, currentPage - 1);
            const end = Math.min(totalPages - 1, currentPage + 1);

            for (let i = start; i <= end; i++) {
                pages.push(i);
            }

            if (currentPage < totalPages - 2) {
                pages.push("ellipsis");
            }

            // Always show last page
            pages.push(totalPages);
        }

        return pages;
    };

    return (
        <nav className="flex items-center justify-center gap-1">
            {/* Previous button */}
            <button
                onClick={() => onPageChange(currentPage - 1)}
                disabled={!hasPrev}
                className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-md border transition-colors",
                    hasPrev
                        ? "border-border bg-card text-foreground hover:border-destructive hover:bg-destructive hover:text-white"
                        : "cursor-not-allowed border-border/50 bg-muted text-muted-foreground"
                )}
                aria-label="Önceki sayfa"
            >
                <ChevronLeft className="h-4 w-4" />
            </button>

            {/* Page numbers */}
            <div className="flex items-center gap-1">
                {getPageNumbers().map((page, index) =>
                    page === "ellipsis" ? (
                        <span
                            key={`ellipsis-${index}`}
                            className="flex h-10 w-10 items-center justify-center text-muted-foreground"
                        >
                            ...
                        </span>
                    ) : (
                        <button
                            key={page}
                            onClick={() => onPageChange(page)}
                            className={cn(
                                "flex h-10 w-10 items-center justify-center rounded-md border text-sm font-medium transition-all",
                                page === currentPage
                                    ? "border-destructive bg-destructive text-white shadow-md shadow-destructive/25"
                                    : "border-border bg-card text-foreground hover:border-destructive/50 hover:bg-destructive/10"
                            )}
                            aria-current={page === currentPage ? "page" : undefined}
                        >
                            {page}
                        </button>
                    )
                )}
            </div>

            {/* Next button */}
            <button
                onClick={() => onPageChange(currentPage + 1)}
                disabled={!hasNext}
                className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-md border transition-colors",
                    hasNext
                        ? "border-border bg-card text-foreground hover:border-destructive hover:bg-destructive hover:text-white"
                        : "cursor-not-allowed border-border/50 bg-muted text-muted-foreground"
                )}
                aria-label="Sonraki sayfa"
            >
                <ChevronRight className="h-4 w-4" />
            </button>
        </nav>
    );
}
