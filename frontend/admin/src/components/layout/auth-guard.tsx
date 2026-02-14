"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useMe } from "@/hooks/use-auth";
import { TokenStore } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

interface AuthGuardProps {
  children: React.ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { data: user, isLoading, isError } = useMe();
  const [isChecking, setIsChecking] = useState(true);
  const hasRedirected = useRef(false);

  useEffect(() => {
    // Prevent running on login page (should never happen, but safety check)
    if (pathname === "/login") {
      setIsChecking(false);
      return;
    }

    // Check if tokens exist
    const hasTokens = TokenStore.hasTokens();

    if (!hasTokens) {
      // No tokens - redirect to login once
      if (!hasRedirected.current) {
        hasRedirected.current = true;
        router.replace("/login");
      }
      return;
    }

    // If error fetching user (e.g., token expired and refresh failed)
    if (isError) {
      TokenStore.clearTokens();
      if (!hasRedirected.current) {
        hasRedirected.current = true;
        router.replace("/login");
      }
      return;
    }

    // Done checking if we have user data or finished loading
    if (!isLoading) {
      setIsChecking(false);
    }
  }, [isError, isLoading, router, pathname]);

  // Show loading skeleton while verifying
  if (isLoading || isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="space-y-4 w-full max-w-sm">
          <Skeleton className="h-8 w-48 mx-auto" />
          <Skeleton className="h-4 w-64 mx-auto" />
          <Skeleton className="h-4 w-56 mx-auto" />
        </div>
      </div>
    );
  }

  // Don't render children if no user and not loading
  if (!user) {
    return null;
  }

  return <>{children}</>;
}
