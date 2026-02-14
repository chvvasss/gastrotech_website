"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { type ColumnDef } from "@tanstack/react-table";
import { Plus, Search, Calendar, User, Eye, Edit, Trash2 } from "lucide-react";
import Link from "next/link";
import { AppShell, PageHeader } from "@/components/layout";
import { DataTable, Pagination } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
import { useBlogPosts, useDeleteBlogPost, useBlogCategories } from "@/hooks/use-blog";
import { useDebounce } from "@/hooks/use-debounce";
import type { BlogPost } from "@/lib/api/blog";

const STATUS_Map: Record<string, { label: string; variant: "default" | "secondary" | "outline" | "destructive" }> = {
    published: { label: "Yayında", variant: "default" },
    draft: { label: "Taslak", variant: "secondary" },
    archived: { label: "Arşiv", variant: "outline" },
};

export default function BlogListPage() {
    const router = useRouter();
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");
    const [status, setStatus] = useState<string>("all");
    const [category, setCategory] = useState<string>("all");
    const [deleteId, setDeleteId] = useState<string | null>(null);

    const debouncedSearch = useDebounce(search, 300);
    const deleteMutation = useDeleteBlogPost();

    const { data: postsData, isLoading } = useBlogPosts({
        page,
        search: debouncedSearch,
        status: status === "all" ? undefined : status,
        category: category === "all" ? undefined : category,
    });

    const { data: categoriesData } = useBlogCategories();

    const handleDelete = async () => {
        if (deleteId) {
            await deleteMutation.mutateAsync(deleteId);
            setDeleteId(null);
        }
    };

    const columns: ColumnDef<BlogPost>[] = [
        {
            accessorKey: "title",
            header: "Başlık",
            cell: ({ row }) => (
                <div className="flex items-center gap-3">
                    {row.original.cover_url ? (
                        <div className="h-10 w-16 flex-shrink-0 overflow-hidden rounded bg-muted">
                            <img
                                src={row.original.cover_url}
                                alt=""
                                className="h-full w-full object-cover"
                            />
                        </div>
                    ) : (
                        <div className="h-10 w-16 flex-shrink-0 rounded bg-muted" />
                    )}
                    <div>
                        <div className="font-medium text-stone-900">{row.original.title}</div>
                        <div className="text-xs text-stone-500 line-clamp-1">{row.original.excerpt}</div>
                    </div>
                </div>
            ),
        },
        {
            accessorKey: "category_detail",
            header: "Kategori",
            cell: ({ row }) => (
                <Badge variant="outline" className="font-normal">
                    {row.original.category_detail?.name_tr || "Kategorisiz"}
                </Badge>
            ),
        },
        {
            accessorKey: "status",
            header: "Durum",
            cell: ({ row }) => {
                const config = STATUS_Map[row.original.status];
                return <Badge variant={config?.variant || "outline"}>{config?.label || row.original.status}</Badge>;
            },
        },
        {
            accessorKey: "author",
            header: "Yazar",
            cell: ({ row }) => (
                <div className="flex items-center gap-2 text-sm text-stone-600">
                    <User className="h-3 w-3" />
                    <span>{row.original.author_name || "-"}</span>
                </div>
            ),
        },
        {
            accessorKey: "stats",
            header: "İstatistik",
            cell: ({ row }) => (
                <div className="flex flex-col gap-1 text-xs text-stone-500">
                    <div className="flex items-center gap-1">
                        <Eye className="h-3 w-3" />
                        <span>{row.original.view_count}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>{row.original.published_at ? new Date(row.original.published_at).toLocaleDateString("tr-TR") : "-"}</span>
                    </div>
                </div>
            ),
        },
        {
            id: "actions",
            cell: ({ row }) => (
                <div className="flex items-center justify-end gap-2">
                    <Button variant="ghost" size="icon" asChild>
                        <Link href={`/blog/${row.original.id}`}>
                            <Edit className="h-4 w-4" />
                        </Link>
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
                { label: "Yazılar" },
            ]}
        >
            <PageHeader
                title="Blog Yazıları"
                description="Blog yazılarını yönetin, düzenleyin ve yayınlayın."
                actions={
                    <div className="flex gap-2">
                        <Button asChild variant="outline">
                            <Link href="/blog/categories">Kategoriler</Link>
                        </Button>
                        <Button asChild>
                            <Link href="/blog/new">
                                <Plus className="mr-2 h-4 w-4" />
                                Yeni Yazı
                            </Link>
                        </Button>
                    </div>
                }
            />

            <div className="mb-6 flex flex-col gap-4 sm:flex-row">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                        placeholder="Başlık veya içerik ara..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="pl-10"
                    />
                </div>
                <Select value={status} onValueChange={setStatus}>
                    <SelectTrigger className="w-[150px]">
                        <SelectValue placeholder="Durum" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">Tüm Durumlar</SelectItem>
                        <SelectItem value="published">Yayında</SelectItem>
                        <SelectItem value="draft">Taslak</SelectItem>
                        <SelectItem value="archived">Arşiv</SelectItem>
                    </SelectContent>
                </Select>
                <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger className="w-[200px]">
                        <SelectValue placeholder="Kategori" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">Tüm Kategoriler</SelectItem>
                        {categoriesData?.results?.map((cat) => (
                            <SelectItem key={cat.id} value={cat.slug}>
                                {cat.name_tr}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>

            <DataTable
                columns={columns}
                data={postsData?.results || []}
                loading={isLoading}
                emptyMessage="Blog yazısı bulunamadı."
            />

            {postsData && (
                <div className="mt-4">
                    <Pagination
                        page={page}
                        pageSize={20}
                        totalItems={postsData.count}
                        totalPages={Math.ceil(postsData.count / 20)}
                        onPageChange={setPage}
                    />
                </div>
            )}

            <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Emin misiniz?</AlertDialogTitle>
                        <AlertDialogDescription>
                            Bu blog yazısını silmek istediğinize emin misiniz? Bu işlem geri alınamaz.
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
