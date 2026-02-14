"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { inquiriesApi, type InquiriesParams } from "@/lib/api/inquiries";
import type {
  InquiryListItem,
  InquiryDetail,
  InquiryStatus,
  PaginatedResponse,
  QuoteComposeRequest,
  QuoteComposeResponse,
} from "@/types/api";

export const inquiryKeys = {
  all: ["inquiries"] as const,
  lists: () => [...inquiryKeys.all, "list"] as const,
  list: (params: InquiriesParams) => [...inquiryKeys.lists(), params] as const,
  details: () => [...inquiryKeys.all, "detail"] as const,
  detail: (id: string) => [...inquiryKeys.details(), id] as const,
};

export function useInquiries(params: InquiriesParams = {}) {
  return useQuery<PaginatedResponse<InquiryListItem>>({
    queryKey: inquiryKeys.list(params),
    queryFn: () => inquiriesApi.list(params),
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useInquiry(id: string) {
  return useQuery<InquiryDetail>({
    queryKey: inquiryKeys.detail(id),
    queryFn: () => inquiriesApi.get(id),
    enabled: !!id,
    staleTime: 30 * 1000,
  });
}

export function useUpdateInquiryStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: InquiryStatus }) =>
      inquiriesApi.updateStatus(id, status),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(inquiryKeys.detail(id), data);
      queryClient.invalidateQueries({ queryKey: inquiryKeys.lists() });
    },
  });
}

export function useUpdateInquiryNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, internal_note }: { id: string; internal_note: string }) =>
      inquiriesApi.updateNote(id, internal_note),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(inquiryKeys.detail(id), data);
    },
  });
}

export function useComposeQuote() {
  return useMutation<QuoteComposeResponse, Error, QuoteComposeRequest>({
    mutationFn: (data) => inquiriesApi.composeQuote(data),
  });
}
