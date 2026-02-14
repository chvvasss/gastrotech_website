import { http } from "./http";
import { MediaUploadResponse } from "@/types/api";

export const mediaApi = {
    upload: async (file: File) => {
        const formData = new FormData();
        formData.append("file", file);
        return http.post<MediaUploadResponse>("/admin/media/upload/", formData, {
            headers: {
                "Content-Type": "multipart/form-data",
            },
        });
    },
};
