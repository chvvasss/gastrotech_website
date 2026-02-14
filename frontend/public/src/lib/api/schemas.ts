import { z } from "zod";

// ============================================================================
// Media
// ============================================================================

export const MediaMetadataSchema = z.object({
  id: z.string(),
  kind: z.string(),
  filename: z.string(),
  content_type: z.string().nullable(),
  size_bytes: z.number().nullable(),
  width: z.number().nullable(),
  height: z.number().nullable(),
  checksum_sha256: z.string().nullable(),
  file_url: z.string(),
});

export type MediaMetadata = z.infer<typeof MediaMetadataSchema>;

// ============================================================================
// Series (Moved to top to prevent circular dependency / initialization issues)
// ============================================================================

export const SeriesSchema = z.object({
  id: z.string(),
  category_slug: z.string(),
  name: z.string(),
  slug: z.string(),
  description_short: z.string().nullable(),
  order: z.number(),
  is_featured: z.boolean(),
  cover_media_url: z.string().nullable(),
  products_count: z.number().optional(),
  is_visible: z.boolean().optional(),
  single_product_slug: z.string().nullable().optional(),
  single_product_name: z.string().nullable().optional(),
  single_product_image_url: z.string().nullable().optional(),
});

export type Series = z.infer<typeof SeriesSchema>;

// ============================================================================
// Navigation
// ============================================================================

export const NavSeriesSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  order: z.number(),
  is_featured: z.boolean(),
  products_count: z.number().optional(),
  is_visible: z.boolean().optional(),
  single_product_slug: z.string().nullable().optional(),
  single_product_name: z.string().nullable().optional(),
  single_product_image_url: z.string().nullable().optional(),
});

export type NavSeries = z.infer<typeof NavSeriesSchema>;

export const NavCategorySchema: z.ZodType<NavCategory> = z.lazy(() =>
  z.object({
    id: z.string(),
    name: z.string(),
    slug: z.string(),
    menu_label: z.string().nullable(),
    order: z.number(),
    is_featured: z.boolean(),
    cover_media_url: z.string().nullable(),
    series: z.array(NavSeriesSchema),
    visible_series: z.array(NavSeriesSchema).optional(),
    children: z.array(NavCategorySchema).optional(),
    parent_slug: z.string().nullable().optional(),
  })
);

export interface NavCategory {
  id: string;
  name: string;
  slug: string;
  menu_label: string | null;
  order: number;
  is_featured: boolean;
  cover_media_url: string | null;
  series: NavSeries[];
  visible_series?: NavSeries[];
  children?: NavCategory[];
  parent_slug?: string | null;
}


// ============================================================================
// Categories
// ============================================================================

export const CategorySchema: z.ZodType<Category> = z.lazy(() =>
  z.object({
    id: z.string(),
    name: z.string(),
    slug: z.string(),
    menu_label: z.string().nullable().optional(),
    description_short: z.string().nullable(),
    order: z.number(),
    is_featured: z.boolean().optional(),
    cover_media_url: z.string().nullable(),
    parent_slug: z.string().nullable().optional(),
    is_leaf: z.boolean().optional(),
    products_count: z.number().optional(),
    subcategory_count: z.number().optional(),
    children: z.array(CategorySchema).optional(),
  })
);

export interface Category {
  id: string;
  name: string;
  slug: string;
  menu_label?: string | null;
  description_short: string | null;
  order: number;
  is_featured?: boolean;
  cover_media_url: string | null;
  parent_slug?: string | null;
  is_leaf?: boolean;
  products_count?: number;
  subcategory_count?: number;
  children?: Category[];
}

// ============================================================================
// Logo Groups (for category landing pages)
// ============================================================================

export const LogoGroupSeriesSchema = z.object({
  series_id: z.string(),
  series_name: z.string(),
  series_slug: z.string(),
  order: z.number(),
  is_heading: z.boolean(),
  cover_media_url: z.string().nullable(),
});

export type LogoGroupSeries = z.infer<typeof LogoGroupSeriesSchema>;

export const LogoGroupSchema = z.object({
  id: z.string(),
  brand_id: z.string(),
  brand_name: z.string(),
  brand_slug: z.string(),
  title: z.string(),
  logo_url: z.string().nullable(),
  order: z.number(),
  is_active: z.boolean(),
  series_list: z.array(LogoGroupSeriesSchema),
});

export type LogoGroup = z.infer<typeof LogoGroupSchema>;




// Category Detail (with logo groups and subcategories)
export const CategoryDetailSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  menu_label: z.string().nullable().optional(),
  description_short: z.string().nullable(),
  order: z.number(),
  is_featured: z.boolean().optional(),
  cover_media_url: z.string().nullable(),
  parent_slug: z.string().nullable().optional(),
  series_mode: z.string().optional(),
  subcategories: z.array(z.lazy(() => CategorySchema)).optional(),
  logo_groups: z.array(z.lazy(() => LogoGroupSchema)).optional(),
  series: z.array(z.lazy(() => SeriesSchema)).optional(),
  visible_series: z.array(z.lazy(() => SeriesSchema)).optional(),
  products_count: z.number().optional(),
});

export type CategoryDetail = z.infer<typeof CategoryDetailSchema>;

// ============================================================================
// Taxonomy
// ============================================================================

export const TaxonomyNodeSchema: z.ZodType<TaxonomyNode> = z.lazy(() =>
  z.object({
    id: z.string(),
    name: z.string(),
    slug: z.string(),
    order: z.number(),
    parent_slug: z.string().nullable(),
    children: z.array(TaxonomyNodeSchema).optional(),
    depth: z.number().optional(),
    full_path: z.string().optional(),
  })
);

export interface TaxonomyNode {
  id: string;
  name: string;
  slug: string;
  order: number;
  parent_slug: string | null;
  children?: TaxonomyNode[];
  depth?: number;
  full_path?: string;
}

// ============================================================================
// Spec Keys
// ============================================================================

export const SpecKeySchema = z.object({
  slug: z.string(),
  label_tr: z.string(),
  label_en: z.string().nullable(),
  unit: z.string().nullable(),
  value_type: z.string(),
  sort_order: z.number(),
});

export type SpecKey = z.infer<typeof SpecKeySchema>;

// ============================================================================
// Brands
// ============================================================================

export const BrandSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  logo_url: z.string().nullable(),
  description: z.string().nullable(),
  website_url: z.string().nullable(),
  is_active: z.boolean(),
  order: z.number(),
});

export type Brand = z.infer<typeof BrandSchema>;

// ============================================================================
// Variants
// ============================================================================

export const SpecRowItemSchema = z.object({
  key: z.string(),
  value: z.union([z.string(), z.number(), z.null()]),
});

export const VariantSchema = z.object({
  id: z.string(),  // UUID for cart operations
  model_code: z.string(),
  name_tr: z.string().nullable(),
  name_en: z.string().nullable(),
  dimensions: z.string().nullable(),
  weight_kg: z.union([z.string(), z.number()]).nullable(),
  list_price: z.union([z.string(), z.number()]).nullable().optional(),  // Optional when prices hidden
  specs: z.record(z.any()).nullable(),
  spec_row: z.array(SpecRowItemSchema).optional(),
});

export type Variant = z.infer<typeof VariantSchema>;

// ============================================================================
// Product Media
// ============================================================================

export const ProductMediaSchema = z.object({
  id: z.number(),
  media_id: z.string(),
  kind: z.string(),
  filename: z.string(),
  file_url: z.string().nullable(),
  width: z.number().nullable(),
  height: z.number().nullable(),
  alt: z.string().nullable(),
  sort_order: z.number(),
  is_primary: z.boolean(),
  variant_id: z.string().nullable().optional(),
});

export type ProductMedia = z.infer<typeof ProductMediaSchema>;

// ============================================================================
// Products
// ============================================================================

export const ProductListItemSchema = z.object({
  title_tr: z.string().nullable(),
  title_en: z.string().nullable(),
  slug: z.string(),
  series_slug: z.string(),
  series_name: z.string(),
  category_slug: z.string(),
  category_name: z.string(),
  brand_slug: z.string().nullable(),
  brand_name: z.string().nullable(),
  status: z.string(),
  is_featured: z.boolean(),
  pdf_ref: z.string().nullable(),
  primary_image_url: z.string().nullable(),
  variants_count: z.number(),
});

export type ProductListItem = z.infer<typeof ProductListItemSchema>;

export const ProductDetailSchema = z.object({
  id: z.string(),
  title_tr: z.string().nullable(),
  title_en: z.string().nullable(),
  slug: z.string(),
  series_slug: z.string(),
  series_name: z.string(),
  category_slug: z.string(),
  category_name: z.string(),
  brand_slug: z.string().nullable(),
  brand_name: z.string().nullable(),
  brand_logo: z.string().nullable().optional(),
  primary_node_slug: z.string().nullable(),
  status: z.string(),
  is_featured: z.boolean(),
  pdf_ref: z.string().nullable(),
  general_features: z.array(z.string()).nullable(),
  notes: z.array(z.string()).nullable(),
  spec_layout: z.array(z.string()).nullable(),
  spec_keys_resolved: z.array(SpecKeySchema),
  variants: z.array(VariantSchema),
  product_media: z.array(ProductMediaSchema),
  long_description: z.string().nullable(),
  seo_title: z.string().nullable(),
  seo_description: z.string().nullable(),
});

export type ProductDetail = z.infer<typeof ProductDetailSchema>;

// ============================================================================
// Product List Response (Paginated)
// ============================================================================

export const ProductListResponseSchema = z.object({
  next: z.string().nullable(),
  previous: z.string().nullable(),
  results: z.array(ProductListItemSchema),
});

export type ProductListResponse = z.infer<typeof ProductListResponseSchema>;

// ============================================================================
// Catalog Assets
// ============================================================================

export const CatalogAssetSchema = z.object({
  id: z.string(),
  title_tr: z.string(),
  title_en: z.string().nullable(),
  is_primary: z.boolean(),
  order: z.number(),
  file_url: z.string().nullable(),
  file_size: z.number().nullable(),
});

export type CatalogAsset = z.infer<typeof CatalogAssetSchema>;

// ============================================================================
// Category Catalogs (catalog mode)
// ============================================================================

export const CategoryCatalogSchema = z.object({
  id: z.string(),
  title_tr: z.string(),
  title_en: z.string().nullable(),
  description: z.string().nullable(),
  order: z.number(),
  file_url: z.string().nullable(),
  file_size: z.number().nullable(),
  filename: z.string().nullable(),
  category_slug: z.string(),
  category_name: z.string(),
});

export type CategoryCatalog = z.infer<typeof CategoryCatalogSchema>;

// ============================================================================
// Cart
// ============================================================================

export const CartItemSchema = z.object({
  id: z.string(),
  variant: z.object({
    id: z.string(),
    model_code: z.string(),
    name_tr: z.string().nullable(),
    name_en: z.string().nullable(),
    sku: z.string().nullable(),
    size: z.string().nullable(),
    color: z.string().nullable(),
    dimensions: z.string().nullable(),
    price: z.union([z.string(), z.number()]).nullable(),
    currency: z.string().nullable(),
    stock_qty: z.union([z.string(), z.number()]).nullable(),
    is_available: z.boolean(),
    product_name: z.string(),
    product_slug: z.string(),
  }),
  quantity: z.number(),
  unit_price_snapshot: z.union([z.string(), z.number()]).nullable(),
  currency_snapshot: z.string(),
  product_name_snapshot: z.string(),
  variant_label_snapshot: z.string(),
  added_at: z.string(),
});

export type CartItem = z.infer<typeof CartItemSchema>;

export const CartTotalsSchema = z.object({
  subtotal: z.union([z.string(), z.number()]),
  item_count: z.number(),
  line_count: z.number(),
  currency: z.string(),
  has_pricing_gaps: z.boolean(),
});

export const CartSchema = z.object({
  id: z.string(),
  token: z.string(),
  status: z.string(),
  currency: z.string(),
  is_anonymous: z.boolean().optional(),
  items: z.array(CartItemSchema),
  totals: CartTotalsSchema,
  warnings: z.array(z.any()).optional(),
});

export type Cart = z.infer<typeof CartSchema>;

export const CartTokenResponseSchema = z.object({
  cart_token: z.string(),
  cart: CartSchema,
});

export type CartTokenResponse = z.infer<typeof CartTokenResponseSchema>;

// ============================================================================
// Inquiries
// ============================================================================

export const InquiryItemSchema = z.object({
  model_code: z.string(),
  qty: z.number().default(1),
});

export const InquiryCreateSchema = z.object({
  full_name: z.string().min(2),
  email: z.string().email(),
  phone: z.string().optional(),
  company: z.string().optional(),
  message: z.string().optional(),
  items: z.array(InquiryItemSchema).optional(),
  product_slug: z.string().optional(),
  model_code: z.string().optional(),
});

export type InquiryCreate = z.infer<typeof InquiryCreateSchema>;

export const InquiryResponseSchema = z.object({
  id: z.string(),
  status: z.string(),
  items_count: z.number(),
});

export type InquiryResponse = z.infer<typeof InquiryResponseSchema>;

// ============================================================================
// Blog
// ============================================================================

export const BlogCategorySchema = z.object({
  id: z.string(),
  name_tr: z.string(),
  name_en: z.string().nullable().optional(),
  slug: z.string(),
  description: z.string().nullable(),
  order: z.number(),
  posts_count: z.number().optional(),
});

export type BlogCategory = z.infer<typeof BlogCategorySchema>;

export const BlogTagSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
});

export type BlogTag = z.infer<typeof BlogTagSchema>;

export const BlogPostListSchema = z.object({
  id: z.string(),
  title: z.string(),
  slug: z.string(),
  excerpt: z.string().nullable(),
  cover_url: z.string().nullable(),
  category: BlogCategorySchema.nullable(),
  tags: z.array(BlogTagSchema),
  author_name: z.string().nullable(),
  published_at: z.string().nullable(),
  is_featured: z.boolean(),
  reading_time_min: z.number(),
  view_count: z.number(),
});

export type BlogPostListItem = z.infer<typeof BlogPostListSchema>;

export const BlogPostDetailSchema = BlogPostListSchema.extend({
  content: z.string().nullable(),
  meta_title: z.string().nullable(),
  meta_description: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type BlogPostDetail = z.infer<typeof BlogPostDetailSchema>;

export const BlogPostListResponseSchema = z.union([
  z.array(BlogPostListSchema),
  z.object({
    count: z.number().optional(),
    next: z.string().nullable().optional(),
    previous: z.string().nullable().optional(),
    results: z.array(BlogPostListSchema),
  }),
]);

export type BlogPostListResponse = {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results: BlogPostListItem[];
};

// ============================================================================
// PLP (Product Listing Page)
// ============================================================================

export const PLPBrandFacetSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  count: z.number(),
  logo_url: z.string().nullable(),
  selected: z.boolean(),
});

export type PLPBrandFacet = z.infer<typeof PLPBrandFacetSchema>;

export const PLPCategoryFacetSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  count: z.number(),
  depth: z.number().optional(),
});

export type PLPCategoryFacet = z.infer<typeof PLPCategoryFacetSchema>;

export const PLPPriceFacetSchema = z.object({
  min: z.number(),
  max: z.number(),
});

export type PLPPriceFacet = z.infer<typeof PLPPriceFacetSchema>;



export const PLPSeriesFacetSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  count: z.number(),
  selected: z.boolean().optional(),
});

export type PLPSeriesFacet = z.infer<typeof PLPSeriesFacetSchema>;

export const PLPAttributeOptionSchema = z.object({
  value: z.string(),
  count: z.number(),
  label: z.string(),
  selected: z.boolean().optional(),
});

export const PLPAttributeFacetSchema = z.object({
  key: z.string(),
  label: z.string(),
  options: z.array(PLPAttributeOptionSchema),
});

export type PLPAttributeFacet = z.infer<typeof PLPAttributeFacetSchema>;

export const PLPProductPriceSchema = z.object({
  min: z.number(),
  max: z.number(),
  currency: z.string(),
});

export const PLPProductSchema = z.object({
  id: z.string(),
  slug: z.string(),
  name: z.string(),
  title_tr: z.string().nullable(),
  brand: z.object({
    id: z.string(),
    name: z.string(),
    slug: z.string(),
  }).nullable(),
  hero_image_url: z.string().nullable(),
  price: PLPProductPriceSchema.nullable(),
  in_stock: z.boolean(),
  short_specs: z.array(z.string()),
});

export type PLPProduct = z.infer<typeof PLPProductSchema>;

export const PLPPaginationSchema = z.object({
  total: z.number(),
  page: z.number(),
  page_size: z.number(),
  total_pages: z.number(),
  has_next: z.boolean(),
  has_prev: z.boolean(),
});

export type PLPPagination = z.infer<typeof PLPPaginationSchema>;

export const PLPFacetsSchema = z.object({
  brands: z.array(PLPBrandFacetSchema),
  categories: z.array(PLPCategoryFacetSchema),
  price: PLPPriceFacetSchema,
  series: z.array(PLPSeriesFacetSchema).optional(),
  attributes: z.array(PLPAttributeFacetSchema).optional(),
});


export type PLPFacets = z.infer<typeof PLPFacetsSchema>;

export const PLPSelectedFiltersSchema = z.object({
  brands: z.array(z.string()),
  price_min: z.number().nullable(),
  price_max: z.number().nullable(),
  in_stock: z.boolean(),
  series: z.array(z.string()).optional(),
  attrs: z.string().nullable().optional(),
});

export type PLPSelectedFilters = z.infer<typeof PLPSelectedFiltersSchema>;

export const PLPSortOptionSchema = z.object({
  key: z.string(),
  label: z.string(),
});

export type PLPSortOption = z.infer<typeof PLPSortOptionSchema>;

export const PLPCategoryInfoSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  description_short: z.string().nullable(),
  cover_media_url: z.string().nullable(),
  breadcrumbs: z.array(z.object({
    name: z.string(),
    slug: z.string(),
  })),
});

export type PLPCategoryInfo = z.infer<typeof PLPCategoryInfoSchema>;

export const PLPResponseSchema = z.object({
  catalog_mode: z.boolean().optional(),
  catalogs: z.array(z.lazy(() => CategoryCatalogSchema)).optional(),
  category: PLPCategoryInfoSchema,
  products: z.array(PLPProductSchema),
  pagination: PLPPaginationSchema,
  facets: PLPFacetsSchema,
  selected_filters: PLPSelectedFiltersSchema,
  sort: z.string(),
  sort_options: z.array(PLPSortOptionSchema),
});

export type PLPResponse = z.infer<typeof PLPResponseSchema>;
