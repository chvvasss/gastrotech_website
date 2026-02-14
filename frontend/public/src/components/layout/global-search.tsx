"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Image from "next/image";
import { Search, X, Loader2, Package, Layers, ArrowRight, ChevronLeft, TrendingUp } from "lucide-react";
import { fetchProducts, fetchNav } from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn, getMediaUrl } from "@/lib/utils";

interface GlobalSearchProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// Popular searches - now uses dynamic categories from nav API
// This ensures links match actual category slugs in the database

export function GlobalSearch({ open, onOpenChange }: GlobalSearchProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  // Fetch navigation for categories/series
  const { data: categories = [] } = useQuery({
    queryKey: ["nav"],
    queryFn: fetchNav,
    enabled: open,
  });

  // Search products
  const { data: productsData, isLoading: loadingProducts } = useQuery({
    queryKey: ["search-products", debouncedQuery],
    queryFn: () => fetchProducts({ search: debouncedQuery, page_size: 6 }),
    enabled: open && debouncedQuery.length >= 2,
  });

  const products = productsData?.results || [];

  // Filter categories/series by query
  const filteredCategories = categories.filter(
    (cat) =>
      cat.name.toLowerCase().includes(query.toLowerCase()) ||
      cat.series.some((s) => s.name.toLowerCase().includes(query.toLowerCase()))
  );

  const handleSelect = useCallback(
    (href: string) => {
      router.push(href);
      onOpenChange(false);
      setQuery("");
    },
    [router, onOpenChange]
  );

  // Keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        onOpenChange(!open);
      }
      if (e.key === "Escape") {
        onOpenChange(false);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onOpenChange]);

  // Reset query when closed & focus input when opened
  useEffect(() => {
    if (!open) {
      setQuery("");
    } else {
      // Small delay to ensure dialog is rendered
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [open]);

  const hasResults =
    products.length > 0 || (query && filteredCategories.length > 0);
  const showEmptyState = query.length >= 2 && !loadingProducts && !hasResults;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn(
        "gap-0 p-0 overflow-hidden",
        // Reset default dialog positioning for mobile
        "!left-0 !top-0 !translate-x-0 !translate-y-0",
        "!w-full !h-full !max-w-full !max-h-full !rounded-none",
        // Desktop: Centered modal
        "sm:!left-1/2 sm:!top-[10%] sm:!-translate-x-1/2 sm:!translate-y-0",
        "sm:!w-full sm:!max-w-2xl sm:!h-auto sm:!max-h-[80vh] sm:!rounded-sm",
        // Styling
        "border-0 sm:border sm:border-white/20",
        "bg-white",
        "shadow-none sm:shadow-2xl",
        "[&>button]:hidden" // Hide default dialog close button
      )}>
        <DialogHeader className="sr-only">
          <DialogTitle>Arama</DialogTitle>
        </DialogHeader>

        {/* Mobile Header - Native App Feel */}
        <div className="sm:hidden sticky top-0 z-10 bg-white safe-area-top">
          {/* Status bar spacer for notched phones */}
          <div className="h-[env(safe-area-inset-top,0px)]" />

          <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100">
            {/* Back Button */}
            <button
              onClick={() => onOpenChange(false)}
              className="flex h-10 w-10 items-center justify-center rounded-sm bg-gray-100 active:bg-gray-200 active:scale-95 transition-all"
            >
              <ChevronLeft className="h-6 w-6 text-gray-700" />
            </button>

            {/* Search Input - Large & Touch Friendly */}
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ne aramıştınız?"
                className="w-full h-12 pl-4 pr-10 rounded-sm bg-gray-100 text-sm font-medium placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-primary/20 focus:bg-white transition-all"
              />
              {query ? (
                <button
                  onClick={() => setQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-sm bg-gray-300 active:bg-gray-400"
                >
                  <X className="h-4 w-4 text-gray-600" />
                </button>
              ) : (
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              )}
            </div>
          </div>
        </div>

        {/* Desktop Header */}
        <div className="hidden sm:flex items-center gap-4 border-b border-gray-100 px-5 py-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-sm bg-gradient-to-br from-primary to-primary/80 shadow-lg shadow-primary/20 text-white">
            <Search className="h-5 w-5" />
          </div>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ürün, kategori veya seri ara..."
            className="flex-1 h-11 text-sm font-medium placeholder:text-gray-400 focus:outline-none bg-transparent"
            autoFocus
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="shrink-0 rounded-sm bg-gray-100 p-2.5 hover:bg-gray-200 transition-all"
            >
              <X className="h-4 w-4 text-gray-500" />
            </button>
          )}
        </div>

        {/* Results Area */}
        <ScrollArea className="flex-1 h-[calc(100vh-80px)] sm:h-auto sm:max-h-[60vh]">
          <div className="p-4 sm:p-5 pb-[calc(env(safe-area-inset-bottom,0px)+1rem)]">

            {/* Loading State */}
            {loadingProducts && query.length >= 2 && (
              <div className="flex flex-col items-center justify-center gap-4 py-20">
                <div className="relative">
                  <div className="h-16 w-16 rounded-sm bg-primary/10 animate-pulse" />
                  <Loader2 className="absolute inset-0 m-auto h-8 w-8 animate-spin text-primary" />
                </div>
                <p className="text-sm font-medium text-gray-500">Aranıyor...</p>
              </div>
            )}

            {/* Empty State */}
            {showEmptyState && (
              <div className="flex flex-col items-center justify-center gap-4 py-20 text-center px-6">
                <div className="flex h-20 w-20 items-center justify-center rounded-sm bg-gray-100">
                  <Search className="h-8 w-8 text-gray-300" />
                </div>
                <div>
                  <p className="text-lg font-semibold text-gray-900">
                    Sonuç bulunamadı
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    &quot;{query}&quot; için eşleşen bir sonuç yok
                  </p>
                </div>
                <button
                  onClick={() => setQuery("")}
                  className="mt-2 px-4 py-2 rounded-sm bg-gray-100 text-sm font-medium text-gray-700 active:bg-gray-200"
                >
                  Aramayı Temizle
                </button>
              </div>
            )}

            {/* Initial State - Quick Access */}
            {!query && (
              <div className="space-y-6">
                {/* Popular Categories */}
                <div>
                  <div className="flex items-center gap-2 mb-3 px-1">
                    <TrendingUp className="h-4 w-4 text-primary" />
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-500">
                      Popüler Kategoriler
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {categories.slice(0, 4).map((cat) => (
                      <button
                        key={cat.id}
                        onClick={() => handleSelect(`/kategori/${cat.slug}`)}
                        className="px-4 py-2.5 rounded-sm bg-gray-100 text-sm font-medium text-gray-700 active:bg-gray-200 active:scale-95 transition-all sm:hover:bg-primary sm:hover:text-white"
                      >
                        {cat.menu_label || cat.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* All Categories */}
                <div>
                  <div className="flex items-center gap-2 mb-3 px-1">
                    <Layers className="h-4 w-4 text-primary" />
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-500">
                      Kategoriler
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 sm:gap-3">
                    {categories.slice(0, 6).map((cat) => (
                      <button
                        key={cat.id}
                        onClick={() => handleSelect(`/kategori/${cat.slug}`)}
                        className="group flex items-center gap-3 p-3 sm:p-4 rounded-sm bg-gray-50 active:bg-gray-100 sm:hover:bg-primary/5 sm:hover:shadow-md transition-all text-left"
                      >
                        <div className="flex h-10 w-10 sm:h-12 sm:w-12 shrink-0 items-center justify-center rounded-sm bg-white shadow-sm sm:group-hover:shadow-md transition-shadow overflow-hidden">
                          {cat.cover_media_url ? (
                            <Image
                              src={getMediaUrl(cat.cover_media_url)}
                              alt={cat.name}
                              width={48}
                              height={48}
                              className="object-contain p-1"
                            />
                          ) : (
                            <Layers className="h-5 w-5 text-primary/50" />
                          )}
                        </div>
                        <span className="flex-1 text-sm font-semibold text-gray-700 sm:group-hover:text-primary transition-colors line-clamp-2">
                          {cat.menu_label || cat.name}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Help Text */}
                <div className="text-center pt-4 sm:hidden">
                  <p className="text-xs text-gray-400">
                    Aramak için yazmaya başlayın
                  </p>
                </div>
              </div>
            )}

            {/* Categories & Series Results */}
            {query && filteredCategories.length > 0 && (
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-3 px-1">
                  <Layers className="h-4 w-4 text-primary" />
                  <span className="text-xs font-bold uppercase tracking-wider text-gray-500">
                    Kategoriler
                  </span>
                </div>
                <div className="space-y-2">
                  {filteredCategories.slice(0, 4).map((cat) => (
                    <button
                      key={cat.id}
                      onClick={() => handleSelect(`/kategori/${cat.slug}`)}
                      className="group flex w-full items-center gap-4 p-4 rounded-sm bg-gray-50 active:bg-gray-100 sm:hover:bg-white sm:hover:shadow-md transition-all text-left"
                    >
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-sm bg-white shadow-sm overflow-hidden">
                        {cat.cover_media_url ? (
                          <Image
                            src={getMediaUrl(cat.cover_media_url)}
                            alt={cat.name}
                            width={48}
                            height={48}
                            className="object-contain p-1"
                          />
                        ) : (
                          <Layers className="h-5 w-5 text-primary/50" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-gray-900 sm:group-hover:text-primary transition-colors">
                          {cat.name}
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {cat.series?.length || 0} seri
                        </p>
                      </div>
                      <ArrowRight className="h-5 w-5 text-gray-300 sm:group-hover:text-primary sm:group-hover:translate-x-1 transition-all" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Products Results */}
            {products.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3 px-1">
                  <Package className="h-4 w-4 text-primary" />
                  <span className="text-xs font-bold uppercase tracking-wider text-gray-500">
                    Ürünler
                  </span>
                </div>
                <div className="space-y-2">
                  {products.map((product) => (
                    <button
                      key={product.slug}
                      onClick={() => handleSelect(`/urun/${product.slug}`)}
                      className="group flex w-full items-center gap-4 p-4 rounded-sm bg-gray-50 active:bg-gray-100 sm:hover:bg-white sm:hover:shadow-md transition-all text-left"
                    >
                      {/* Product Image */}
                      <div className="relative h-14 w-14 sm:h-16 sm:w-16 shrink-0 overflow-hidden rounded-sm bg-white shadow-sm">
                        {product.primary_image_url ? (
                          <Image
                            src={getMediaUrl(product.primary_image_url)}
                            alt={product.title_tr || product.slug}
                            fill
                            className="object-contain p-2"
                          />
                        ) : (
                          <div className="flex h-full w-full items-center justify-center">
                            <Package className="h-6 w-6 text-gray-300" />
                          </div>
                        )}
                      </div>

                      {/* Product Info */}
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-gray-900 sm:group-hover:text-primary transition-colors line-clamp-1">
                          {product.title_tr || product.slug}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="inline-flex px-2 py-0.5 rounded-sm bg-primary/10 text-xs font-medium text-primary">
                            {product.series_name}
                          </span>
                          <span className="text-xs text-gray-400">
                            {product.category_name}
                          </span>
                        </div>
                      </div>

                      <ArrowRight className="h-5 w-5 text-gray-300 sm:group-hover:text-primary sm:group-hover:translate-x-1 transition-all" />
                    </button>
                  ))}
                </div>

                {/* View All Results */}
                {productsData?.next && (
                  <button
                    onClick={() => handleSelect(`/urunler?search=${query}`)}
                    className="mt-4 flex w-full items-center justify-center gap-2 rounded-sm bg-primary py-4 text-white font-semibold active:bg-primary/90 sm:hover:shadow-lg sm:hover:shadow-primary/30 transition-all"
                  >
                    Tüm sonuçları gör
                    <ArrowRight className="h-5 w-5" />
                  </button>
                )}
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Desktop Footer */}
        <div className="hidden sm:flex border-t border-gray-100 bg-gray-50/50 px-5 py-2" />
      </DialogContent>
    </Dialog>
  );
}
