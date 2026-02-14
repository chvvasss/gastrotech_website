// ============================================================================
// API Types - Aligned with Django Backend
// ============================================================================

// Auth Types
export interface User {
  id: string;
  email: string;
  role: "admin" | "editor";
  is_active: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

// Inquiry Types
export type InquiryStatus = "new" | "in_progress" | "closed";

export interface InquiryListItem {
  id: string;
  full_name: string;
  email: string;
  phone: string;
  company: string;
  status: InquiryStatus;
  items_count: number;
  items_summary: string;
  product_slug_snapshot: string;
  model_code_snapshot: string;
  created_at: string;
  updated_at: string;
}

export interface InquiryItem {
  id: number;
  model_code_snapshot: string;
  model_name_tr_snapshot: string;
  product_title_tr_snapshot: string;
  product_slug_snapshot: string;
  series_slug_snapshot: string;
  qty: number;
}

export interface InquiryDetail extends InquiryListItem {
  message: string;
  source_url: string;
  utm_source: string;
  utm_medium: string;
  utm_campaign: string;
  internal_note: string;
  items: InquiryItem[];
}

// Catalog Types
export type ProductStatus = "draft" | "active" | "archived";

export interface ProductListItem {
  title_tr: string;
  title_en: string;
  slug: string;
  series_slug: string;
  series_name: string;
  category_slug: string;
  category_name: string;
  status: ProductStatus;
  is_featured: boolean;
  pdf_ref: string;
  primary_image_url: string | null;
  variants_count: number;
}

export interface Series {
  id: string;
  name: string;
  slug: string;
  category_slug: string;
  description_short: string;
  order: number;
  is_featured: boolean;
  cover_media_url: string | null;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  menu_label: string;
  description_short: string;
  order: number;
  is_featured: boolean;
  cover_media_url: string | null;
  parent_slug: string | null;
}

export interface CategoryWithCounts extends Category {
  series_count: number;
  products_count: number;
}

export interface SeriesWithCounts extends Series {
  products_count: number;
}

export interface CategoryDetail extends Category {
  series: SeriesWithCounts[];
  products_count: number;
}

export interface BrandCategory {
  id?: string;
  category: string;
  category_name?: string;
  category_slug?: string;
  is_active: boolean;
  order: number;
}

export interface Brand {
  id: string;
  name: string;
  slug: string;
  description?: string;
  website_url?: string;
  logo_url?: string | null;
  is_active: boolean;
  order: number;
  category_count?: number;
  product_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface BrandDetail extends Brand {
  categories_list: BrandCategory[];
}

// Navigation Types (from /api/v1/nav)
export interface NavSeries {
  id: string;
  name: string;
  slug: string;
  order: number;
  is_featured: boolean;
  products_count?: number;
  is_visible?: boolean;
}

export interface NavCategory {
  id: string;
  name: string;
  slug: string;
  menu_label: string;
  order: number;
  is_featured: boolean;
  cover_media_url: string | null;
  series: NavSeries[];
  visible_series?: NavSeries[];
}

// Taxonomy Types
export interface TaxonomyNode {
  id: string;
  name: string;
  slug: string;
  order: number;
  parent_slug: string | null;
  depth: number;
  full_path: string;
  children: TaxonomyNode[];
}

// SpecKey Types
export interface SpecKey {
  slug: string;
  label_tr: string;
  label_en: string | null;
  unit: string | null;
  value_type: "text" | "number" | "boolean";
  sort_order: number;
}

// Variant Types
export interface Variant {
  model_code: string;
  name_tr: string;
  name_en: string | null;
  dimensions: string | null;
  weight_kg: number | null;
  list_price: number | null;
  specs: Record<string, string | number | boolean> | null;
  spec_row: Array<{ key: string; value: string | number | null }>;
}

// Product Media Types
export interface ProductMedia {
  id: number;  // ProductMedia ID (for delete/reorder)
  media_id: string;  // Media UUID (for file URL reference)
  kind: "image" | "pdf" | "video";
  filename: string;
  file_url: string;
  width: number | null;
  height: number | null;
  alt: string;
  sort_order: number;
  is_primary: boolean;
}

// Product Detail Types
export interface ProductDetail {
  id: string;
  title_tr: string;
  title_en: string | null;
  slug: string;
  series_slug: string;
  series_name: string;
  category_slug: string;
  category_name: string;
  primary_node_slug: string | null;
  status: ProductStatus;
  is_featured: boolean;
  pdf_ref: string | null;
  general_features: string[] | null;
  notes: string | null;
  spec_layout: string[] | null;
  spec_keys_resolved: SpecKey[];
  variants: Variant[];
  product_media: ProductMedia[];
  long_description: string | null;
  seo_title: string | null;
  seo_description: string | null;
}

// Media Upload Response
export interface MediaUploadResponse {
  id: string;
  file_url: string;
  checksum_sha256: string;
  kind: "image" | "pdf" | "video";
  filename: string;
  content_type: string;
  size_bytes: number;
  width: number | null;
  height: number | null;
}

// Product Media Upload Response
export interface ProductMediaUploadResponse {
  id: string;
  media_id: string;
  file_url: string;
  alt: string;
  sort_order: number;
  is_primary: boolean;
}

// SpecTemplate Types
export interface SpecTemplate {
  id: string;
  name: string;
  spec_layout: string[];
  default_general_features: string[] | null;
  default_notes: string | null;
}

// Quote Compose Types
export interface QuoteComposeItem {
  model_code: string;
  qty: number;
}

export interface QuoteComposeRequest {
  full_name?: string;
  company?: string;
  note?: string;
  items: QuoteComposeItem[];
}

export interface QuoteComposeItemResolved {
  model_code: string;
  qty: number;
  name_tr: string | null;
  product_slug: string | null;
  product_title_tr: string | null;
  series_slug: string | null;
  category_slug: string | null;
  dimensions: string | null;
  weight_kg: number | null;
  list_price: number | null;
  spec_row: Array<{
    key: string;
    label_tr: string;
    value: string;
    unit: string;
  }> | null;
  error: string | null;
}

export interface QuoteComposeResponse {
  items_resolved: QuoteComposeItemResolved[];
  message_tr: string;
  message_en: string | null;
}

// Pagination Types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Dashboard Stats (Full)
export interface DashboardStats {
  // Catalog metrics
  categories_total: number;
  series_total: number;
  taxonomy_nodes_total: number;
  products_total: number;
  products_active: number;
  products_draft: number;
  products_archived: number;
  variants_total: number;
  // Media metrics
  media_total: number;
  media_unreferenced_total: number;
  // Inquiry metrics
  inquiries_total: number;
  inquiries_new_range: number;
  inquiries_open: number;
  inquiries_closed: number;
  inquiry_items_total: number;
  // Charts
  inquiries_by_day: Array<{ date: string; count: number }>;
  products_by_status: { active: number; draft: number; archived: number };
  top_requested_variants: Array<{ model_code: string; name_tr: string; count: number }>;
  // Recent activity
  recently_updated_products: Array<{
    title_tr: string;
    slug: string;
    status: ProductStatus;
    updated_at: string;
  }>;
  recently_updated_inquiries: Array<{
    id: string;
    full_name: string;
    company: string;
    status: InquiryStatus;
    items_count: number;
    created_at: string;
  }>;
}
