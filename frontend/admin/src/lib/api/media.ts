import { http } from "./http";
import { MediaUploadResponse } from "@/types/api";

export const mediaApi = {
    upload: async (file: File) => {
        const formData = new FormData();
        formData.append("file", file);
        // Do NOT set Content-Type explicitly for FormData.
        // The browser must set it automatically with the correct boundary.
        // Explicitly overriding prevents the boundary from being added.
        return http.post<MediaUploadResponse>("/admin/media/upload/", formData, {
            headers: {
                "Content-Type": undefined as unknown as string,
            },
        });
    },
};
