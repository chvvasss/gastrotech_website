"use client";

import { useState } from "react";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Plus, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { adminProductsApi } from "@/lib/api/admin-products";
import { http } from "@/lib/api/http";

// Simple series interface since we just need id/name/category relative to adminList
interface AdminSeriesListItem {
    id: string;
    name: string;
    slug: string;
    category: {
        id: string;
        name: string;
        slug: string;
    };
}

export function CreateProductDialog() {
    const [open, setOpen] = useState(false);
    const [title, setTitle] = useState("");
    const [seriesSlug, setSeriesSlug] = useState("");

    const router = useRouter();
    const { toast } = useToast();
    const queryClient = useQueryClient();

    // Fetch all series for selection
    const { data: seriesList, isLoading: seriesLoading } = useQuery<AdminSeriesListItem[]>({
        queryKey: ["admin-series-list"],
        queryFn: async () => {
            // NOTE: We assume /admin/series/ exists and returns pagination or list
            const res = await http.get<{ results: AdminSeriesListItem[] } | AdminSeriesListItem[]>("/admin/series/");
            if (Array.isArray(res.data)) return res.data;
            if ("results" in res.data) return res.data.results;
            return [];
        },
        staleTime: 5 * 60 * 1000,
    });

    const createMutation = useMutation({
        mutationFn: async () => {
            return adminProductsApi.createProduct({
                title_tr: title,
                // API expects 'series' (slug or ID)
                series: seriesSlug,
                status: "draft",
            });
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ["products"] });
            toast({
                title: "Ürün oluşturuldu",
                description: `"${data.title_tr}" başarıyla oluşturuldu. Düzenleme sayfasına yönlendiriliyorsunuz.`,
            });
            setOpen(false);
            // Redirect to edit page
            router.push(`/catalog/products/${data.slug}`);
        },
        onError: (error: any) => {
            toast({
                title: "Hata",
                description: error.message || "Ürün oluşturulamadı",
                variant: "destructive",
            });
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!title || !seriesSlug) return;
        createMutation.mutate();
    };

    // Group series by category for better UX
    const groupedSeries = (seriesList || []).reduce((acc, series) => {
        const catName = series.category?.name || "Diğer";
        if (!acc[catName]) acc[catName] = [];
        acc[catName].push(series);
        return acc;
    }, {} as Record<string, AdminSeriesListItem[]>);

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Yeni Ürün
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <form onSubmit={handleSubmit}>
                    <DialogHeader>
                        <DialogTitle>Yeni Ürün Oluştur</DialogTitle>
                        <DialogDescription>
                            Temel bilgileri girerek hızlıca ürün oluşturun. Detayları bir sonraki ekranda girebileceksiniz.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="series">Seri / Kategori</Label>
                            <Select value={seriesSlug} onValueChange={setSeriesSlug} required>
                                <SelectTrigger id="series" disabled={seriesLoading}>
                                    <SelectValue placeholder={seriesLoading ? "Yükleniyor..." : "Seri seçin"} />
                                </SelectTrigger>
                                <SelectContent>
                                    {Object.entries(groupedSeries).map(([categoryName, seriesItems]) => (
                                        <div key={categoryName}>
                                            <div className="px-2 py-1.5 text-xs font-semibold text-stone-500 bg-stone-50">
                                                {categoryName}
                                            </div>
                                            {seriesItems.map((series) => (
                                                <SelectItem key={series.id} value={series.slug}>
                                                    {series.name}
                                                </SelectItem>
                                            ))}
                                        </div>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="title">Ürün Başlığı</Label>
                            <Input
                                id="title"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                placeholder="Örn: Set Altı Bulaşık Makinesi"
                                required
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button
                            type="submit"
                            disabled={!title || !seriesSlug || createMutation.isPending}
                        >
                            {createMutation.isPending ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Oluşturuluyor...
                                </>
                            ) : (
                                "Oluştur"
                            )}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
