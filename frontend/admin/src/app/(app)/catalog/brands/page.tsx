"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
    Plus,
    Edit2,
    Trash2,
    Loader2,
    MoreHorizontal,
    Tag,
    ExternalLink,
    Check,
    X,
    Folder,
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
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import {
    useBrands,
    useCreateBrand,
    useUpdateBrand,
    useDeleteBrand,
} from "@/hooks/use-admin-brands";
import type { AdminBrand, CreateBrandPayload, UpdateBrandPayload } from "@/lib/api/admin-brands";

const getMediaUrl = (id?: string | null) => {
    if (!id) return undefined;
    return `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/media/${id}/file/`;
};

export default function BrandsPage() {
    const router = useRouter();
    const { toast } = useToast();
    const [formOpen, setFormOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [editingBrand, setEditingBrand] = useState<AdminBrand | null>(null);
    const [deletingBrand, setDeletingBrand] = useState<AdminBrand | null>(null);

    // Form state
    const [formData, setFormData] = useState<CreateBrandPayload>({
        name: "",
        slug: "",
        description: "",
        is_active: true,
        order: 0,
        logo_media: null,
    });

    const { data: brands, isLoading } = useBrands();
    const createMutation = useCreateBrand();
    const updateMutation = useUpdateBrand();
    const deleteMutation = useDeleteBrand();

    const handleOpenCreate = () => {
        setEditingBrand(null);
        setFormData({
            name: "",
            slug: "",
            description: "",
            is_active: true,
            order: 0,
            logo_media: null,
        });
        setFormOpen(true);
    };

    const handleOpenEdit = (brand: AdminBrand) => {
        setEditingBrand(brand);
        setFormData({
            name: brand.name,
            slug: brand.slug,
            description: brand.description || "",
            is_active: brand.is_active,
            order: brand.order,
            logo_media: brand.logo_media,
        });
        setFormOpen(true);
    };

    const handleOpenDelete = (brand: AdminBrand) => {
        setDeletingBrand(brand);
        setDeleteDialogOpen(true);
    };

    const handleSubmit = async () => {
        try {
            if (editingBrand) {
                await updateMutation.mutateAsync({
                    slug: editingBrand.slug,
                    payload: formData as UpdateBrandPayload,
                });
                toast({ title: "Marka güncellendi" });
            } else {
                await createMutation.mutateAsync(formData);
                toast({ title: "Marka oluşturuldu" });
            }
            setFormOpen(false);
        } catch (error: any) {
            console.error("Brand save error:", error);
            const message = error.response?.data?.detail ||
                (typeof error.response?.data === 'object' ? JSON.stringify(error.response?.data) : error.response?.data) ||
                error.message ||
                "İşlem başarısız oldu";
            toast({
                title: "Hata",
                description: message,
                variant: "destructive",
            });
        }
    };

    const handleDelete = async () => {
        if (!deletingBrand) return;
        try {
            await deleteMutation.mutateAsync(deletingBrand.slug);
            toast({ title: "Marka silindi" });
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

    return (
        <AppShell
            breadcrumbs={[
                { label: "Katalog", href: "/catalog/products" },
                { label: "Markalar" },
            ]}
        >
            <PageHeader
                title="Marka Yönetimi"
                description="Ürün markalarını yönetin"
                actions={
                    <Button onClick={handleOpenCreate}>
                        <Plus className="h-4 w-4 mr-2" />
                        Yeni Marka
                    </Button>
                }
            />

            <Card className="border-stone-200 bg-white">
                <CardHeader className="pb-3">
                    <CardTitle className="text-lg text-stone-900">Markalar</CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="space-y-2">
                            {[...Array(4)].map((_, i) => (
                                <Skeleton key={i} className="h-12 w-full" />
                            ))}
                        </div>
                    ) : !brands || brands.length === 0 ? (
                        <div className="text-center py-12 text-stone-500">
                            <Tag className="h-12 w-12 mx-auto mb-4 opacity-20" />
                            <p>Henüz marka eklenmemiş</p>
                            <Button
                                variant="outline"
                                className="mt-4"
                                onClick={handleOpenCreate}
                            >
                                <Plus className="h-4 w-4 mr-2" />
                                İlk Markayı Ekle
                            </Button>
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Logo</TableHead>
                                    <TableHead>Marka Adı</TableHead>
                                    <TableHead>Slug</TableHead>
                                    <TableHead>Ürün Sayısı</TableHead>
                                    <TableHead>Durum</TableHead>
                                    <TableHead>Sıra</TableHead>
                                    <TableHead className="text-right">İşlemler</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {brands.map((brand) => (
                                    <TableRow key={brand.id}>
                                        <TableCell>
                                            {brand.logo_media_url ? (
                                                <div className="h-10 w-10 rounded overflow-hidden border border-stone-200">
                                                    <img
                                                        src={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${brand.logo_media_url}`}
                                                        alt={brand.name}
                                                        className="h-full w-full object-contain"
                                                    />
                                                </div>
                                            ) : (
                                                <div className="h-10 w-10 rounded bg-stone-100 flex items-center justify-center">
                                                    <Tag className="h-5 w-5 text-stone-400" />
                                                </div>
                                            )}
                                        </TableCell>
                                        <TableCell className="font-medium">
                                            {brand.name}
                                        </TableCell>
                                        <TableCell className="text-stone-500 font-mono text-sm">
                                            {brand.slug}
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant="secondary">
                                                {brand.products_count || 0} ürün
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            {brand.is_active ? (
                                                <Badge className="bg-green-100 text-green-700">
                                                    <Check className="h-3 w-3 mr-1" />
                                                    Aktif
                                                </Badge>
                                            ) : (
                                                <Badge variant="secondary">
                                                    <X className="h-3 w-3 mr-1" />
                                                    Pasif
                                                </Badge>
                                            )}
                                        </TableCell>
                                        <TableCell className="text-stone-400">
                                            #{brand.order}
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="icon" className="h-8 w-8">
                                                        <MoreHorizontal className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuItem onClick={() => router.push(`/catalog/brands/${brand.slug}`)}>
                                                        <Folder className="h-4 w-4 mr-2" />
                                                        Kategorileri Görüntüle
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem onClick={() => handleOpenEdit(brand)}>
                                                        <Edit2 className="h-4 w-4 mr-2" />
                                                        Düzenle
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem
                                                        onClick={() => handleOpenDelete(brand)}
                                                        className="text-red-600 focus:text-red-600"
                                                    >
                                                        <Trash2 className="h-4 w-4 mr-2" />
                                                        Sil
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </CardContent>
            </Card>

            {/* Create/Edit Dialog */}
            <Dialog open={formOpen} onOpenChange={setFormOpen}>
                <DialogContent className="max-w-lg max-h-[90vh] flex flex-col">
                    <DialogHeader>
                        <DialogTitle>
                            {editingBrand ? "Marka Düzenle" : "Yeni Marka"}
                        </DialogTitle>
                        <DialogDescription>
                            {editingBrand
                                ? "Marka bilgilerini güncelleyin"
                                : "Yeni bir marka oluşturun"}
                        </DialogDescription>
                    </DialogHeader>

                    <div className="flex-1 overflow-y-auto py-4 px-1">
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="name">Marka Adı *</Label>
                                    <Input
                                        id="name"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        placeholder="örn: Gastrotech"
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
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="description">Açıklama</Label>
                                <Textarea
                                    id="description"
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    placeholder="Marka açıklaması"
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
                                    <Label htmlFor="is_active">Aktif</Label>
                                    <Switch
                                        id="is_active"
                                        checked={formData.is_active}
                                        onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label>Logo</Label>
                                <ImageUpload
                                    value={formData.logo_media || undefined}
                                    onChange={(val) => setFormData({ ...formData, logo_media: val })}
                                    currentImageUrl={getMediaUrl(formData.logo_media)}
                                />
                            </div>
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setFormOpen(false)}>
                            İptal
                        </Button>
                        <Button onClick={handleSubmit} disabled={isPending || !formData.name}>
                            {isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                            {editingBrand ? "Güncelle" : "Oluştur"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation */}
            <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Markayı Sil</AlertDialogTitle>
                        <AlertDialogDescription>
                            <strong>{deletingBrand?.name}</strong> markasını silmek istediğinizden emin misiniz?
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
        </AppShell>
    );
}
