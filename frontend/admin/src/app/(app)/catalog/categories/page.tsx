"use client";

import { useState } from "react";
import {
    Plus,
    Edit2,
    Trash2,
    ChevronRight,
    ChevronDown,
    Folder,
    FolderOpen,
    Loader2,
    MoreHorizontal,
    Image as ImageIcon,
    Star,
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
    useCreateCategory,
    useUpdateCategory,
    useDeleteCategory,
} from "@/hooks/use-admin-taxonomy";
import type { AdminCategory, CreateCategoryPayload, UpdateCategoryPayload } from "@/lib/api/admin-taxonomy";

// Build tree structure from flat list with cycle protection
function buildCategoryTree(categories: AdminCategory[]): (AdminCategory & { children: AdminCategory[] })[] {
    if (!categories || !Array.isArray(categories)) {
        return [];
    }

    const map = new Map<string | null, AdminCategory[]>();

    // Group by parent
    categories.forEach(cat => {
        const parentId = cat.parent;
        if (!map.has(parentId)) {
            map.set(parentId, []);
        }
        map.get(parentId)!.push(cat);
    });

    // Recursive build with visited set to prevent infinite loops
    const buildTree = (parentId: string | null, visited: Set<string> = new Set()): (AdminCategory & { children: AdminCategory[] })[] => {
        const children = map.get(parentId) || [];
        return children
            .filter(cat => !visited.has(cat.id)) // Skip if already visited (cycle detected)
            .map(cat => {
                const newVisited = new Set(visited);
                newVisited.add(cat.id);
                return {
                    ...cat,
                    children: buildTree(cat.id, newVisited),
                };
            });
    };

    return buildTree(null);
}

const getMediaUrl = (id?: string | null) => {
    if (!id) return undefined;
    return `${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/v1/media/${id}/file/`;
};

interface CategoryNodeProps {
    category: AdminCategory & { children: AdminCategory[] };
    level: number;
    onEdit: (cat: AdminCategory) => void;
    onDelete: (cat: AdminCategory) => void;
    onAddChild: (parentSlug: string) => void;
}

function CategoryNode({ category, level, onEdit, onDelete, onAddChild }: CategoryNodeProps) {
    const [isOpen, setIsOpen] = useState(level < 1);
    const hasChildren = category.children.length > 0;

    return (
        <div>
            <div
                className="flex items-center gap-2 py-2 px-3 rounded-lg hover:bg-stone-50 group transition-colors"
                style={{ paddingLeft: `${level * 24 + 12}px` }}
            >
                {/* Expand/Collapse */}
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className={`p-1 rounded hover:bg-stone-200 transition-colors ${!hasChildren && "invisible"}`}
                >
                    {isOpen ? (
                        <ChevronDown className="h-4 w-4 text-stone-500" />
                    ) : (
                        <ChevronRight className="h-4 w-4 text-stone-500" />
                    )}
                </button>

                {/* Icon */}
                {isOpen && hasChildren ? (
                    <FolderOpen className="h-5 w-5 text-amber-500" />
                ) : (
                    <Folder className="h-5 w-5 text-stone-400" />
                )}

                {/* Cover Preview (if exists) */}
                {category.cover_media && (
                    <div className="h-6 w-6 rounded overflow-hidden flex-shrink-0 border border-stone-200">
                        <img
                            src={getMediaUrl(category.cover_media)}
                            alt={category.name}
                            className="h-full w-full object-cover"
                        />
                    </div>
                )}

                {/* Name */}
                <span className="flex-1 font-medium text-stone-900">
                    {category.name}
                </span>

                {/* Featured Badge */}
                {category.is_featured && (
                    <Badge variant="secondary" className="text-xs">
                        <Star className="h-3 w-3 mr-1 fill-amber-400 text-amber-400" />
                        Öne Çıkan
                    </Badge>
                )}

                {/* Order */}
                <span className="text-xs text-stone-400">#{category.order}</span>

                {/* Actions */}
                <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreHorizontal className="h-4 w-4" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => onEdit(category)}>
                                <Edit2 className="h-4 w-4 mr-2" />
                                Düzenle
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => onAddChild(category.slug)}>
                                <Plus className="h-4 w-4 mr-2" />
                                Alt Kategori Ekle
                            </DropdownMenuItem>
                            <DropdownMenuItem
                                onClick={() => onDelete(category)}
                                className="text-red-600 focus:text-red-600"
                            >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Sil
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </div>

            {/* Children */}
            {isOpen && hasChildren && (
                <div>
                    {category.children.map(child => (
                        <CategoryNode
                            key={child.id}
                            category={child as AdminCategory & { children: AdminCategory[] }}
                            level={level + 1}
                            onEdit={onEdit}
                            onDelete={onDelete}
                            onAddChild={onAddChild}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

export default function CategoriesPage() {
    const { toast } = useToast();
    const [formOpen, setFormOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [editingCategory, setEditingCategory] = useState<AdminCategory | null>(null);
    const [deletingCategory, setDeletingCategory] = useState<AdminCategory | null>(null);
    const [parentSlugForNew, setParentSlugForNew] = useState<string | null>(null);

    // Form state
    const [formData, setFormData] = useState<CreateCategoryPayload>({
        name: "",
        slug: "",
        menu_label: "",
        description_short: "",
        order: 0,
        is_featured: false,
        cover_media: null,
    });

    const { data: categories, isLoading } = useCategories();
    const createMutation = useCreateCategory();
    const updateMutation = useUpdateCategory();
    const deleteMutation = useDeleteCategory();

    const categoryTree = categories ? buildCategoryTree(categories) : [];

    const handleOpenCreate = (parentSlug?: string) => {
        setEditingCategory(null);
        setParentSlugForNew(parentSlug || null);
        setFormData({
            name: "",
            slug: "",
            menu_label: "",
            description_short: "",
            order: 0,
            is_featured: false,
            cover_media: null,
            parent_slug: parentSlug || null,
        });
        setFormOpen(true);
    };

    const handleOpenEdit = (category: AdminCategory) => {
        setEditingCategory(category);
        setParentSlugForNew(null);
        setFormData({
            name: category.name,
            slug: category.slug,
            menu_label: category.menu_label || "",
            description_short: category.description_short || "",
            order: category.order,
            is_featured: category.is_featured,
            cover_media: category.cover_media,
            parent_slug: category.parent_slug,
        });
        setFormOpen(true);
    };

    const handleOpenDelete = (category: AdminCategory) => {
        setDeletingCategory(category);
        setDeleteDialogOpen(true);
    };

    const handleSubmit = async () => {
        try {
            if (editingCategory) {
                await updateMutation.mutateAsync({
                    slug: editingCategory.slug,
                    payload: formData as UpdateCategoryPayload,
                });
                toast({ title: "Kategori güncellendi" });
            } else {
                await createMutation.mutateAsync(formData);
                toast({ title: "Kategori oluşturuldu" });
            }
            setFormOpen(false);
        } catch (error: any) {
            console.error(error);
            const errorMessage = error?.response?.data?.error ||
                JSON.stringify(error?.response?.data) ||
                "İşlem başarısız oldu";
            toast({
                title: "Hata",
                description: errorMessage,
                variant: "destructive",
            });
        }
    };

    const handleDelete = async () => {
        if (!deletingCategory) return;
        try {
            await deleteMutation.mutateAsync(deletingCategory.slug);
            toast({ title: "Kategori silindi" });
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

    // Find all categories for parent select
    const allCategoriesFlat = categories || [];

    return (
        <AppShell
            breadcrumbs={[
                { label: "Katalog", href: "/catalog/products" },
                { label: "Kategoriler" },
            ]}
        >
            <PageHeader
                title="Kategori Yönetimi"
                description="Ürün kategorilerini hiyerarşik olarak yönetin"
                actions={
                    <Button onClick={() => handleOpenCreate()}>
                        <Plus className="h-4 w-4 mr-2" />
                        Yeni Kategori
                    </Button>
                }
            />

            <Card className="border-stone-200 bg-white">
                <CardHeader className="pb-3">
                    <CardTitle className="text-lg text-stone-900">Kategoriler</CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="space-y-2">
                            {[...Array(6)].map((_, i) => (
                                <Skeleton key={i} className="h-10 w-full" />
                            ))}
                        </div>
                    ) : categoryTree.length === 0 ? (
                        <div className="text-center py-12 text-stone-500">
                            <Folder className="h-12 w-12 mx-auto mb-4 opacity-20" />
                            <p>Henüz kategori eklenmemiş</p>
                            <Button
                                variant="outline"
                                className="mt-4"
                                onClick={() => handleOpenCreate()}
                            >
                                <Plus className="h-4 w-4 mr-2" />
                                İlk Kategoriyi Ekle
                            </Button>
                        </div>
                    ) : (
                        <div className="space-y-1">
                            {categoryTree.map(cat => (
                                <CategoryNode
                                    key={cat.id}
                                    category={cat}
                                    level={0}
                                    onEdit={handleOpenEdit}
                                    onDelete={handleOpenDelete}
                                    onAddChild={handleOpenCreate}
                                />
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
                            {editingCategory ? "Kategori Düzenle" : "Yeni Kategori"}
                        </DialogTitle>
                        <DialogDescription>
                            {editingCategory
                                ? "Kategori bilgilerini güncelleyin"
                                : parentSlugForNew
                                    ? "Alt kategori oluşturun"
                                    : "Yeni bir ana kategori oluşturun"}
                        </DialogDescription>
                    </DialogHeader>

                    <div className="flex-1 overflow-y-auto px-6 py-2">
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="name">Kategori Adı *</Label>
                                    <Input
                                        id="name"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        placeholder="örn: Pişirme Üniteleri"
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

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="menu_label">Menü Etiketi</Label>
                                    <Input
                                        id="menu_label"
                                        value={formData.menu_label}
                                        onChange={(e) => setFormData({ ...formData, menu_label: e.target.value })}
                                        placeholder="Navigasyonda görünecek kısa isim"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="parent">Üst Kategori</Label>
                                    <Select
                                        value={formData.parent_slug || "__none__"}
                                        onValueChange={(v) => setFormData({ ...formData, parent_slug: v === "__none__" ? null : v })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Ana kategori (yok)" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="__none__">Ana Kategori (Yok)</SelectItem>
                                            {allCategoriesFlat
                                                .filter(c => c.slug !== editingCategory?.slug)
                                                .map(c => (
                                                    <SelectItem key={c.id} value={c.slug}>
                                                        {c.name}
                                                    </SelectItem>
                                                ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="description_short">Kısa Açıklama</Label>
                                <Textarea
                                    id="description_short"
                                    value={formData.description_short}
                                    onChange={(e) => setFormData({ ...formData, description_short: e.target.value })}
                                    placeholder="Kategori açıklaması"
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
                        <Button onClick={handleSubmit} disabled={isPending || !formData.name}>
                            {isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                            {editingCategory ? "Güncelle" : "Oluştur"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation */}
            <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Kategoriyi Sil</AlertDialogTitle>
                        <AlertDialogDescription>
                            <strong>{deletingCategory?.name}</strong> kategorisini silmek istediğinizden emin misiniz?
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
