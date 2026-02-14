import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminBlogApi, BlogPost, BlogCategory, BlogSearchParams, BlogTag } from "@/lib/api/blog";
import { useToast } from "./use-toast";

// Blog Posts
export function useBlogPosts(params?: BlogSearchParams) {
    return useQuery({
        queryKey: ["blog-posts", params],
        queryFn: () => adminBlogApi.getPosts(params),
    });
}

export function useBlogPost(id: string) {
    return useQuery({
        queryKey: ["blog-post", id],
        queryFn: () => adminBlogApi.getPost(id),
        enabled: !!id,
    });
}

export function useCreateBlogPost() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: (data: Partial<BlogPost>) => adminBlogApi.createPost(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["blog-posts"] });
            toast({
                title: "Başarılı",
                description: "Blog yazısı oluşturuldu.",
            });
        },
        onError: () => {
            toast({
                title: "Hata",
                description: "Blog yazısı oluşturulamadı.",
                variant: "destructive",
            });
        },
    });
}

export function useUpdateBlogPost() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<BlogPost> }) =>
            adminBlogApi.updatePost(id, data),
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ["blog-posts"] });
            queryClient.invalidateQueries({ queryKey: ["blog-post", data.id] });
            toast({
                title: "Başarılı",
                description: "Blog yazısı güncellendi.",
            });
        },
        onError: () => {
            toast({
                title: "Hata",
                description: "Blog yazısı güncellenemedi.",
                variant: "destructive",
            });
        },
    });
}

export function useDeleteBlogPost() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: (id: string) => adminBlogApi.deletePost(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["blog-posts"] });
            toast({
                title: "Başarılı",
                description: "Blog yazısı silindi.",
            });
        },
        onError: () => {
            toast({
                title: "Hata",
                description: "Blog yazısı silinemedi.",
                variant: "destructive",
            });
        },
    });
}

// Blog Categories
export function useBlogCategories() {
    return useQuery({
        queryKey: ["blog-categories"],
        queryFn: adminBlogApi.getCategories,
    });
}

export function useCreateBlogCategory() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: (data: Partial<BlogCategory>) => adminBlogApi.createCategory(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["blog-categories"] });
            toast({
                title: "Başarılı",
                description: "Kategori oluşturuldu.",
            });
        },
        onError: () => {
            toast({
                title: "Hata",
                description: "Kategori oluşturulamadı.",
                variant: "destructive",
            });
        },
    });
}

export function useUpdateBlogCategory() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<BlogCategory> }) =>
            adminBlogApi.updateCategory(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["blog-categories"] });
            toast({
                title: "Başarılı",
                description: "Kategori güncellendi.",
            });
        },
        onError: () => {
            toast({
                title: "Hata",
                description: "Kategori güncellenemedi.",
                variant: "destructive",
            });
        },
    });
}

export function useDeleteBlogCategory() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: (id: string) => adminBlogApi.deleteCategory(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["blog-categories"] });
            toast({
                title: "Başarılı",
                description: "Kategori silindi.",
            });
        },
        onError: () => {
            toast({
                title: "Hata",
                description: "Kategori silinemedi.",
                variant: "destructive",
            });
        },
    });
}

// Blog Tags
export function useBlogTags() {
    return useQuery({
        queryKey: ["blog-tags"],
        queryFn: adminBlogApi.getTags,
    });
}

export function useCreateBlogTag() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: (data: Partial<BlogTag>) => adminBlogApi.createTag(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["blog-tags"] });
            toast({
                title: "Başarılı",
                description: "Etiket oluşturuldu.",
            });
        },
        onError: () => {
            toast({
                title: "Hata",
                description: "Etiket oluşturulamadı.",
                variant: "destructive",
            });
        },
    });
}

export function useDeleteBlogTag() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: (id: string) => adminBlogApi.deleteTag(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["blog-tags"] });
            toast({
                title: "Başarılı",
                description: "Etiket silindi.",
            });
        },
        onError: () => {
            toast({
                title: "Hata",
                description: "Etiket silinemedi.",
                variant: "destructive",
            });
        },
    });
}
