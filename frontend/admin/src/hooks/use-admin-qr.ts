"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { infoSheetsApi, InfoSheet } from "@/lib/api/admin-qr";

export const infoSheetKeys = {
    all: ["info-sheets"] as const,
    list: () => [...infoSheetKeys.all, "list"] as const,
    detail: (id: string) => [...infoSheetKeys.all, "detail", id] as const,
};

export function useInfoSheets() {
    return useQuery({
        queryKey: infoSheetKeys.list(),
        queryFn: () => infoSheetsApi.list(),
    });
}

export function useInfoSheet(id: string) {
    return useQuery({
        queryKey: infoSheetKeys.detail(id),
        queryFn: () => infoSheetsApi.get(id),
        enabled: !!id,
    });
}

export function useCreateInfoSheet() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ title, pdfFile }: { title: string; pdfFile: File }) =>
            infoSheetsApi.create(title, pdfFile),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: infoSheetKeys.all });
        },
    });
}

export function useUpdateInfoSheet() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, data }: { id: string; data: { title?: string; pdf_file?: File } }) =>
            infoSheetsApi.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: infoSheetKeys.all });
        },
    });
}

export function useDeleteInfoSheet() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => infoSheetsApi.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: infoSheetKeys.all });
        },
    });
}

export function useRegenerateQr() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => infoSheetsApi.regenerateQr(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: infoSheetKeys.all });
        },
    });
}
