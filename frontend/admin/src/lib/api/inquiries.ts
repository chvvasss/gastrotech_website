import { http } from "./http";
import type {
  InquiryListItem,
  InquiryDetail,
  InquiryStatus,
  PaginatedResponse,
  QuoteComposeRequest,
  QuoteComposeResponse,
} from "@/types/api";

export interface InquiriesParams {
  page?: number;
  page_size?: number;
  status?: InquiryStatus | "";
  search?: string;
  ordering?: string;
}

export const inquiriesApi = {
  async list(
    params: InquiriesParams = {}
  ): Promise<PaginatedResponse<InquiryListItem>> {
    const queryParams = new URLSearchParams();

    if (params.page) queryParams.set("page", params.page.toString());
    if (params.page_size)
      queryParams.set("page_size", params.page_size.toString());
    if (params.status) queryParams.set("status", params.status);
    if (params.search) queryParams.set("search", params.search);
    if (params.ordering) queryParams.set("ordering", params.ordering);

    // IMPORTANT: Trailing slash for DRF
    const url = `/admin/inquiries/${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    const response = await http.get<PaginatedResponse<InquiryListItem>>(url);
    return response.data;
  },

  async get(id: string): Promise<InquiryDetail> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.get<InquiryDetail>(`/admin/inquiries/${id}/`);
    return response.data;
  },

  async updateStatus(id: string, status: InquiryStatus): Promise<InquiryDetail> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.patch<InquiryDetail>(`/admin/inquiries/${id}/`, {
      status,
    });
    return response.data;
  },

  async updateNote(id: string, internal_note: string): Promise<InquiryDetail> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.patch<InquiryDetail>(`/admin/inquiries/${id}/`, {
      internal_note,
    });
    return response.data;
  },

  async composeQuote(data: QuoteComposeRequest): Promise<QuoteComposeResponse> {
    // IMPORTANT: Trailing slash for DRF
    const response = await http.post<QuoteComposeResponse>(
      "/quote/compose/",
      data
    );
    return response.data;
  },
};
