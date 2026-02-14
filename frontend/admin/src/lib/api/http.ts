import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { TokenStore } from "./token-store";

// NGROK/Gateway desteği: Boş string = relative path (aynı origin)
// Gateway üzerinden çalışırken NEXT_PUBLIC_BACKEND_URL="" olmalı
// Lokal geliştirmede NEXT_PUBLIC_BACKEND_URL="http://localhost:8000"
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "";

// basePath: "/admin" olduğu için relative API path'lerinin başına eklenmeli
const BASE_PATH = "/admin";
const API_BASE_URL = BACKEND_URL ? `${BACKEND_URL}/api/v1` : `${BASE_PATH}/api/v1`;

/**
 * Django APPEND_SLASH=True ile uyumluluk için trailing slash garantisi
 * POST/PATCH/PUT/DELETE isteklerinde slash yoksa 500 hatası oluşur
 */
function ensureTrailingSlash(url: string): string {
  // Query string varsa ayır
  const [path, query] = url.split("?");
  // Path zaten slash ile bitiyorsa veya dosya uzantısı varsa dokunma
  if (path.endsWith("/") || /\.\w+$/.test(path)) {
    return url;
  }
  // Trailing slash ekle
  return query ? `${path}/?${query}` : `${path}/`;
}

// Paths that should NEVER have Authorization header attached
// These are public endpoints that don't need auth and can fail with stale tokens
const PUBLIC_PATHS = [
  "/auth/login/",
  "/auth/refresh/",
  "/health/",
  "/health",
  "/schema/",
  "/docs/",
];

/**
 * Check if a URL is a public path that shouldn't have Authorization header
 */
function isPublicPath(url: string | undefined): boolean {
  if (!url) return false;
  return PUBLIC_PATHS.some((p) => url.includes(p));
}

// Create axios instance
// baseURL: relative path ("/api/v1") veya absolute ("http://localhost:8000/api/v1")
export const http = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
    // Ngrok browser warning bypass - required for external device access
    "ngrok-skip-browser-warning": "true",
  },
});

// Request interceptor - trailing slash + Authorization header
http.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Django APPEND_SLASH uyumluluğu: POST/PATCH/PUT/DELETE için trailing slash garantisi
    // Bu olmadan Django RuntimeError verir
    const method = config.method?.toUpperCase();
    if (method && ["POST", "PATCH", "PUT", "DELETE"].includes(method) && config.url) {
      config.url = ensureTrailingSlash(config.url);
    }

    const url = config.url ?? "";

    // CRITICAL: Never attach Authorization to public paths
    if (isPublicPath(url)) {
      // Explicitly remove Authorization header if somehow present
      if (config.headers) {
        delete config.headers.Authorization;
      }

      // Dev-only debug logging
      if (process.env.NODE_ENV === "development") {
        console.log(`[HTTP] Public path: ${url} - NO Authorization header`);
      }

      return config;
    }

    // For protected paths, attach token if available
    const token = TokenStore.getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Track if we're currently refreshing to avoid multiple refresh calls
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response interceptor - handle 401 and token refresh
// IMPORTANT: We do NOT redirect here. Let React components handle auth state.
http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Don't try to refresh for login/refresh endpoints
    if (isPublicPath(originalRequest?.url)) {
      return Promise.reject(error);
    }

    // If 401 and we haven't tried refreshing yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = TokenStore.getRefreshToken();

      // No refresh token - just reject, let component handle it
      if (!refreshToken) {
        TokenStore.clearTokens();
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Wait for the refresh to complete
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return http(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Use raw axios (not http instance) to avoid interceptor loops
        // Also don't send any Authorization header for refresh
        // API_BASE_URL supports both relative ("/api/v1") and absolute URLs
        const response = await axios.post(
          `${API_BASE_URL}/auth/refresh/`,
          { refresh: refreshToken },
          {
            headers: {
              "Content-Type": "application/json",
              "ngrok-skip-browser-warning": "true",
              // Explicitly no Authorization header
            },
          }
        );

        const { access } = response.data;
        TokenStore.setTokens(access, refreshToken);

        processQueue(null, access);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access}`;
        }

        return http(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        TokenStore.clearTokens();
        // Do NOT redirect here - let the component handle auth state
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

/**
 * Check if backend health endpoint is reachable
 * Useful for diagnostics on login page
 */
export async function checkBackendHealth(): Promise<{
  ok: boolean;
  message: string;
}> {
  try {
    const response = await axios.get(`${API_BASE_URL}/health/`, {
      timeout: 5000,
      headers: {
        "ngrok-skip-browser-warning": "true",
      },
    });
    return {
      ok: true,
      message: `Backend OK (${response.status})`,
    };
  } catch (error) {
    const axiosError = error as AxiosError;
    if (axiosError.response) {
      return {
        ok: false,
        message: `Backend error: ${axiosError.response.status}`,
      };
    }
    return {
      ok: false,
      message: "Backend unreachable",
    };
  }
}
