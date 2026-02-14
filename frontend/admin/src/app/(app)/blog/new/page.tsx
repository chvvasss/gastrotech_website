"use client";

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
import { useCreateBlogPost, useBlogCategories, useBlogTags } from "@/hooks/use-blog";
import { useToast } from "@/hooks/use-toast";
import { useState } from "react";
import { ImageUpload } from "@/components/ui/image-upload";

export default function NewBlogPostPage() {
    const router = useRouter();
    const { toast } = useToast();
    const createMutation = useCreateBlogPost();
    const { data: categories } = useBlogCategories();
    const { data: tags } = useBlogTags();

    const [formData, setFormData] = useState({
        title: "",
        excerpt: "",
        content: "",
        category_id: "",
        status: "draft" as "draft" | "published" | "archived",
        cover_media_id: null as string | null,
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        try {
            await createMutation.mutateAsync({
                ...formData,
                category_id: formData.category_id || null,
                cover_media_id: formData.cover_media_id || null,
            });
            toast({
                title: "Başarılı",
                description: "Blog yazısı oluşturuldu.",
            });
            router.push("/blog");
        } catch (error) {
            // Error handling is done in the hook
        }
    };

    return (
        <AppShell
            breadcrumbs={[
                { label: "Blog", href: "/blog" },
                { label: "Yeni Yazı" },
            ]}
        >
            <PageHeader
                title="Yeni Blog Yazısı"
                description="Yeni bir blog içeriği oluşturun."
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
                    <Button type="submit" disabled={createMutation.isPending}>
                        {createMutation.isPending ? "Oluşturuluyor..." : "Oluştur"}
                    </Button>
                </div>
            </form>
        </AppShell>
    );
}
