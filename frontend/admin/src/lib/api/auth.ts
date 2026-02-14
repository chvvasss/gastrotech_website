import { http } from "./http";
import { TokenStore } from "./token-store";
import type { LoginRequest, TokenPair, User } from "@/types/api";
import { AxiosError } from "axios";

/**
 * Get a user-friendly error message from login error
 */
function getLoginErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const status = error.response?.status;
    const detail = error.response?.data?.detail;

    if (status === 401) {
      // Check if this might be token contamination
      if (detail?.includes("token") || detail?.includes("Token")) {
        return "Token contamination detected. Tokens cleared, please retry.";
      }
      return "Invalid email or password";
    }

    if (status === 400) {
      return detail || "Invalid request format";
    }

    if (status === 500) {
      return "Server error. Please try again later.";
    }

    if (!error.response) {
      return "Network error. Check your connection and backend status.";
    }

    return detail || `Error: ${status}`;
  }

  return "An unexpected error occurred";
}

export const authApi = {
  async login(data: LoginRequest): Promise<User> {
    // CRITICAL: Clear any stale tokens BEFORE attempting login
    // This prevents Authorization header contamination
    TokenStore.clearTokens();

    if (process.env.NODE_ENV === "development") {
      console.log("[Auth] Cleared tokens before login attempt");
    }

    try {
      // POST to login - interceptor will NOT add Authorization header for this path
      const response = await http.post<TokenPair>("/auth/login/", data);
      const { access, refresh } = response.data;
      TokenStore.setTokens(access, refresh);

      if (process.env.NODE_ENV === "development") {
        console.log("[Auth] Login successful, tokens stored");
      }

      // Fetch user info
      return this.me();
    } catch (error) {
      const message = getLoginErrorMessage(error);
      if (process.env.NODE_ENV === "development") {
        console.error("[Auth] Login failed:", message, error);
      }
      throw new Error(message);
    }
  },

  async me(): Promise<User> {
    const response = await http.get<User>("/auth/me/");
    return response.data;
  },

  async refresh(): Promise<string> {
    const refreshToken = TokenStore.getRefreshToken();
    if (!refreshToken) {
      throw new Error("No refresh token");
    }

    const response = await http.post<{ access: string }>("/auth/refresh/", {
      refresh: refreshToken,
    });

    const { access } = response.data;
    TokenStore.setTokens(access, refreshToken);
    return access;
  },

  // Note: logout is now handled by useLogout hook with router.replace
  // This is kept for backwards compatibility but not used
  logout(): void {
    TokenStore.clearTokens();
  },
};
