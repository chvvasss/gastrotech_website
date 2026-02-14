"use client";

import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  page: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export function Pagination({
  page,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
}: PaginationProps) {
  const startItem = (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, totalItems);

  return (
    <div className="flex items-center justify-between px-2 py-4">
      <p className="text-sm text-stone-500">
        {totalItems > 0 ? (
          <>
            <span className="font-medium text-stone-700">{startItem}</span>-
            <span className="font-medium text-stone-700">{endItem}</span> / toplam{" "}
            <span className="font-medium text-stone-700">{totalItems}</span> kayıt
          </>
        ) : (
          "Kayıt bulunamadı"
        )}
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="border-stone-200"
        >
          <ChevronLeft className="h-4 w-4" />
          <span className="sr-only">Önceki</span>
        </Button>
        <span className="text-sm text-stone-600">
          Sayfa {page} / {totalPages || 1}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="border-stone-200"
        >
          <ChevronRight className="h-4 w-4" />
          <span className="sr-only">Sonraki</span>
        </Button>
      </div>
    </div>
  );
}
