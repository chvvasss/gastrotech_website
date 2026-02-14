"use client";

import { useState } from "react";
import { Plus, Edit2, Trash2, Search, Loader2 } from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import {
    useAdminSpecs,
    useCreateSpecKey,
    useUpdateSpecKey,
    useDeleteSpecKey,
} from "@/hooks/use-admin-specs";

export default function SpecKeysPage() {
    const { toast } = useToast();
    const [searchTerm, setSearchTerm] = useState("");
    const [formOpen, setFormOpen] = useState(false);
    const [editingKey, setEditingKey] = useState<any | null>(null);

    // Form state
    const [formData, setFormData] = useState({
        slug: "",
        label_tr: "",
        label_en: "",
        unit: "",
        value_type: "text",
        sort_order: 0,
    });

    const { data: specs = [], isLoading } = useAdminSpecs({ search: searchTerm });
    const createMutation = useCreateSpecKey();
    const updateMutation = useUpdateSpecKey();
    const deleteMutation = useDeleteSpecKey();

    const handleOpenCreate = () => {
        setEditingKey(null);
        setFormData({
            slug: "",
            label_tr: "",
            label_en: "",
            unit: "",
            value_type: "text",
            sort_order: 0,
        });
        setFormOpen(true);
    };

    const handleOpenEdit = (spec: any) => {
        setEditingKey(spec);
        setFormData({
            slug: spec.slug,
            label_tr: spec.label_tr,
            label_en: spec.label_en || "",
            unit: spec.unit || "",
            value_type: spec.value_type,
            sort_order: spec.sort_order,
        });
        setFormOpen(true);
    };

    const handleDelete = async (slug: string) => {
        if (!confirm("Bu özelliği silmek istediğinize emin misiniz?")) return;

        try {
            await deleteMutation.mutateAsync(slug);
            toast({ title: "Özellik silindi" });
        } catch {
            toast({
                title: "Hata",
                description: "Silme işlemi başarısız oldu",
                variant: "destructive",
            });
        }
    };

    const handleSubmit = async () => {
        try {
            const payload: any = {
                label_tr: formData.label_tr,
                label_en: formData.label_en || null,
                unit: formData.unit || null,
                value_type: formData.value_type,
                sort_order: Number(formData.sort_order),
            };

            // Slug only for create or if API allows update (usually not for primary keys, but slug here is ID-like)
            if (!editingKey) {
                payload.slug = formData.slug || undefined; // Let backend auto-generate if empty
            }

            if (editingKey) {
                await updateMutation.mutateAsync({
                    slug: editingKey.slug,
                    payload
                });
                toast({ title: "Özellik güncellendi" });
            } else {
                await createMutation.mutateAsync(payload);
                toast({ title: "Özellik oluşturuldu" });
            }
            setFormOpen(false);
        } catch {
            toast({
                title: "Hata",
                description: "İşlem başarısız oldu",
                variant: "destructive",
            });
        }
    };

    const isPending = createMutation.isPending || updateMutation.isPending;

    return (
        <AppShell
            breadcrumbs={[
                { label: "Katalog", href: "/catalog/products" },
                { label: "Teknik Özellikler" },
            ]}
        >
            <PageHeader
                title="Teknik Özellik Yönetimi"
                description="Ürünler için dinamik teknik özellik anahtarlarını yönetin"
                actions={
                    <Button onClick={handleOpenCreate}>
                        <Plus className="h-4 w-4 mr-2" />
                        Yeni Özellik
                    </Button>
                }
            />

            <div className="space-y-6">
                {/* Search */}
                <div className="relative max-w-sm">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
                    <Input
                        placeholder="Özellik ara..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 bg-white border-stone-200"
                    />
                </div>

                {/* List */}
                <Card className="border-stone-200 bg-white">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-lg text-stone-900">
                            Tanımlı Özellikler
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-20">Sıra</TableHead>
                                    <TableHead>Etiket (TR)</TableHead>
                                    <TableHead>Etiket (EN)</TableHead>
                                    <TableHead>Birim</TableHead>
                                    <TableHead>Veri Tipi</TableHead>
                                    <TableHead className="w-24 text-right">İşlemler</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {isLoading ? (
                                    <TableRow>
                                        <TableCell colSpan={6} className="h-24 text-center">
                                            <Loader2 className="h-6 w-6 animate-spin mx-auto text-stone-400" />
                                        </TableCell>
                                    </TableRow>
                                ) : specs.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={6} className="h-24 text-center text-stone-500">
                                            Özellik bulunamadı
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    specs.map((spec) => (
                                        <TableRow key={spec.id}>
                                            <TableCell className="font-mono text-stone-600">
                                                {spec.sort_order}
                                            </TableCell>
                                            <TableCell className="font-medium text-stone-900">
                                                {spec.label_tr}
                                                <div className="text-xs text-stone-400 font-mono mt-0.5">
                                                    {spec.slug}
                                                </div>
                                            </TableCell>
                                            <TableCell className="text-stone-600">
                                                {spec.label_en || "-"}
                                            </TableCell>
                                            <TableCell>
                                                {spec.unit ? (
                                                    <Badge variant="secondary" className="font-mono text-xs">
                                                        {spec.unit}
                                                    </Badge>
                                                ) : (
                                                    "-"
                                                )}
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="outline" className="capitalize">
                                                    {spec.value_type}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <div className="flex justify-end gap-2">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleOpenEdit(spec)}
                                                        className="h-8 w-8 p-0 text-stone-500 hover:text-stone-700"
                                                    >
                                                        <Edit2 className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleDelete(spec.slug)}
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
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>
                            {editingKey ? "Özelliği Düzenle" : "Yeni Özellik"}
                        </DialogTitle>
                        <DialogDescription>
                            Teknik özellik detaylarını girin.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Etiket (TR) *</Label>
                                <Input
                                    value={formData.label_tr}
                                    onChange={(e) => setFormData({ ...formData, label_tr: e.target.value })}
                                    placeholder="örn: Güç"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Etiket (EN)</Label>
                                <Input
                                    value={formData.label_en}
                                    onChange={(e) => setFormData({ ...formData, label_en: e.target.value })}
                                    placeholder="örn: Power"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Slug</Label>
                                <Input
                                    value={formData.slug}
                                    onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                                    placeholder="otomatik"
                                    disabled={!!editingKey}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Birim</Label>
                                <Input
                                    value={formData.unit}
                                    onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                                    placeholder="örn: kW"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Veri Tipi</Label>
                                <Select
                                    value={formData.value_type}
                                    onValueChange={(v) => setFormData({ ...formData, value_type: v })}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="text">Metin</SelectItem>
                                        <SelectItem value="int">Tamsayı</SelectItem>
                                        <SelectItem value="decimal">Ondalıklı Sayı</SelectItem>
                                        <SelectItem value="bool">Mantıksal (Var/Yok)</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label>Sıralama</Label>
                                <Input
                                    type="number"
                                    value={formData.sort_order}
                                    onChange={(e) => setFormData({ ...formData, sort_order: parseInt(e.target.value) || 0 })}
                                />
                            </div>
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setFormOpen(false)}>İptal</Button>
                        <Button onClick={handleSubmit} disabled={isPending}>
                            {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Kaydet
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </AppShell>
    );
}
