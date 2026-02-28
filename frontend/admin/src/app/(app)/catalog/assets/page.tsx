"use client";

import { useState, useRef } from "react";
import { Plus, Edit2, Trash2, Loader2, Upload, FileText, CheckCircle, XCircle } from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
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
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import {
    useAdminAssets,
    useCreateCatalogAsset,
    useUpdateCatalogAsset,
    useDeleteCatalogAsset,
    useRefUploadMedia
} from "@/hooks/use-admin-assets";

export default function CatalogAssetsPage() {
    const { toast } = useToast();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [formOpen, setFormOpen] = useState(false);
    const [editingAsset, setEditingAsset] = useState<any | null>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);

    // Form state
    const [formData, setFormData] = useState({
        title_tr: "",
        title_en: "",
        is_primary: false,
        published: true,
        order: 0,
        media_id: "",
    });

    const { data: assets = [], isLoading } = useAdminAssets();
    const createMutation = useCreateCatalogAsset();
    const updateMutation = useUpdateCatalogAsset();
    const deleteMutation = useDeleteCatalogAsset();
    const uploadMutation = useRefUploadMedia();

    const handleOpenCreate = () => {
        setEditingAsset(null);
        setSelectedFile(null);
        setFormData({
            title_tr: "",
            title_en: "",
            is_primary: false,
            published: true,
            order: 0,
            media_id: "",
        });
        setFormOpen(true);
    };

    const handleOpenEdit = (asset: any) => {
        setEditingAsset(asset);
        setSelectedFile(null);
        setFormData({
            title_tr: asset.title_tr,
            title_en: asset.title_en || "",
            is_primary: asset.is_primary,
            published: asset.published,
            order: asset.order,
            media_id: asset.media,
        });
        setFormOpen(true);
    };

    const handleDelete = async (id: string, name: string) => {
        if (!confirm(`"${name}" kataloğunu silmek istediğinize emin misiniz?`)) return;

        try {
            await deleteMutation.mutateAsync(id);
            toast({ title: "Katalog silindi" });
        } catch {
            toast({
                title: "Hata",
                description: "Silme işlemi başarısız oldu",
                variant: "destructive",
            });
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedFile(e.target.files[0]);
        }
    };

    const handleSubmit = async () => {
        if (!formData.title_tr) {
            toast({ title: "Başlık zorunludur", variant: "destructive" });
            return;
        }

        try {
            let mediaId = formData.media_id;

            // Handle file upload if new file selected
            if (selectedFile) {
                setIsUploading(true);
                const uploadRes = await uploadMutation.mutateAsync(selectedFile);
                mediaId = uploadRes.data.id;
                setIsUploading(false);
            }

            if (!mediaId && !editingAsset) {
                toast({ title: "Lütfen bir PDF dosyası yükleyin", variant: "destructive" });
                return;
            }

            const payload = {
                title_tr: formData.title_tr,
                title_en: formData.title_en || undefined,
                is_primary: formData.is_primary,
                published: formData.published,
                order: Number(formData.order),
                media: mediaId,
            };

            if (editingAsset) {
                await updateMutation.mutateAsync({
                    id: editingAsset.id,
                    payload
                });
                toast({ title: "Katalog güncellendi" });
            } else {
                await createMutation.mutateAsync(payload);
                toast({ title: "Katalog oluşturuldu" });
            }
            setFormOpen(false);
        } catch {
            setIsUploading(false);
            toast({
                title: "Hata",
                description: "İşlem başarısız oldu",
                variant: "destructive",
            });
        }
    };

    const isPending = createMutation.isPending || updateMutation.isPending || isUploading;

    return (
        <AppShell
            breadcrumbs={[
                { label: "İçerik Yönetimi", href: "/blog" },
                { label: "Katalog Dosyaları" },
            ]}
        >
            <PageHeader
                title="Katalog Dosyaları (PDF)"
                description="İndirilebilir PDF katalog dosyalarını yönetin"
                actions={
                    <Button onClick={handleOpenCreate}>
                        <Plus className="h-4 w-4 mr-2" />
                        Yeni Katalog
                    </Button>
                }
            />

            <div className="space-y-6">
                {/* List */}
                <Card className="border-stone-200 bg-white">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-lg text-stone-900">
                            Yüklü Kataloglar
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-20">Sıra</TableHead>
                                    <TableHead>Başlık (TR)</TableHead>
                                    <TableHead>Dosya Adı</TableHead>
                                    <TableHead>Durum</TableHead>
                                    <TableHead className="w-24 text-right">İşlemler</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {isLoading ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="h-24 text-center">
                                            <Loader2 className="h-6 w-6 animate-spin mx-auto text-stone-400" />
                                        </TableCell>
                                    </TableRow>
                                ) : assets.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="h-24 text-center text-stone-500">
                                            Katalog dosyası bulunamadı
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    assets.map((asset) => (
                                        <TableRow key={asset.id}>
                                            <TableCell className="font-mono text-stone-600">
                                                {asset.order}
                                            </TableCell>
                                            <TableCell className="font-medium text-stone-900">
                                                {asset.title_tr}
                                                {asset.is_primary && (
                                                    <Badge className="ml-2 bg-blue-100 text-blue-700 hover:bg-blue-100 border-blue-200">
                                                        Ana Katalog
                                                    </Badge>
                                                )}
                                                <div className="text-xs text-stone-400 mt-0.5">
                                                    {asset.title_en}
                                                </div>
                                            </TableCell>
                                            <TableCell className="text-stone-600">
                                                <div className="flex items-center gap-2">
                                                    <FileText className="h-4 w-4 text-red-500" />
                                                    <span className="truncate max-w-[200px]">
                                                        {asset.media_details?.filename || "Dosya"}
                                                    </span>
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                {asset.published ? (
                                                    <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                                                        Yayında
                                                    </Badge>
                                                ) : (
                                                    <Badge variant="outline" className="bg-stone-50 text-stone-500 border-stone-200">
                                                        Taslak
                                                    </Badge>
                                                )}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <div className="flex justify-end gap-2">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleOpenEdit(asset)}
                                                        className="h-8 w-8 p-0 text-stone-500 hover:text-stone-700"
                                                    >
                                                        <Edit2 className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleDelete(asset.id, asset.title_tr)}
                                                        className="h-8 w-8 p-0 text-stone-500 hover:text-red-600"
                                                    >
                                                        <Trash2 className="h-4 w-4" />
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
            </div>

            {/* Form Dialog */}
            <Dialog open={formOpen} onOpenChange={setFormOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>
                            {editingAsset ? "Katalog Düzenle" : "Yeni Katalog"}
                        </DialogTitle>
                        <DialogDescription>
                            PDF katalog dosyasını yükleyin ve detaylarını girin.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Başlık (TR) *</Label>
                                <Input
                                    value={formData.title_tr}
                                    onChange={(e) => setFormData({ ...formData, title_tr: e.target.value })}
                                    placeholder="örn: 2024 Genel Katalog"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Başlık (EN)</Label>
                                <Input
                                    value={formData.title_en}
                                    onChange={(e) => setFormData({ ...formData, title_en: e.target.value })}
                                    placeholder="örn: 2024 General Catalog"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>PDF Dosyası {editingAsset && "(Değiştirmek için yükleyin)"}</Label>
                            <div
                                className="border-2 border-dashed border-stone-200 rounded-lg p-6 text-center hover:border-primary/50 transition-colors cursor-pointer bg-stone-50"
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="application/pdf"
                                    onChange={handleFileChange}
                                    className="hidden"
                                />
                                {selectedFile ? (
                                    <div className="flex items-center justify-center gap-2 text-primary font-medium">
                                        <FileText className="h-5 w-5" />
                                        {selectedFile.name}
                                    </div>
                                ) : (
                                    <div className="text-stone-500">
                                        <Upload className="h-8 w-8 mx-auto mb-2 text-stone-400" />
                                        <p className="text-sm">PDF dosyası seçmek için tıklayın</p>
                                    </div>
                                )}
                            </div>
                            {editingAsset && !selectedFile && (
                                <p className="text-xs text-stone-500 mt-1">
                                    Mevcut dosya koruncak.
                                </p>
                            )}
                        </div>

                        <div className="flex items-center gap-6 py-2">
                            <div className="flex items-center space-x-2">
                                <Checkbox
                                    id="is_primary"
                                    checked={formData.is_primary}
                                    onCheckedChange={(c) => setFormData({ ...formData, is_primary: !!c })}
                                />
                                <Label htmlFor="is_primary" className="cursor-pointer">Ana Katalog</Label>
                            </div>

                            <div className="flex items-center space-x-2">
                                <Checkbox
                                    id="published"
                                    checked={formData.published}
                                    onCheckedChange={(c) => setFormData({ ...formData, published: !!c })}
                                />
                                <Label htmlFor="published" className="cursor-pointer">Yayında</Label>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Sıralama</Label>
                            <Input
                                type="number"
                                value={formData.order}
                                onChange={(e) => setFormData({ ...formData, order: parseInt(e.target.value) || 0 })}
                            />
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setFormOpen(false)}>İptal</Button>
                        <Button onClick={handleSubmit} disabled={isPending}>
                            {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {isPending ? "Yükleniyor..." : "Kaydet"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </AppShell>
    );
}
