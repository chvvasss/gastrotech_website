"use client";

import { useState } from "react";
import {
    Plus,
    Edit2,
    Trash2,
    Loader2,
    MoreHorizontal,
    Star,
    Layers,
    Package,
} from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { ImageUpload } from "@/components/ui/image-upload";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import {
    useCategories,
    useAdminSeries,
    useCreateSeries,
    useUpdateSeries,
    useDeleteSeries,
} from "@/hooks/use-admin-taxonomy";
import type { AdminSeries, CreateSeriesPayload, UpdateSeriesPayload } from "@/lib/api/admin-taxonomy";

const getMediaUrl = (id?: string | null) => {
    if (!id) return undefined;
    return `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/media/${id}/file/`;
};

export default function SeriesPage() {
    const { toast } = useToast();
    const [selectedCategory, setSelectedCategory] = useState<string>("__all__");
    const [formOpen, setFormOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [editingSeries, setEditingSeries] = useState<AdminSeries | null>(null);
    const [deletingSeries, setDeletingSeries] = useState<AdminSeries | null>(null);

    // Form state
    const [formData, setFormData] = useState<CreateSeriesPayload>({
        name: "",
        slug: "",
        category_slug: "",
        description_short: "",
        order: 0,
        is_featured: false,
        cover_media: null,
    });

    const { data: categories, isLoading: categoriesLoading } = useCategories();
    const { data: series, isLoading: seriesLoading } = useAdminSeries(
        selectedCategory !== "__all__" ? { category: selectedCategory } : undefined
    );

    const createMutation = useCreateSeries();
    const updateMutation = useUpdateSeries();
    const deleteMutation = useDeleteSeries();

    const handleOpenCreate = () => {
        setEditingSeries(null);
        setFormData({
            name: "",
            slug: "",
            category_slug: selectedCategory !== "__all__" ? selectedCategory : "",
            description_short: "",
            order: 0,
            is_featured: false,
            cover_media: null,
        });
        setFormOpen(true);
    };

    const handleOpenEdit = (s: AdminSeries) => {
        setEditingSeries(s);
        setFormData({
            name: s.name,
            slug: s.slug,
            category_slug: s.category_slug,
            description_short: s.description_short || "",
            order: s.order,
            is_featured: s.is_featured,
            cover_media: s.cover_media,
        });
        setFormOpen(true);
    };

    const handleOpenDelete = (s: AdminSeries) => {
        setDeletingSeries(s);
        setDeleteDialogOpen(true);
    };

    const handleSubmit = async () => {
        try {
            if (editingSeries) {
                await updateMutation.mutateAsync({
                    slug: editingSeries.slug,
                    payload: formData as UpdateSeriesPayload,
                });
                toast({ title: "Seri güncellendi" });
            } else {
                await createMutation.mutateAsync(formData);
                toast({ title: "Seri oluşturuldu" });
            }
            setFormOpen(false);
        } catch (error) {
            toast({
                title: "Hata",
                description: "İşlem başarısız oldu",
                variant: "destructive",
            });
        }
    };

    const handleDelete = async () => {
        if (!deletingSeries) return;
        try {
            await deleteMutation.mutateAsync(deletingSeries.slug);
            toast({ title: "Seri silindi" });
            setDeleteDialogOpen(false);
        } catch (error) {
            toast({
                title: "Hata",
                description: "Silme işlemi başarısız oldu",
                variant: "destructive",
            });
        }
    };

    const isPending = createMutation.isPending || updateMutation.isPending;
    const isLoading = categoriesLoading || seriesLoading;

    // Group series by category for display
    const seriesList = series || [];

    return (
        <AppShell
            breadcrumbs={[
                { label: "Katalog", href: "/catalog/products" },
                { label: "Seriler" },
            ]}
        >
            <PageHeader
                title="Seri Yönetimi"
                description="Ürün serilerini kategorilere göre yönetin"
                actions={
                    <Button onClick={handleOpenCreate}>
                        <Plus className="h-4 w-4 mr-2" />
                        Yeni Seri
                    </Button>
                }
            />

            {/* Filter */}
            <div className="mb-6">
                <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                    <SelectTrigger className="w-[280px]">
                        <SelectValue placeholder="Kategori seçin" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="__all__">Tüm Kategoriler</SelectItem>
                        {categories?.map((cat) => (
                            <SelectItem key={cat.id} value={cat.slug}>
                                {cat.name}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>

            <Card className="border-stone-200 bg-white">
                <CardHeader className="pb-3">
                    <CardTitle className="text-lg text-stone-900 flex items-center gap-2">
                        <Layers className="h-5 w-5" />
                        Seriler
                        <Badge variant="secondary" className="ml-2">
                            {seriesList.length}
                        </Badge>
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="space-y-3">
                            {[...Array(6)].map((_, i) => (
                                <Skeleton key={i} className="h-16 w-full" />
                            ))}
                        </div>
                    ) : seriesList.length === 0 ? (
                        <div className="text-center py-12 text-stone-500">
                            <Package className="h-12 w-12 mx-auto mb-4 opacity-20" />
                            <p>Henüz seri eklenmemiş</p>
                            <Button
                                variant="outline"
                                className="mt-4"
                                onClick={handleOpenCreate}
                            >
                                <Plus className="h-4 w-4 mr-2" />
                                İlk Seriyi Ekle
                            </Button>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {seriesList.map((s) => (
                                <div
                                    key={s.id}
                                    className="flex items-center gap-4 p-4 rounded-lg border border-stone-100 hover:border-stone-200 hover:bg-stone-50 transition-colors group"
                                >
                                    {/* Cover */}
                                    <div className="w-14 h-14 rounded-lg bg-stone-100 flex items-center justify-center overflow-hidden border border-stone-200">
                                        {s.cover_media ? (
                                            <img
                                                src={getMediaUrl(s.cover_media)}
                                                alt={s.name}
                                                className="w-full h-full object-cover"
                                            />
                                        ) : (
                                            <Package className="h-6 w-6 text-stone-400" />
                                        )}
                                    </div>

                                    {/* Info */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <h3 className="font-medium text-stone-900">{s.name}</h3>
                                            {s.is_featured && (
                                                <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                                            )}
                                        </div>
                                        <p className="text-sm text-stone-500 truncate">
                                            {s.description_short || "Açıklama yok"}
                                        </p>
                                        <div className="flex items-center gap-2 mt-1">
                                            <Badge variant="outline" className="text-xs">
                                                {categories?.find(c => c.slug === s.category_slug)?.name || s.category_slug}
                                            </Badge>
                                            <span className="text-xs text-stone-400">Sıra: {s.order}</span>
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                                    <MoreHorizontal className="h-4 w-4" />
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                                <DropdownMenuItem onClick={() => handleOpenEdit(s)}>
                                                    <Edit2 className="h-4 w-4 mr-2" />
                                                    Düzenle
                                                </DropdownMenuItem>
                                                <DropdownMenuItem
                                                    onClick={() => handleOpenDelete(s)}
                                                    className="text-red-600 focus:text-red-600"
                                                >
                                                    <Trash2 className="h-4 w-4 mr-2" />
                                                    Sil
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Create/Edit Dialog */}
            <Dialog open={formOpen} onOpenChange={setFormOpen}>
                <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col p-0 gap-0">
                    <DialogHeader className="p-6 pb-2">
                        <DialogTitle>
                            {editingSeries ? "Seri Düzenle" : "Yeni Seri"}
                        </DialogTitle>
                        <DialogDescription>
                            {editingSeries
                                ? "Seri bilgilerini güncelleyin"
                                : "Yeni bir seri oluşturun"}
                        </DialogDescription>
                    </DialogHeader>

                    <div className="flex-1 overflow-y-auto px-6 py-2">
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="category">Kategori *</Label>
                                <Select
                                    value={formData.category_slug}
                                    onValueChange={(v) => setFormData({ ...formData, category_slug: v })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Kategori seçin" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {categories?.map((cat) => (
                                            <SelectItem key={cat.id} value={cat.slug}>
                                                {cat.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="name">Seri Adı *</Label>
                                    <Input
                                        id="name"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        placeholder="örn: 600 Serisi"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="slug">Slug</Label>
                                    <Input
                                        id="slug"
                                        value={formData.slug}
                                        onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                                        placeholder="otomatik oluşturulur"
                                    />
                                    <p className="text-xs text-stone-500">Boş bırakılırsa otomatik oluşturulur</p>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="description_short">Kısa Açıklama</Label>
                                <Textarea
                                    id="description_short"
                                    value={formData.description_short}
                                    onChange={(e) => setFormData({ ...formData, description_short: e.target.value })}
                                    placeholder="Seri açıklaması"
                                    rows={2}
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="order">Sıra</Label>
                                    <Input
                                        id="order"
                                        type="number"
                                        value={formData.order}
                                        onChange={(e) => setFormData({ ...formData, order: parseInt(e.target.value) || 0 })}
                                    />
                                </div>

                                <div className="flex items-center justify-between space-x-2 pt-6">
                                    <Label htmlFor="is_featured">Öne Çıkan</Label>
                                    <Switch
                                        id="is_featured"
                                        checked={formData.is_featured}
                                        onCheckedChange={(checked) => setFormData({ ...formData, is_featured: checked })}
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label>Kapak Görseli</Label>
                                <ImageUpload
                                    value={formData.cover_media || undefined}
                                    onChange={(val) => setFormData({ ...formData, cover_media: val })}
                                    currentImageUrl={getMediaUrl(formData.cover_media)}
                                />
                            </div>
                        </div>
                    </div>

                    <DialogFooter className="p-6 pt-2">
                        <Button variant="outline" onClick={() => setFormOpen(false)}>
                            İptal
                        </Button>
                        <Button
                            onClick={handleSubmit}
                            disabled={isPending || !formData.name || !formData.category_slug}
                        >
                            {isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                            {editingSeries ? "Güncelle" : "Oluştur"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation */}
            <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Seriyi Sil</AlertDialogTitle>
                        <AlertDialogDescription>
                            <strong>{deletingSeries?.name}</strong> serisini silmek istediğinizden emin misiniz?
                            Bu işlem geri alınamaz.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>İptal</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDelete}
                            className="bg-red-600 hover:bg-red-700"
                            disabled={deleteMutation.isPending}
                        >
                            {deleteMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                            Sil
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </AppShell >
    );
}
