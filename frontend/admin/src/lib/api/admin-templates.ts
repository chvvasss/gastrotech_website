
import { http } from "./http";
import { SpecTemplate, PaginatedResponse } from "@/types/api";

export const adminTemplatesApi = {
    list: (params?: { page?: number; search?: string; series?: string }) =>
        http.get<PaginatedResponse<SpecTemplate>>("/admin/spec-templates/", { params }),

    get: (id: string) =>
        http.get<SpecTemplate>(`/admin/spec-templates/${id}/`),

    create: (data: Partial<SpecTemplate>) =>
        http.post<SpecTemplate>("/admin/spec-templates/", data),

    update: (id: string, data: Partial<SpecTemplate>) =>
        http.patch<SpecTemplate>(`/admin/spec-templates/${id}/`, data),

    delete: (id: string) =>
        http.delete(`/admin/spec-templates/${id}/`),

    apply: (productId: string, templateId: string, overwrite: boolean) =>
        http.post(`/admin/products/${productId}/apply-template/`, {
            template_id: templateId,
            overwrite
        }),
};
