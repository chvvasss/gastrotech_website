"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PageHeader, AppShell } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { useBlogPost, useUpdateBlogPost, useBlogCategories } from "@/hooks/use-blog";
import { useToast } from "@/hooks/use-toast";
import { use } from "react";
import { ImageUpload } from "@/components/ui/image-upload";

export default function EditBlogPostPage({ params }: { params: Promise<{ id: string }> }) {
    const resolvedParams = use(params);
    const router = useRouter();
    const { toast } = useToast();
    const { data: post, isLoading } = useBlogPost(resolvedParams.id);
    const updateMutation = useUpdateBlogPost();
    const { data: categories } = useBlogCategories();

    const [formData, setFormData] = useState({
        title: "",
        excerpt: "",
        content: "",
        category_id: "",
        status: "draft" as "draft" | "published" | "archived",
        cover_media_id: null as string | null,
    });

    useEffect(() => {
        if (post) {
            setFormData({
                title: post.title,
                excerpt: post.excerpt,
                content: post.content,
                category_id: post.category?.id || "",
                status: post.status,
                cover_media_id: post.cover?.id || null,
            });
        }
    }, [post]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        try {
            await updateMutation.mutateAsync({
                id: resolvedParams.id,
                data: {
                    ...formData,
                    category_id: formData.category_id || null,
                    cover_media_id: formData.cover_media_id || null,
                },
            });
            // Success toast is handled in the hook
            router.push("/blog");
        } catch (error) {
            // Error toast is handled in the hook
        }
    };

    if (isLoading) {
        return <div>Yükleniyor...</div>;
    }

    return (
        <AppShell
            breadcrumbs={[
                { label: "Blog", href: "/blog" },
                { label: "Yazıyı Düzenle" },
            ]}
        >
            <PageHeader
                title="Blog Yazısını Düzenle"
                description="Mevcut blog içeriğini güncelleyin."
            />

            <form onSubmit={handleSubmit} className="max-w-4xl space-y-8">
                <div className="space-y-4 rounded-lg border bg-card p-6">
                    <div className="grid gap-4 sm:grid-cols-2">
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="title">Başlık</Label>
                                <Input
                                    id="title"
                                    value={formData.title}
                                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                    placeholder="Blog yazısı başlığı"
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="category">Kategori</Label>
                                <Select
                                    value={formData.category_id}
                                    onValueChange={(value) => setFormData({ ...formData, category_id: value })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Kategori seçin" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {categories?.results.map((cat) => (
                                            <SelectItem key={cat.id} value={cat.id}>
                                                {cat.name_tr}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>Kapak Görseli</Label>
                            <ImageUpload
                                value={formData.cover_media_id || undefined}
                                onChange={(value) => setFormData({ ...formData, cover_media_id: value })}
                                currentImageUrl={post?.cover?.file_url}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="excerpt">Özet</Label>
                        <Textarea
                            id="excerpt"
                            value={formData.excerpt}
                            onChange={(e) => setFormData({ ...formData, excerpt: e.target.value })}
                            placeholder="Yazının kısa özeti (SEO için önemli)"
                            rows={3}
                            required
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="content">İçerik</Label>
                        <Textarea
                            id="content"
                            value={formData.content}
                            onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                            placeholder="Blog içeriği (HTML/Markdown)"
                            rows={15}
                            required
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="status">Durum</Label>
                        <Select
                            value={formData.status}
                            onValueChange={(value: any) => setFormData({ ...formData, status: value })}
                        >
                            <SelectTrigger className="w-[200px]">
                                <SelectValue placeholder="Durum seçin" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="draft">Taslak</SelectItem>
                                <SelectItem value="published">Yayında</SelectItem>
                                <SelectItem value="archived">Arşiv</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                <div className="flex gap-4">
                    <Button type="button" variant="outline" onClick={() => router.back()}>
                        İptal
                    </Button>
                    <Button type="submit" disabled={updateMutation.isPending}>
                        {updateMutation.isPending ? "Güncelleniyor..." : "Güncelle"}
                    </Button>
                </div>
            </form>
        </AppShell>
    );
}
