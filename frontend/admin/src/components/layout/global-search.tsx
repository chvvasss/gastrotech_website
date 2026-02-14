"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Package,
  FolderTree,
  Layers,
  GitBranch,
  LayoutDashboard,
  Settings,
  Upload,
  ClipboardList,
  MessageSquare,
  Tag,
  Loader2,
} from "lucide-react";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { useDebounce } from "@/hooks/use-debounce";
import { adminSearchApi, type SearchResultItem } from "@/lib/api/admin-search";

// Quick navigation items (always shown when no search or as fallback)
const quickActions = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard, keywords: ["home", "ana sayfa", "gösterge"] },
  { name: "Ürünler", href: "/catalog/products", icon: Package, keywords: ["products", "katalog"] },
  { name: "Taksonomi", href: "/catalog/taxonomy", icon: GitBranch, keywords: ["taxonomy", "ağaç", "kategori"] },
  { name: "Talepler", href: "/inquiries", icon: MessageSquare, keywords: ["inquiries", "requests", "istekler"] },
  { name: "İçe Aktar", href: "/ops/import", icon: Upload, keywords: ["import", "csv", "excel"] },
  { name: "İşlem Geçmişi", href: "/ops/audit-logs", icon: ClipboardList, keywords: ["audit", "log", "geçmiş"] },
  { name: "Ayarlar", href: "/settings", icon: Settings, keywords: ["settings", "preferences"] },
];

// Icon map for result types
const typeIcons: Record<SearchResultItem["type"], React.ElementType> = {
  product: Package,
  category: FolderTree,
  series: Layers,
  taxonomy: GitBranch,
  variant: Tag,
};

// Label map for result types
const typeLabels: Record<SearchResultItem["type"], string> = {
  product: "Ürünler",
  category: "Kategoriler",
  series: "Seriler",
  taxonomy: "Taksonomi",
  variant: "Model Kodları",
};

interface GlobalSearchProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function GlobalSearch({ open, onOpenChange }: GlobalSearchProps) {
  const router = useRouter();
  const [search, setSearch] = React.useState("");
  const debouncedSearch = useDebounce(search, 250);
  
  // Use backend search API
  const { data: searchData, isLoading, isError, error } = useQuery({
    queryKey: ["admin-search", debouncedSearch],
    queryFn: () => adminSearchApi.search(debouncedSearch, 30),
    enabled: debouncedSearch.length >= 2,
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 60 * 1000, // 1 minute
    retry: 1,
  });

  // Close and navigate
  const handleSelect = React.useCallback((href: string) => {
    onOpenChange(false);
    setSearch("");
    router.push(href);
  }, [router, onOpenChange]);

  // Reset search when dialog closes
  React.useEffect(() => {
    if (!open) {
      setSearch("");
    }
  }, [open]);

  // Filter quick actions based on search
  const filteredActions = React.useMemo(() => {
    if (debouncedSearch.length === 0) return quickActions;
    const query = debouncedSearch.toLowerCase();
    return quickActions.filter(action => 
      action.name.toLowerCase().includes(query) ||
      action.keywords.some(k => k.toLowerCase().includes(query))
    );
  }, [debouncedSearch]);

  // Group results by type
  const groupedResults = React.useMemo(() => {
    if (!searchData?.results) return {};
    
    const groups: Record<string, SearchResultItem[]> = {};
    for (const result of searchData.results) {
      if (!groups[result.type]) {
        groups[result.type] = [];
      }
      groups[result.type].push(result);
    }
    return groups;
  }, [searchData]);

  // Order for displaying groups
  const typeOrder: SearchResultItem["type"][] = ["product", "variant", "category", "series", "taxonomy"];

  const hasSearchResults = Object.keys(groupedResults).length > 0;
  const showQuickActions = debouncedSearch.length === 0 || filteredActions.length > 0;

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput 
        placeholder="Ara... (ürün, kategori, seri, model kodu)" 
        value={search}
        onValueChange={setSearch}
      />
      <CommandList>
        {/* Loading state */}
        {isLoading && debouncedSearch.length >= 2 && (
          <div className="py-6 text-center text-sm text-stone-500 flex items-center justify-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Aranıyor...</span>
          </div>
        )}

        {/* Error state */}
        {isError && debouncedSearch.length >= 2 && (
          <div className="py-6 text-center text-sm text-red-500">
            <p>Arama sırasında bir hata oluştu.</p>
            <p className="text-xs text-stone-400 mt-1">Lütfen tekrar deneyin.</p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !isError && (
          <CommandEmpty>
            {debouncedSearch.length < 2
              ? "En az 2 karakter girin..."
              : "Sonuç bulunamadı."
            }
          </CommandEmpty>
        )}

        {/* Quick Actions - always show when no search */}
        {showQuickActions && !isLoading && (
          <CommandGroup heading="Hızlı Erişim">
            {filteredActions.map((action) => (
              <CommandItem
                key={action.href}
                value={`action-${action.name}`}
                onSelect={() => handleSelect(action.href)}
                className="gap-3"
              >
                <action.icon className="h-4 w-4 text-stone-500" />
                <span>{action.name}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        )}

        {/* Backend Search Results - grouped by type */}
        {!isLoading && hasSearchResults && (
          <>
            {typeOrder.map((type) => {
              const results = groupedResults[type];
              if (!results || results.length === 0) return null;
              
              const Icon = typeIcons[type];
              const label = typeLabels[type];
              
              return (
                <React.Fragment key={type}>
                  <CommandSeparator />
                  <CommandGroup heading={label}>
                    {results.map((result) => (
                      <CommandItem
                        key={`${result.type}-${result.id}`}
                        value={`${result.type}-${result.id}-${result.title}`}
                        onSelect={() => handleSelect(result.href)}
                        className="gap-3"
                      >
                        <Icon className="h-4 w-4 text-stone-500 shrink-0" />
                        <div className="flex flex-col min-w-0">
                          <span className="font-medium truncate">{result.title}</span>
                          {result.subtitle && (
                            <span className="text-xs text-stone-500 truncate">
                              {result.subtitle}
                            </span>
                          )}
                        </div>
                        {/* Score indicator (subtle) */}
                        <span className="ml-auto text-[10px] text-stone-400 tabular-nums">
                          {Math.round(result.score * 100)}%
                        </span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </React.Fragment>
              );
            })}
          </>
        )}
      </CommandList>
      
      {/* Footer with keyboard hints */}
      <div className="border-t border-stone-200 px-3 py-2 text-xs text-stone-500 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <kbd className="px-1.5 py-0.5 bg-stone-100 rounded text-stone-600 font-mono">↑↓</kbd>
          <span>gezin</span>
          <kbd className="px-1.5 py-0.5 bg-stone-100 rounded text-stone-600 font-mono ml-2">↵</kbd>
          <span>seç</span>
        </div>
        <div className="flex items-center gap-2">
          <kbd className="px-1.5 py-0.5 bg-stone-100 rounded text-stone-600 font-mono">Esc</kbd>
          <span>kapat</span>
        </div>
      </div>
    </CommandDialog>
  );
}

// Hook for keyboard shortcut
export function useGlobalSearchShortcut(onOpen: () => void) {
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        onOpen();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onOpen]);
}
