"use client";

import { useState } from "react";
import { Plus, Edit2, Trash2, Loader2, List, FileText } from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
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
import { adminTemplatesApi } from "@/lib/api/admin-templates";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { SpecTemplate } from "@/types/api";

export default function SpecTemplatesPage() {
    const { toast } = useToast();
    const queryClient = useQueryClient();

    const [formOpen, setFormOpen] = useState(false);
    const [editingTemplate, setEditingTemplate] = useState<SpecTemplate | null>(null);
    const [formData, setFormData] = useState({
        name: "",
        spec_layout: "", // Comma separated slugs
        default_general_features: "", // Newline separated
        default_notes: "",
    });

    // --- Queries ---
    const { data: response, isLoading } = useQuery({
        queryKey: ["admin-spec-templates"],
        queryFn: () => adminTemplatesApi.list(),
    });

    const templates = response?.data?.results || [];

    // --- Mutations ---
    const createMutation = useMutation({
        mutationFn: adminTemplatesApi.create,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-spec-templates"] });
            toast({ title: "Şablon oluşturuldu" });
            setFormOpen(false);
        },
        onError: () => toast({ title: "Hata", description: "Şablon oluşturulamadı", variant: "destructive" }),
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: any }) => adminTemplatesApi.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-spec-templates"] });
            toast({ title: "Şablon güncellendi" });
            setFormOpen(false);
        },
        onError: () => toast({ title: "Hata", description: "Güncelleme başarısız", variant: "destructive" }),
    });

    const deleteMutation = useMutation({
        mutationFn: adminTemplatesApi.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-spec-templates"] });
            toast({ title: "Şablon silindi" });
        },
    });

    // --- Handlers ---
    const handleOpenCreate = () => {
        setEditingTemplate(null);
        setFormData({
            name: "",
            spec_layout: "",
            default_general_features: "",
            default_notes: "",
        });
        setFormOpen(true);
    };

    const handleOpenEdit = (template: SpecTemplate) => {
        setEditingTemplate(template);
        setFormData({
            name: template.name,
            spec_layout: template.spec_layout?.join(", ") || "",
            default_general_features: template.default_general_features?.join("\n") || "",
            default_notes: template.default_notes || "",
        });
        setFormOpen(true);
    };

    const handleDelete = async (id: string, name: string) => {
        if (!confirm(`"${name}" şablonunu silmek istediğinize emin misiniz?`)) return;
        deleteMutation.mutate(id);
    };

    const handleSubmit = () => {
        if (!formData.name) return;

        const payload = {
            name: formData.name,
            spec_layout: formData.spec_layout.split(",").map(s => s.trim()).filter(Boolean),
            default_general_features: formData.default_general_features.split("\n").map(s => s.trim()).filter(Boolean),
            default_notes: formData.default_notes,
        };

        if (editingTemplate) {
            updateMutation.mutate({ id: editingTemplate.id, data: payload });
        } else {
            createMutation.mutate(payload);
        }
    };

    const isPending = createMutation.isPending || updateMutation.isPending;

    return (
        <AppShell
            breadcrumbs={[
                { label: "Katalog", href: "/catalog" },
                { label: "Özellik Şablonları" },
            ]}
        >
            <PageHeader
                title="Özellik Şablonları"
                description="Ürün girişi için hazır özellik setleri tanımlayın"
                actions={
                    <Button onClick={handleOpenCreate}>
                        <Plus className="h-4 w-4 mr-2" />
                        Yeni Şablon
                    </Button>
                }
            />

            <div className="space-y-6">
                <Card className="border-stone-200 bg-white">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-lg text-stone-900">
                            Tanımlı Şablonlar
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Şablon Adı</TableHead>
                                    <TableHead>Özellik Sayısı</TableHead>
                                    <TableHead>Varsayılan İçerik</TableHead>
                                    <TableHead className="w-24 text-right">İşlemler</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {isLoading ? (
                                    <TableRow>
                                        <TableCell colSpan={4} className="h-24 text-center">
                                            <Loader2 className="h-6 w-6 animate-spin mx-auto text-stone-400" />
                                        </TableCell>
                                    </TableRow>
                                ) : templates.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={4} className="h-24 text-center text-stone-500">
                                            Henüz şablon oluşturulmamış
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    templates.map((template) => (
                                        <TableRow key={template.id}>
                                            <TableCell className="font-medium text-stone-900">
                                                <div className="flex items-center gap-2">
                                                    <List className="h-4 w-4 text-blue-500" />
                                                    {template.name}
                                                </div>
                                            </TableCell>
                                            <TableCell className="text-stone-600">
                                                <Badge variant="outline" className="font-mono">
                                                    {template.spec_layout?.length || 0} Özellik
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-stone-500 text-sm">
                                                <div className="flex gap-2">
                                                    {template.default_general_features && template.default_general_features.length > 0 && (
                                                        <Badge variant="secondary" className="bg-stone-100">
                                                            +Genel Özellikler
                                                        </Badge>
                                                    )}
                                                    {template.default_notes && (
                                                        <Badge variant="secondary" className="bg-stone-100">
                                                            +Notlar
                                                        </Badge>
                                                    )}
                                                </div>
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <div className="flex justify-end gap-2">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleOpenEdit(template)}
                                                        className="h-8 w-8 p-0 text-stone-500 hover:text-stone-700"
                                                    >
                                                        <Edit2 className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleDelete(template.id, template.name)}
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
                <DialogContent className="max-w-xl">
                    <DialogHeader>
                        <DialogTitle>
                            {editingTemplate ? "Şablonu Düzenle" : "Yeni Şablon"}
                        </DialogTitle>
                        <DialogDescription>
                            Hızlı ürün girişi için özellik seti ve varsayılan içerikler tanımlayın.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Şablon Adı *</Label>
                            <Input
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                placeholder="örn: Gazlı Ocak Standart Şablonu"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Özellik Anahtarları (Spec Layout)</Label>
                            <div className="text-xs text-stone-500 mb-1">
                                Virgülle ayırarak slug kodlarını girin (örn: power, capacity, dims).
                            </div>
                            <Textarea
                                className="font-mono text-sm"
                                rows={3}
                                value={formData.spec_layout}
                                onChange={(e) => setFormData({ ...formData, spec_layout: e.target.value })}
                                placeholder="power, capacity, dimensions, weight_kg"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Varsayılan Genel Özellikler</Label>
                            <div className="text-xs text-stone-500 mb-1">
                                Her satıra bir özellik girin (Maddeler halinde görünür).
                            </div>
                            <Textarea
                                rows={4}
                                value={formData.default_general_features}
                                onChange={(e) => setFormData({ ...formData, default_general_features: e.target.value })}
                                placeholder="Paslanmaz çelik gövde&#10;Ergonomik tasarım&#10;Yüksek verimli brülörler"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Varsayılan Notlar</Label>
                            <Textarea
                                rows={2}
                                value={formData.default_notes}
                                onChange={(e) => setFormData({ ...formData, default_notes: e.target.value })}
                                placeholder="Tüplü ve doğalgazlı seçenekleri mevcuttur."
                            />
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setFormOpen(false)}>İptal</Button>
                        <Button onClick={handleSubmit} disabled={isPending}>
                            {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {isPending ? "Kaydediliyor..." : "Kaydet"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </AppShell>
    );
}
