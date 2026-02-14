"use client";

import { useState, useRef } from "react";
import { Plus, Edit2, Trash2, Loader2, Upload, FileText, CheckCircle, XCircle } from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import {
    useAdminCategoryCatalogs,
    useCreateCategoryCatalog,
    useUpdateCategoryCatalog,
    useDeleteCategoryCatalog,
} from "@/hooks/use-admin-category-catalogs";
import { adminCategoriesApi } from "@/lib/api/admin-taxonomy";
import { adminCatalogApi } from "@/lib/api/admin-catalog";
import { useQuery } from "@tanstack/react-query";

function formatFileSize(bytes: number | null | undefined): string {
    if (!bytes) return "-";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function CategoryCatalogsPage() {
    const { toast } = useToast();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [formOpen, setFormOpen] = useState(false);
    const [editingItem, setEditingItem] = useState<any | null>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [filterCategory, setFilterCategory] = useState<string>("");

    const [formData, setFormData] = useState({
        category: "",
        title_tr: "",
        title_en: "",
        description: "",
        media: "",
        order: 0,
        published: true,
    });

    const { data: catalogs = [], isLoading } = useAdminCategoryCatalogs(
        filterCategory || undefined
    );
    const { data: categories = [] } = useQuery({
        queryKey: ["admin-categories-list", "root"],
        queryFn: () => adminCategoriesApi.list({ parent: "null" }),
    });

    const createMutation = useCreateCategoryCatalog();
    const updateMutation = useUpdateCategoryCatalog();
    const deleteMutation = useDeleteCategoryCatalog();

    const handleOpenCreate = () => {
        setEditingItem(null);
        setSelectedFile(null);
        setFormData({
            category: "",
            title_tr: "",
            title_en: "",
            description: "",
            media: "",
            order: 0,
            published: true,
        });
        setFormOpen(true);
    };

    const handleOpenEdit = (item: any) => {
        setEditingItem(item);
        setSelectedFile(null);
        setFormData({
            category: item.category,
            title_tr: item.title_tr,
            title_en: item.title_en || "",
            description: item.description || "",
            media: item.media,
            order: item.order,
            published: item.published,
        });
        setFormOpen(true);
    };

    const handleDelete = async (id: string, name: string) => {
        if (!confirm(`"${name}" katalogunu silmek istediginize emin misiniz?`)) return;
        try {
            await deleteMutation.mutateAsync(id);
            toast({ title: "Katalog silindi" });
        } catch {
            toast({ title: "Hata", description: "Silme basarisiz oldu", variant: "destructive" });
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            if (file.type !== "application/pdf") {
                toast({ title: "Hata", description: "Sadece PDF dosyalari yuklenebilir", variant: "destructive" });
                return;
            }
            setSelectedFile(file);
        }
    };

    const handleSubmit = async () => {
        if (!formData.category) {
            toast({ title: "Hata", description: "Kategori seciniz", variant: "destructive" });
            return;
        }
        if (!formData.title_tr) {
            toast({ title: "Hata", description: "Baslik giriniz", variant: "destructive" });
            return;
        }

        let mediaId = formData.media;

        // Upload file if selected
        if (selectedFile) {
            setIsUploading(true);
            try {
                const uploadResult = await adminCatalogApi.mediaUpload(selectedFile);
                mediaId = uploadResult.id;
            } catch {
                toast({ title: "Hata", description: "Dosya yukleme basarisiz", variant: "destructive" });
                setIsUploading(false);
                return;
            }
            setIsUploading(false);
        }

        if (!mediaId && !editingItem) {
            toast({ title: "Hata", description: "PDF dosyasi yukleyin", variant: "destructive" });
            return;
        }

        try {
            if (editingItem) {
                await updateMutation.mutateAsync({
                    id: editingItem.id,
                    data: {
                        ...formData,
                        ...(mediaId ? { media: mediaId } : {}),
                    },
                });
                toast({ title: "Katalog guncellendi" });
            } else {
                await createMutation.mutateAsync({
                    ...formData,
                    media: mediaId,
                });
                toast({ title: "Katalog oluşturuldu" });
            }
            setFormOpen(false);
        } catch (err: any) {
            toast({
                title: "Hata",
                description: err?.response?.data?.detail || "Islem basarisiz oldu",
                variant: "destructive",
            });
        }
    };

    const isSaving = createMutation.isPending || updateMutation.isPending || isUploading;

    return (
        <AppShell breadcrumbs={[{ label: "Katalog", href: "/catalog/products" }, { label: "Kategori Kataloglari" }]}>
            <PageHeader
                title="Kategori Kataloglari"
                description="Kategorilere atanan PDF katalog dosyalarini yonetin. Katalog modu acik oldugunda bu dosyalar sitede gorunur."
                actions={
                    <Button onClick={handleOpenCreate}>
                        <Plus className="mr-2 h-4 w-4" />
                        Yeni Katalog
                    </Button>
                }
            />

            {/* Filter */}
            <div className="mb-4 flex items-center gap-4">
                <div className="w-64">
                    <Select value={filterCategory || "all"} onValueChange={(val) => setFilterCategory(val === "all" ? "" : val)}>
                        <SelectTrigger>
                            <SelectValue placeholder="Tum Kategoriler" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">Tum Kategoriler</SelectItem>
                            {categories.map((cat: any) => (
                                <SelectItem key={cat.slug} value={cat.slug}>
                                    {cat.name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <Card>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Kategori</TableHead>
                                <TableHead>Baslik</TableHead>
                                <TableHead>Dosya</TableHead>
                                <TableHead>Boyut</TableHead>
                                <TableHead>Sira</TableHead>
                                <TableHead>Durum</TableHead>
                                <TableHead className="w-[100px]">Islemler</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading ? (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center py-8">
                                        <Loader2 className="h-6 w-6 animate-spin mx-auto text-muted-foreground" />
                                    </TableCell>
                                </TableRow>
                            ) : catalogs.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                                        Henuz katalog eklenmemis.
                                    </TableCell>
                                </TableRow>
                            ) : (
                                catalogs.map((item: any) => (
                                    <TableRow key={item.id}>
                                        <TableCell className="font-medium">{item.category_name}</TableCell>
                                        <TableCell>{item.title_tr}</TableCell>
                                        <TableCell>
                                            {item.media_details ? (
                                                <a
                                                    href={item.media_details.file_url}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    className="flex items-center gap-1.5 text-primary hover:underline text-sm"
                                                >
                                                    <FileText className="h-3.5 w-3.5" />
                                                    {item.media_details.filename}
                                                </a>
                                            ) : (
                                                "-"
                                            )}
                                        </TableCell>
                                        <TableCell className="text-muted-foreground text-sm">
                                            {formatFileSize(item.media_details?.size_bytes)}
                                        </TableCell>
                                        <TableCell>{item.order}</TableCell>
                                        <TableCell>
                                            {item.published ? (
                                                <Badge variant="default" className="bg-green-600">
                                                    <CheckCircle className="mr-1 h-3 w-3" />
                                                    Yayinda
                                                </Badge>
                                            ) : (
                                                <Badge variant="secondary">
                                                    <XCircle className="mr-1 h-3 w-3" />
                                                    Taslak
                                                </Badge>
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-1">
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={() => handleOpenEdit(item)}
                                                >
                                                    <Edit2 className="h-4 w-4" />
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={() => handleDelete(item.id, item.title_tr)}
                                                >
                                                    <Trash2 className="h-4 w-4 text-destructive" />
                                                </Button>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Create/Edit Dialog */}
            <Dialog open={formOpen} onOpenChange={setFormOpen}>
                <DialogContent className="sm:max-w-lg">
                    <DialogHeader>
                        <DialogTitle>
                            {editingItem ? "Katalogu Duzenle" : "Yeni Katalog Ekle"}
                        </DialogTitle>
                        <DialogDescription>
                            Kategoriye PDF katalog dosyasi atayin.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="grid gap-4 py-4">
                        <div className="space-y-2">
                            <Label>Kategori *</Label>
                            <Select
                                value={formData.category || undefined}
                                onValueChange={(val) => setFormData({ ...formData, category: val })}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Kategori seciniz" />
                                </SelectTrigger>
                                <SelectContent>
                                    {categories.map((cat: any) => (
                                        <SelectItem key={cat.id} value={cat.id}>
                                            {cat.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label>Baslik (TR) *</Label>
                            <Input
                                value={formData.title_tr}
                                onChange={(e) => setFormData({ ...formData, title_tr: e.target.value })}
                                placeholder="Katalog basligi"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Baslik (EN)</Label>
                            <Input
                                value={formData.title_en}
                                onChange={(e) => setFormData({ ...formData, title_en: e.target.value })}
                                placeholder="Catalog title"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Aciklama</Label>
                            <Textarea
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                placeholder="Opsiyonel aciklama"
                                rows={2}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>PDF Dosyasi {!editingItem && "*"}</Label>
                            <div className="flex items-center gap-2">
                                <Input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="application/pdf"
                                    onChange={handleFileChange}
                                    className="flex-1"
                                />
                            </div>
                            {selectedFile && (
                                <p className="text-xs text-muted-foreground">
                                    Secilen: {selectedFile.name} ({formatFileSize(selectedFile.size)})
                                </p>
                            )}
                            {editingItem?.media_details && !selectedFile && (
                                <p className="text-xs text-muted-foreground">
                                    Mevcut: {editingItem.media_details.filename}
                                </p>
                            )}
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Siralama</Label>
                                <Input
                                    type="number"
                                    min={0}
                                    value={formData.order}
                                    onChange={(e) => setFormData({ ...formData, order: parseInt(e.target.value) || 0 })}
                                />
                            </div>
                            <div className="flex items-center gap-2 pt-6">
                                <Switch
                                    checked={formData.published}
                                    onCheckedChange={(checked) => setFormData({ ...formData, published: checked })}
                                />
                                <Label>Yayinda</Label>
                            </div>
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setFormOpen(false)}>
                            Iptal
                        </Button>
                        <Button onClick={handleSubmit} disabled={isSaving}>
                            {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {editingItem ? "Guncelle" : "Olustur"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </AppShell>
    );
}
