"use client";

import { http } from "./http";

/**
 * API capability detection
 *
 * Check if an endpoint exists by attempting a request.
 * Only 404 means "endpoint missing". All other responses (including errors like
 * 401, 403, 400, 405) mean the endpoint exists but may require auth or different method.
 */

// Store both capability result and the status code for debugging
interface CapabilityResult {
  exists: boolean;
  status: number | null;
  error?: string;
}

const capabilityCache: Record<string, CapabilityResult> = {};

export async function checkEndpointExists(
  method: "GET" | "POST" | "PATCH" | "DELETE" | "OPTIONS" | "HEAD",
  path: string
): Promise<boolean> {
  const cacheKey = `${method}:${path}`;

  if (cacheKey in capabilityCache) {
    return capabilityCache[cacheKey].exists;
  }

  try {
    let response;
    
    // Use appropriate method based on what we're checking
    switch (method) {
      case "OPTIONS":
        response = await http.options(path);
        break;
      case "HEAD":
        response = await http.head(path);
        break;
      case "GET":
        response = await http.get(path);
        break;
      default:
        // For POST/PATCH/DELETE, use OPTIONS to avoid side effects
        response = await http.options(path);
        break;
    }
    
    capabilityCache[cacheKey] = { 
      exists: true, 
      status: response.status 
    };
    return true;
  } catch (error: unknown) {
    const axiosError = error as { response?: { status?: number }; message?: string };
    const status = axiosError.response?.status ?? null;

    // ONLY treat 404 as "missing endpoint"
    // All other statuses mean the endpoint exists:
    // - 200, 201, 202, 204: success
    // - 301, 302: redirect (endpoint exists)
    // - 400: bad request (endpoint exists, validation failed)
    // - 401, 403: auth error (endpoint exists, need auth)
    // - 405: method not allowed (endpoint exists, different method)
    if (status === 404) {
      capabilityCache[cacheKey] = { 
        exists: false, 
        status, 
        error: "Not Found" 
      };
      return false;
    }

    // Any other response (including network errors) assume endpoint exists
    // This is safer - we'd rather show edit UI than hide it incorrectly
    capabilityCache[cacheKey] = { 
      exists: true, 
      status, 
      error: axiosError.message 
    };
    return true;
  }
}

/**
 * Admin API capabilities interface
 */
export interface AdminCapabilities {
  canCreateProduct: boolean;
  canPatchProduct: boolean;
  canDeleteProduct: boolean;
  canCreateVariant: boolean;
  canPatchVariant: boolean;
  canDeleteVariant: boolean;
  canBulkUpdateVariants: boolean;
  canListTemplates: boolean;
  canApplyTemplate: boolean;
  canGenerateProducts: boolean;
}

let cachedCapabilities: AdminCapabilities | null = null;

/**
 * Check all admin capabilities at once
 * 
 * IMPORTANT: We check LIST endpoints instead of instance endpoints.
 * DRF routers always provide instance CRUD if the list endpoint exists.
 * Checking /admin/products/test-slug/ would return 404 because "test-slug" doesn't exist,
 * NOT because the endpoint is missing.
 */
export async function checkAdminCapabilities(): Promise<AdminCapabilities> {
  if (cachedCapabilities) {
    return cachedCapabilities;
  }

  // Check all capabilities in parallel
  // KEY FIX: Use OPTIONS on LIST endpoints to detect if the ViewSet is registered
  // DRF ViewSets always provide all CRUD operations if registered
  const [
    productsEndpointExists,
    variantsEndpointExists,
    bulkEndpointExists,
    templatesEndpointExists,
    generateEndpointExists,
  ] = await Promise.all([
    // Check if products ViewSet is registered (list endpoint)
    checkEndpointExists("OPTIONS", "/admin/products/"),
    // Check if variants ViewSet is registered (list endpoint)
    checkEndpointExists("OPTIONS", "/admin/variants/"),
    // Check bulk update endpoint specifically
    checkEndpointExists("OPTIONS", "/admin/variants/bulk/"),
    // Check spec-templates list
    checkEndpointExists("OPTIONS", "/admin/spec-templates/"),
    // Check taxonomy generate endpoint
    checkEndpointExists("OPTIONS", "/admin/taxonomy/generate-products/"),
  ]);

  // If the ViewSet is registered, ALL CRUD operations are available
  cachedCapabilities = {
    canCreateProduct: productsEndpointExists,
    canPatchProduct: productsEndpointExists,  // Same ViewSet = same capability
    canDeleteProduct: productsEndpointExists, // Same ViewSet = same capability
    canCreateVariant: variantsEndpointExists,
    canPatchVariant: variantsEndpointExists,  // Same ViewSet = same capability
    canDeleteVariant: variantsEndpointExists, // Same ViewSet = same capability
    canBulkUpdateVariants: bulkEndpointExists,
    canListTemplates: templatesEndpointExists,
    canApplyTemplate: productsEndpointExists, // Custom action on products ViewSet
    canGenerateProducts: generateEndpointExists,
  };

  // Debug logging in development
  if (process.env.NODE_ENV === "development") {
    console.log("[Capabilities] Admin API check results:", cachedCapabilities);
    console.log("[Capabilities] Raw cache:", capabilityCache);
  }

  return cachedCapabilities;
}

/**
 * Get the raw capability cache for debugging
 */
export function getCapabilityCache(): Record<string, CapabilityResult> {
  return { ...capabilityCache };
}

/**
 * Clear capability cache (useful after auth changes)
 */
export function clearCapabilityCache(): void {
  Object.keys(capabilityCache).forEach((key) => delete capabilityCache[key]);
  cachedCapabilities = null;
}

// Legacy exports for backward compatibility
export const apiCapabilities = {
  async canGenerateProducts(): Promise<boolean> {
    return checkEndpointExists("OPTIONS", "/admin/taxonomy/generate-products/");
  },

  async canListTemplates(): Promise<boolean> {
    return checkEndpointExists("OPTIONS", "/admin/spec-templates/");
  },

  async canApplyTemplate(): Promise<boolean> {
    const caps = await checkAdminCapabilities();
    return caps.canApplyTemplate;
  },
};
