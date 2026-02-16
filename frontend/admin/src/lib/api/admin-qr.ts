import { http } from "./http";

// =============================================================================
// Admin Info Sheets (QR Code Generator) API
// =============================================================================

export interface InfoSheet {
    id: string;
    title: string;
    pdf_file: string;
    pdf_url: string | null;
    qr_code: string | null;
    qr_url: string | null;
    created_at: string;
    updated_at: string;
}

export const infoSheetsApi = {
    /**
     * List all info sheets
     */
    async list(): Promise<InfoSheet[]> {
        const response = await http.get<InfoSheet[] | { results: InfoSheet[] }>("/admin/info-sheets/");
        const data = response.data;
        return Array.isArray(data) ? data : (data.results || []);
    },

    /**
     * Get single info sheet
     */
    async get(id: string): Promise<InfoSheet> {
        const response = await http.get<InfoSheet>(`/admin/info-sheets/${id}/`);
        return response.data;
    },

    /**
     * Create new info sheet (upload PDF)
     */
    async create(title: string, pdfFile: File): Promise<InfoSheet> {
        const formData = new FormData();
        formData.append("title", title);
        formData.append("pdf_file", pdfFile);
        const response = await http.post<InfoSheet>("/admin/info-sheets/", formData, {
            headers: {
                "Content-Type": "multipart/form-data",
            },
        });
        return response.data;
    },

    /**
     * Update info sheet
     */
    async update(id: string, data: { title?: string; pdf_file?: File }): Promise<InfoSheet> {
        const formData = new FormData();
        if (data.title) formData.append("title", data.title);
        if (data.pdf_file) formData.append("pdf_file", data.pdf_file);
        const response = await http.patch<InfoSheet>(`/admin/info-sheets/${id}/`, formData, {
            headers: {
                "Content-Type": "multipart/form-data",
            },
        });
        return response.data;
    },

    /**
     * Delete info sheet
     */
    async delete(id: string): Promise<void> {
        await http.delete(`/admin/info-sheets/${id}/`);
    },

    /**
     * Regenerate QR code
     */
    async regenerateQr(id: string): Promise<InfoSheet> {
        const response = await http.post<InfoSheet>(`/admin/info-sheets/${id}/regenerate-qr/`);
        return response.data;
    },
};
