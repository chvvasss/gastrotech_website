"use client";

import { useState } from "react";
import { PageHeader, AppShell } from "@/components/layout";
import { DataTable } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Plus, Edit, Trash2 } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
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
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { useBlogCategories, useCreateBlogCategory, useUpdateBlogCategory, useDeleteBlogCategory } from "@/hooks/use-blog";
import { ColumnDef } from "@tanstack/react-table";
import { BlogCategory } from "@/lib/api/blog";

export default function BlogCategoriesPage() {
    const { data, isLoading } = useBlogCategories();
    const createMutation = useCreateBlogCategory();
    const updateMutation = useUpdateBlogCategory();
    const deleteMutation = useDeleteBlogCategory();

    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [editingCategory, setEditingCategory] = useState<BlogCategory | null>(null);
    const [deleteId, setDeleteId] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        name_tr: "",
        description: "",
        order: 0,
        is_active: true,
    });

    const handleCreate = () => {
        setEditingCategory(null);
        setFormData({ name_tr: "", description: "", order: 0, is_active: true });
        setIsDialogOpen(true);
    };

    const handleEdit = (category: BlogCategory) => {
        setEditingCategory(category);
        setFormData({
            name_tr: category.name_tr,
            description: category.description || "",
            order: category.order,
            is_active: category.is_active,
        });
        setIsDialogOpen(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (editingCategory) {
                await updateMutation.mutateAsync({
                    id: editingCategory.id,
                    data: formData,
                });
            } else {
                await createMutation.mutateAsync(formData);
            }
            setIsDialogOpen(false);
        } catch (error) {
            // Error handled in hook
        }
    };

    const handleDelete = async () => {
        if (deleteId) {
            await deleteMutation.mutateAsync(deleteId);
            setDeleteId(null);
        }
    };

    const columns: ColumnDef<BlogCategory>[] = [
        {
            accessorKey: "order",
            header: "Sıra",
            cell: ({ row }) => <span className="font-mono text-sm">{row.original.order}</span>,
        },
        {
            accessorKey: "name_tr",
            header: "Kategori Adı",
            cell: ({ row }) => (
                <div>
                    <div className="font-medium">{row.original.name_tr}</div>
                    <div className="text-xs text-muted-foreground">{row.original.slug}</div>
                </div>
            ),
        },
        {
            accessorKey: "description",
            header: "Açıklama",
            cell: ({ row }) => (
                <div className="max-w-md truncate text-muted-foreground">{row.original.description}</div>
            ),
        },
        {
            accessorKey: "posts_count",
            header: "Yazı Sayısı",
            cell: ({ row }) => (
                <Badge variant="secondary" className="font-normal">
                    {row.original.posts_count || 0} Yazı
                </Badge>
            ),
        },
        {
            accessorKey: "is_active",
            header: "Durum",
            cell: ({ row }) => (
                <Badge variant={row.original.is_active ? "default" : "secondary"}>
                    {row.original.is_active ? "Aktif" : "Pasif"}
                </Badge>
            ),
        },
        {
            id: "actions",
            cell: ({ row }) => (
                <div className="flex justify-end gap-2">
                    <Button variant="ghost" size="icon" onClick={() => handleEdit(row.original)}>
                        <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={() => setDeleteId(row.original.id)}
                    >
                        <Trash2 className="h-4 w-4" />
                    </Button>
                </div>
            ),
        },
    ];

    return (
        <AppShell
            breadcrumbs={[
                { label: "Blog", href: "/blog" },
                { label: "Kategoriler" },
            ]}
        >
            <PageHeader
                title="Blog Kategorileri"
                description="Blog yazılarını gruplamak için kategorileri yönetin."
                actions={
                    <Button onClick={handleCreate}>
                        <Plus className="mr-2 h-4 w-4" />
                        Yeni Kategori
                    </Button>
                }
            />

            <DataTable
                columns={columns}
                data={data?.results || []}
                loading={isLoading}
                emptyMessage="Kategori bulunamadı."
            />

            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>{editingCategory ? "Kategoriyi Düzenle" : "Yeni Kategori"}</DialogTitle>
                        <DialogDescription>
                            Blog kategorisi detaylarını aşağıdan düzenleyebilirsiniz.
                        </DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Kategori Adı</Label>
                            <Input
                                id="name"
                                value={formData.name_tr}
                                onChange={(e) => setFormData({ ...formData, name_tr: e.target.value })}
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="description">Açıklama</Label>
                            <Textarea
                                id="description"
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                rows={3}
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="order">Sıralama</Label>
                                <Input
                                    id="order"
                                    type="number"
                                    value={formData.order}
                                    onChange={(e) => setFormData({ ...formData, order: parseInt(e.target.value) || 0 })}
                                />
                            </div>
                            <div className="flex items-center justify-between space-y-0 pt-8">
                                <Label htmlFor="active" className="cursor-pointer">Aktif mi?</Label>
                                <Switch
                                    id="active"
                                    checked={formData.is_active}
                                    onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                                İptal
                            </Button>
                            <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
                                {createMutation.isPending || updateMutation.isPending ? "Kaydediliyor..." : "Kaydet"}
                            </Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Dialog>

            <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Emin misiniz?</AlertDialogTitle>
                        <AlertDialogDescription>
                            Bu kategoriyi silmek istediğinize emin misiniz? Bu kategoriye bağlı yazılar kategorisiz kalacaktır.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>İptal</AlertDialogCancel>
                        <AlertDialogAction onClick={handleDelete} className="bg-destructive hover:bg-destructive/90">
                            Sil
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </AppShell>
    );
}
