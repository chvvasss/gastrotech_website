import { http } from "./http";

export interface BlogCategory {
    id: string;
    name_tr: string;
    name_en?: string;
    slug: string;
    description?: string;
    order: number;
    is_active: boolean;
    posts_count?: number;
    created_at: string;
    updated_at: string;
}

export interface BlogTag {
    id: string;
    name: string;
    slug: string;
    created_at: string;
}

export interface BlogPost {
    id: string;
    title: string;
    slug: string;
    excerpt: string;
    content: string;
    cover_url?: string;
    cover_media_id?: string | null;
    category?: BlogCategory;
    category_detail?: BlogCategory;
    category_id?: string | null;
    tags: BlogTag[];
    tag_ids?: string[];
    author_name?: string;
    status: "draft" | "published" | "archived";
    published_at?: string;
    is_featured: boolean;
    view_count: number;
    reading_time_min: number;
    meta_title?: string;
    meta_description?: string;
    created_at: string;
    updated_at: string;
    cover?: {
        id: string;
        file_url: string;
    };
}

export interface BlogSearchParams {
    page?: number;
    search?: string;
    status?: string;
    category?: string;
}

export const adminBlogApi = {
    // Blog Posts
    getPosts: async (params?: BlogSearchParams) => {
        const response = await http.get<{ count: number; next: string | null; previous: string | null; results: BlogPost[] }>(
            "/admin/blog/",
            { params }
        );
        return response.data;
    },

    getPost: async (id: string) => {
        const response = await http.get<BlogPost>(`/admin/blog/${id}/`);
        return response.data;
    },

    createPost: async (data: Partial<BlogPost>) => {
        const response = await http.post<BlogPost>("/admin/blog/create/", data);
        return response.data;
    },

    updatePost: async (id: string, data: Partial<BlogPost>) => {
        const response = await http.put<BlogPost>(`/admin/blog/${id}/`, data);
        return response.data;
    },

    deletePost: async (id: string) => {
        const response = await http.delete(`/admin/blog/${id}/`);
        return response.data;
    },

    // Categories
    getCategories: async () => {
        const response = await http.get<{ count: number; results: BlogCategory[] }>("/admin/blog/categories/");
        return response.data;
    },

    createCategory: async (data: Partial<BlogCategory>) => {
        const response = await http.post<BlogCategory>("/admin/blog/categories/", data);
        return response.data;
    },

    updateCategory: async (id: string, data: Partial<BlogCategory>) => {
        const response = await http.put<BlogCategory>(`/admin/blog/categories/${id}/`, data);
        return response.data;
    },

    deleteCategory: async (id: string) => {
        const response = await http.delete(`/admin/blog/categories/${id}/`);
        return response.data;
    },

    // Tags
    getTags: async () => {
        const response = await http.get<{ count: number; results: BlogTag[] }>("/admin/blog/tags/");
        return response.data;
    },

    createTag: async (data: Partial<BlogTag>) => {
        const response = await http.post<BlogTag>("/admin/blog/tags/", data);
        return response.data;
    },

    deleteTag: async (id: string) => {
        const response = await http.delete(`/admin/blog/tags/${id}/`);
        return response.data;
    },
};
