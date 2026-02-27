"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { type ColumnDef } from "@tanstack/react-table";
import { Search, Filter, Star, ExternalLink, Trash2, GitBranch, Loader2, AlertCircle, Tag } from "lucide-react";
import Link from "next/link";
import { DataTable, Pagination } from "@/components/data-table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useCatalogProducts } from "@/hooks/use-catalog-products";
import { BadgeStatus } from "@/components/catalog";
import { CreateProductDialog } from "@/components/catalog/create-product-dialog";
import { BulkBrandChangeModal } from "@/components/catalog/bulk-brand-change-modal";
import type { ProductStatus } from "@/types/api";
import type { AdminProductListItem } from "@/lib/api/admin-products";
import { adminProductsApi } from "@/lib/api/admin-products";
import { useToast } from "@/hooks/use-toast";
import { getMediaUrl } from "@/lib/media-url";

const ALL_STATUS = "_all";

// Debounce hook
function useDebounce<T>(value: T, delay: number): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);

    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]);

    return debouncedValue;
}

interface ProductsTableProps {
    scope?: "all" | "category" | "series";
    scopeId?: string; // category slug or series slug
    showFilters?: boolean;
}

export function ProductsTable({ scope = "all", scopeId, showFilters = true }: ProductsTableProps) {
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const { toast } = useToast();

    // Local state for filters (detached from URL if scoped)
    // If scope is 'all', we sync with URL. If scoped, we keep local.
    const isGlobal = scope === "all";

    const initialPage = isGlobal ? parseInt(searchParams.get("page") || "1", 10) : 1;
    const initialStatus = isGlobal ? (searchParams.get("status") || ALL_STATUS) : ALL_STATUS;
    const initialSearch = isGlobal ? (searchParams.get("search") || "") : "";

    const [page, setPage] = useState(initialPage);
    const [status, setStatus] = useState<string>(initialStatus);
    const [searchInput, setSearchInput] = useState(initialSearch);

    const debouncedSearch = useDebounce(searchInput, 300);
    const pageSize = 20;

    // Derive filters from props + state
    const queryFilters: any = {
        page,
        page_size: pageSize,
        status: status === ALL_STATUS ? undefined : (status as ProductStatus),
        search: debouncedSearch || undefined,
        ordering: "-created_at",
    };

    if (scope === "category" && scopeId) {
        queryFilters.category = scopeId;
    } else if (scope === "series" && scopeId) {
        // Note: API might expect 'series' slug
        queryFilters.series = scopeId;
    }

    const { data, isLoading, refetch } = useCatalogProducts(queryFilters);

    // Sync URL only for Global scope
    useEffect(() => {
        if (!isGlobal) return;

        const params = new URLSearchParams(searchParams.toString());
        if (page > 1) params.set("page", page.toString());
        else params.delete("page");

        if (status !== ALL_STATUS) params.set("status", status);
        else params.delete("status");

        if (debouncedSearch) params.set("search", debouncedSearch);
        else params.delete("search");

        const queryString = params.toString();
        router.replace(queryString ? `?${queryString}` : pathname, { scroll: false });
    }, [isGlobal, page, status, debouncedSearch, router, searchParams, pathname]);


    // Selection state for bulk operations
    const [rowSelection, setRowSelection] = useState<Record<string, boolean>>({});
    const [selectAllFiltered, setSelectAllFiltered] = useState(false);
    const [bulkModalOpen, setBulkModalOpen] = useState(false);

    // Delete Logic
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [productToDelete, setProductToDelete] = useState<AdminProductListItem | null>(null);
    const [isDeleting, setIsDeleting] = useState(false);

    const handleDeleteClick = useCallback((product: AdminProductListItem) => {
        setProductToDelete(product);
        setDeleteDialogOpen(true);
    }, []);

    const confirmDelete = async () => {
        if (!productToDelete) return;
        setIsDeleting(true);
        try {
            await adminProductsApi.deleteProduct(productToDelete.slug);
            toast({
                title: "Ürün silindi",
                description: `"${productToDelete.title_tr}" başarıyla silindi.`,
            });
            refetch();
            setDeleteDialogOpen(false);
            setProductToDelete(null);
        } catch (error) {
            toast({
                title: "Hata",
                description: "Ürün silinirken bir hata oluştu.",
                variant: "destructive",
            });
        } finally {
            setIsDeleting(false);
        }
    };

    const totalPages = Math.ceil((data?.count ?? 0) / pageSize);

    // Handle row selection toggle
    const handleRowSelect = useCallback((id: string, checked: boolean) => {
        setRowSelection(prev => {
            const next = { ...prev };
            if (checked) {
                next[id] = true;
            } else {
                delete next[id];
            }
            return next;
        });
    }, []);

    // Handle select all on current page
    const handleSelectAllPage = useCallback((checked: boolean) => {
        if (!data?.results) return;
        setRowSelection(prev => {
            const next = { ...prev };
            data.results.forEach(item => {
                if (checked) {
                    next[item.id] = true;
                } else {
                    delete next[item.id];
                }
            });
            return next;
        });
    }, [data?.results]);

    // Check if all current page items are selected
    const allPageSelected = useMemo(() => {
        if (!data?.results || data.results.length === 0) return false;
        return data.results.every(item => rowSelection[item.id]);
    }, [data?.results, rowSelection]);

    const selectedCount = Object.keys(rowSelection).length;

    const columns = useMemo<ColumnDef<AdminProductListItem>[]>(() => [
        {
            id: "select",
            header: () => (
                <Checkbox
                    checked={allPageSelected}
                    onCheckedChange={(checked) => handleSelectAllPage(!!checked)}
                    aria-label="Tümünü seç"
                />
            ),
            cell: ({ row }) => (
                <Checkbox
                    checked={!!rowSelection[row.original.id]}
                    onCheckedChange={(checked) => handleRowSelect(row.original.id, !!checked)}
                    aria-label="Satırı seç"
                />
            ),
        },
        {
            accessorKey: "primary_image_url",
            header: "",
            cell: ({ row }) => {
                const imageUrl = row.original.primary_image_url;
                return (
                    <div className="w-12 h-12 rounded-lg bg-stone-100 overflow-hidden border border-stone-200">
                        {imageUrl ? (
                            <img
                                src={getMediaUrl(imageUrl)}
                                alt={row.original.title_tr}
                                className="w-full h-full object-cover"
                            />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center text-stone-400 text-xs">
                                N/A
                            </div>
                        )}
                    </div>
                );
            },
        },
        {
            accessorKey: "title_tr",
            header: "Ürün",
            cell: ({ row }) => (
                <div className="flex items-center gap-2">
                    <div>
                        <Link
                            href={`/catalog/products/${row.original.slug}`}
                            className="font-medium text-stone-900 hover:text-primary transition-colors"
                        >
                            {row.original.title_tr}
                        </Link>
                        <p className="text-xs text-stone-500">{row.original.slug}</p>
                    </div>
                    {row.original.is_featured && (
                        <Star className="h-4 w-4 text-amber-500 fill-amber-500" />
                    )}
                </div>
            ),
        },
        {
            accessorKey: "series_name",
            header: "Seri",
            cell: ({ row }) => (
                <div>
                    <p className="font-medium text-stone-900">{row.original.series_name}</p>
                    <p className="text-xs text-stone-500">{row.original.category_name}</p>
                </div>
            ),
        },
        {
            accessorKey: "brand_name",
            header: "Marka",
            cell: ({ row }) => (
                <span className="text-sm text-stone-600">
                    {row.original.brand_name || "-"}
                </span>
            ),
        },
        {
            accessorKey: "variants_count",
            header: "Varyant",
            cell: ({ row }) => (
                <span className="font-medium text-stone-900">{row.original.variants_count}</span>
            ),
        },
        {
            accessorKey: "status",
            header: "Durum",
            cell: ({ row }) => <BadgeStatus status={row.original.status} />,
        },
        {
            id: "actions",
            cell: ({ row }) => {
                const djangoAdminUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "";
                return (
                    <div className="flex items-center gap-1">
                        <Button variant="ghost" size="sm" className="text-stone-500 hover:text-stone-900 h-8" asChild>
                            <Link href={`/catalog/products/${row.original.slug}`}>
                                Düzenle
                            </Link>
                        </Button>
                        <Button variant="ghost" size="icon" className="text-stone-400 hover:text-stone-900 h-8 w-8" asChild>
                            <a
                                href={`${djangoAdminUrl}/admin/catalog/product/${row.original.slug}/change/`}
                                target="_blank"
                                rel="noopener noreferrer"
                                title="Django Admin'de Aç"
                            >
                                <ExternalLink className="h-4 w-4" />
                            </a>
                        </Button>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="text-stone-400 hover:text-red-600 h-8 w-8 hover:bg-red-50"
                            onClick={() => handleDeleteClick(row.original)}
                            title="Sil"
                        >
                            <Trash2 className="h-4 w-4" />
                        </Button>
                    </div>
                );
            },
        },
    ], [handleDeleteClick, allPageSelected, handleSelectAllPage, rowSelection, handleRowSelect]);


    return (
        <div className="space-y-6">
            {/* Filters */}
            {showFilters && (
                <div className="flex flex-col sm:flex-row gap-4">
                    <div className="flex flex-1 gap-2">
                        <div className="relative flex-1 max-w-md">
                            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
                            <Input
                                placeholder="Ürün adı ile ara..."
                                value={searchInput}
                                onChange={(e) => {
                                    setSearchInput(e.target.value);
                                    setPage(1);
                                }}
                                className="pl-10 bg-white border-stone-200"
                            />
                        </div>
                    </div>
                    <div className="flex gap-2 items-center">
                        <Select value={status} onValueChange={(val) => { setStatus(val); setPage(1); }}>
                            <SelectTrigger className="w-[140px] bg-white border-stone-200">
                                <Filter className="h-4 w-4 mr-2 text-stone-500" />
                                <SelectValue placeholder="Tüm durumlar" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value={ALL_STATUS}>Tüm durumlar</SelectItem>
                                <SelectItem value="draft">Taslak</SelectItem>
                                <SelectItem value="active">Aktif</SelectItem>
                                <SelectItem value="archived">Arşiv</SelectItem>
                            </SelectContent>
                        </Select>

                        {/* Create Button */}
                        <div className="h-6 w-px bg-stone-200 mx-2 hidden sm:block" />
                        <CreateProductDialog />
                    </div>
                </div>
            )}

            {/* Bulk Action Bar */}
            {selectedCount > 0 && (
                <div className="flex items-center justify-between p-3 bg-primary/5 border border-primary/20 rounded-lg">
                    <div className="flex items-center gap-4">
                        <span className="text-sm font-medium text-stone-700">
                            {selectAllFiltered && data?.count
                                ? `${data.count} ürün seçildi (tüm filtre)`
                                : `${selectedCount} ürün seçildi`}
                        </span>
                        {data && data.count > pageSize && !selectAllFiltered && (
                            <Button
                                variant="link"
                                size="sm"
                                className="text-primary p-0 h-auto"
                                onClick={() => setSelectAllFiltered(true)}
                            >
                                Tüm {data.count} ürünü seç
                            </Button>
                        )}
                        {selectAllFiltered && (
                            <Button
                                variant="link"
                                size="sm"
                                className="text-stone-500 p-0 h-auto"
                                onClick={() => setSelectAllFiltered(false)}
                            >
                                Sadece bu sayfa
                            </Button>
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                                setRowSelection({});
                                setSelectAllFiltered(false);
                            }}
                        >
                            Seçimi Temizle
                        </Button>
                        <Button
                            size="sm"
                            onClick={() => setBulkModalOpen(true)}
                        >
                            <Tag className="h-4 w-4 mr-2" />
                            Marka Değiştir
                        </Button>
                    </div>
                </div>
            )}

            {/* Empty State */}
            {!isLoading && (!data?.results || data.results.length === 0) ? (
                <div className="flex flex-col items-center justify-center py-16 text-center border border-dashed border-stone-200 rounded-lg bg-stone-50">
                    <div className="h-16 w-16 rounded-full bg-stone-100 flex items-center justify-center mb-4">
                        <GitBranch className="h-8 w-8 text-stone-400" />
                    </div>
                    <h3 className="text-lg font-medium text-stone-900 mb-2">
                        Ürün bulunamadı
                    </h3>
                    <p className="text-sm text-stone-500 max-w-md mb-6">
                        Bu kriterlere uygun ürün bulunamadı.
                    </p>
                    {scope === "all" && (
                        <Button asChild>
                            <Link href="/catalog/taxonomy">
                                <GitBranch className="h-4 w-4 mr-2" />
                                Taksonomi Ekranına Git
                            </Link>
                        </Button>
                    )}
                </div>
            ) : (
                <>
                    <DataTable
                        columns={columns}
                        data={data?.results ?? []}
                        loading={isLoading}
                        emptyMessage="Ürün bulunamadı"
                        emptyDescription="Filtrelere uygun ürün bulunamadı."
                    />
                    {data && data.count > 0 && (
                        <Pagination
                            page={page}
                            totalPages={totalPages}
                            totalItems={data.count}
                            pageSize={pageSize}
                            onPageChange={setPage}
                        />
                    )}
                </>
            )}

            <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle className="flex items-center gap-2 text-red-600">
                            <AlertCircle className="h-5 w-5" />
                            Ürünü Sil
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                            Bu işlem geri alınamaz.
                            <span className="font-semibold text-stone-900 block mt-1">
                                "{productToDelete?.title_tr}" ({productToDelete?.slug})
                            </span>
                            adlı ürün kalıcı olarak silinecektir. Emin misiniz?
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={isDeleting}>İptal</AlertDialogCancel>
                        <AlertDialogAction
                            className="bg-red-600 hover:bg-red-700 focus:ring-red-600 transition-colors"
                            onClick={(e) => {
                                e.preventDefault();
                                confirmDelete();
                            }}
                            disabled={isDeleting}
                        >
                            {isDeleting ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Siliniyor...
                                </>
                            ) : (
                                "Evet, Sil"
                            )}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* Bulk Brand Change Modal */}
            <BulkBrandChangeModal
                open={bulkModalOpen}
                onOpenChange={setBulkModalOpen}
                selectedIds={Object.keys(rowSelection)}
                filters={selectAllFiltered ? {
                    series: queryFilters.series,
                    category: queryFilters.category,
                    status: queryFilters.status,
                    search: queryFilters.search,
                } : undefined}
                selectionMode={selectAllFiltered ? "filtered" : "explicit"}
                onSuccess={() => {
                    setRowSelection({});
                    setSelectAllFiltered(false);
                    refetch();
                }}
            />
        </div>
    );
}
