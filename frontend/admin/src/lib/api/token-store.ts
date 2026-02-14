/**
 * Token Store - Abstract storage for JWT tokens
 *
 * Currently uses localStorage for simplicity.
 * Can be migrated to httpOnly cookies later by changing this implementation.
 */

const ACCESS_TOKEN_KEY = "gastrotech_access_token";
const REFRESH_TOKEN_KEY = "gastrotech_refresh_token";

// In-memory cache for faster access (avoids localStorage reads)
let cachedAccessToken: string | null = null;
let cachedRefreshToken: string | null = null;
let initialized = false;

function initFromStorage() {
  if (initialized || typeof window === "undefined") return;
  cachedAccessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
  cachedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  initialized = true;
}

export const TokenStore = {
  getAccessToken(): string | null {
    initFromStorage();
    return cachedAccessToken;
  },

  getRefreshToken(): string | null {
    initFromStorage();
    return cachedRefreshToken;
  },

  setTokens(access: string, refresh: string): void {
    if (typeof window === "undefined") return;
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
    cachedAccessToken = access;
    cachedRefreshToken = refresh;
    initialized = true;
  },

  clearTokens(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    cachedAccessToken = null;
    cachedRefreshToken = null;
  },

  hasTokens(): boolean {
    initFromStorage();
    return !!cachedAccessToken;
  },
};
