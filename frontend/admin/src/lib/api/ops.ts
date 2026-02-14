import { http } from "./http";

export interface ImportJob {
  id: string;
  kind: "catalog_import" | "variants_csv" | "products_csv" | "taxonomy_csv";
  kind_display: string;
  status: "pending" | "validating" | "running" | "success" | "failed" | "partial";
  status_display: string;
  mode: "strict" | "smart";
  mode_display: string;
  created_by: string | null;
  created_by_email: string | null;
  input_file: string | null;
  file_hash: string;
  is_preview: boolean;
  allow_partial: boolean;
  report_json: ImportReport;
  total_rows: number;
  created_count: number;
  updated_count: number;
  skipped_count: number;
  error_count: number;
  warning_count: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at?: string;
}

export interface ImportReportIssue {
  row: number | null;
  column: string | null;
  value: string | null;
  severity: "error" | "warning" | "info";
  code: string;
  message: string;
  expected?: string | null;
}

export interface ImportReportCandidate {
  slug: string;
  name?: string;
  category_slug?: string;
  rows: number[];
}

export interface ImportReport {
  status: string;
  issues: ImportReportIssue[];
  candidates: {
    categories: ImportReportCandidate[];
    series: ImportReportCandidate[];
    brands: ImportReportCandidate[];
    products: ImportReportCandidate[];
  };
  normalization: {
    merged_continuation_rows: Array<{ primary_row: number; continuation_row: number }>;
    disambiguated_model_codes: Array<{ row: number; original: string; new: string }>;
    empty_value_normalizations: number;
  };
  counts: {
    total_product_rows: number;
    total_variant_rows: number;
    valid_product_rows: number;
    valid_variant_rows: number;
    error_rows: number;
    warning_rows: number;
    products_to_create: number;
    products_to_update: number;
    variants_to_create: number;
    variants_to_update: number;
  };
  products_data: Array<Record<string, unknown>>;
  variants_data: Array<Record<string, unknown>>;
  valid_rows: Array<{ row_num: number; data: Record<string, unknown>; type: string }>;
  // Legacy/error fields (optional for backward compatibility)
  column_error?: string;
  parse_error?: string;
  execution_error?: string;
  columns_found?: string[];
  rows?: Array<{ row: number; model_code?: string; slug?: string; action: string; errors: string[] }>;
  execution_errors?: Array<{ row: number; error: string }>;
}

export interface CommitResult {
  status: string;
  job_id: string;
  counts: {
    categories_created: number;
    brands_created: number;
    series_created: number;
    products_created: number;
    products_updated: number;
    variants_created: number;
    variants_updated: number;
  };
  db_verify: {
    enabled: boolean;
    verified_at: string;
    created_entities_found_in_db: boolean;
    created_category_slugs: string[];
    created_brand_slugs: string[];
    created_series_slugs: string[];
    created_product_slugs: string[];
    created_variant_model_codes: string[];
    verification_details: {
      categories_verified: boolean;
      brands_verified: boolean;
      series_verified: boolean;
      products_verified: boolean;
      variants_verified: boolean;
    };
  };
}

export interface AuditLog {
  id: string;
  actor: string | null;
  actor_email: string;
  action: string;
  entity_type: string;
  entity_id: string;
  entity_label: string;
  before_json: Record<string, unknown>;
  after_json: Record<string, unknown>;
  metadata: Record<string, unknown>;
  ip_address: string | null;
  user_agent: string;
  created_at: string;
}

export interface AuditLogListItem {
  id: string;
  actor_email: string;
  action: string;
  entity_type: string;
  entity_id: string;
  entity_label: string;
  created_at: string;
}

function extractArray<T>(data: T[] | { results: T[] } | unknown): T[] {
  if (Array.isArray(data)) {
    return data;
  }
  if (data && typeof data === "object" && "results" in data) {
    return (data as { results: T[] }).results;
  }
  return [];
}

export const opsApi = {
  async listImportJobs(params?: {
    kind?: string;
    status?: string;
  }): Promise<ImportJob[]> {
    const queryParams = new URLSearchParams();
    if (params?.kind) queryParams.set("kind", params.kind);
    if (params?.status) queryParams.set("status", params.status);

    const url = `/admin/import-jobs/${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    const response = await http.get(url);
    return extractArray<ImportJob>(response.data);
  },

  async getImportJob(id: string): Promise<ImportJob> {
    const response = await http.get<ImportJob>(`/admin/import-jobs/${id}/`);
    return response.data;
  },

  async validateImport(
    file: File,
    options: {
      mode?: "strict" | "smart";
      kind?: string;
      treatSlashAsHierarchy?: boolean;
      allowCreateMissingCategories?: boolean;
    } = {}
  ): Promise<ImportJob | { message: string; existing_job_id: string; job: ImportJob }> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("mode", options.mode ?? "strict");
    formData.append("kind", options.kind ?? "catalog_import");
    formData.append("treat_slash_as_hierarchy", String(options.treatSlashAsHierarchy ?? true));
    formData.append("allow_create_missing_categories", String(options.allowCreateMissingCategories ?? true));

    const response = await http.post<ImportJob | { message: string; existing_job_id: string; job: ImportJob }>(
      "/admin/import-jobs/validate/",
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return response.data;
  },

  async commitImport(
    jobId: string,
    options: {
      allowPartial?: boolean;
      treatSlashAsHierarchy?: boolean;
      allowCreateMissingCategories?: boolean;
    } = {}
  ): Promise<{ message: string; job_id: string; status: string; result: CommitResult }> {
    const response = await http.post(`/admin/import-jobs/${jobId}/commit/`, {
      allow_partial: options.allowPartial ?? false,
      treat_slash_as_hierarchy: options.treatSlashAsHierarchy ?? true,
      allow_create_missing_categories: options.allowCreateMissingCategories ?? true,
    });
    return response.data;
  },

  async downloadReport(jobId: string): Promise<Blob> {
    const response = await http.get(`/admin/import-jobs/${jobId}/report/`, {
      responseType: "blob",
    });
    return response.data;
  },

  async downloadTemplate(format: "xlsx" | "csv" = "xlsx", includeExamples: boolean = true): Promise<Blob> {
    const response = await http.get(`/admin/import-jobs/template/?fmt=${format}&include_examples=${includeExamples}`, {
      responseType: "blob",
    });
    return response.data;
  },

  async uploadVariantsCSV(
    file: File,
    options: { dryRun?: boolean; allowPartial?: boolean } = {}
  ): Promise<ImportJob | { message: string; existing_job_id: string; job: ImportJob }> {
    return this.validateImport(file, { mode: options.dryRun ? "strict" : "smart" });
  },

  async uploadProductsCSV(
    file: File,
    options: { dryRun?: boolean; allowPartial?: boolean } = {}
  ): Promise<ImportJob | { message: string; existing_job_id: string; job: ImportJob }> {
    return this.validateImport(file, { mode: options.dryRun ? "strict" : "smart" });
  },

  async applyImportJob(id: string): Promise<{ message: string; job_id: string; status: string; result: CommitResult }> {
    return this.commitImport(id);
  },

  async listAuditLogs(params?: {
    entity_type?: string;
    entity_id?: string;
    action?: string;
    actor?: string;
  }): Promise<AuditLogListItem[]> {
    const queryParams = new URLSearchParams();
    if (params?.entity_type) queryParams.set("entity_type", params.entity_type);
    if (params?.entity_id) queryParams.set("entity_id", params.entity_id);
    if (params?.action) queryParams.set("action", params.action);
    if (params?.actor) queryParams.set("actor", params.actor);

    const url = `/admin/audit-logs/${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    const response = await http.get(url);
    return extractArray<AuditLogListItem>(response.data);
  },

  async getAuditLog(id: string): Promise<AuditLog> {
    const response = await http.get<AuditLog>(`/admin/audit-logs/${id}/`);
    return response.data;
  },

  async cleanupAuditLogs(olderThanDays: number = 30): Promise<{ deleted_count: number; older_than_days: number; cutoff_date: string }> {
    const response = await http.delete(`/admin/audit-logs/cleanup/?older_than_days=${olderThanDays}`);
    return response.data;
  },
};
