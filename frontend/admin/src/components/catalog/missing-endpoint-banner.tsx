"use client";

import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface MissingEndpointBannerProps {
  endpoint: string;
  description?: string;
  className?: string;
}

export function MissingEndpointBanner({
  endpoint,
  description,
  className,
}: MissingEndpointBannerProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 p-4 rounded-lg border border-amber-200 bg-amber-50",
        className
      )}
    >
      <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
      <div>
        <p className="text-sm font-medium text-amber-800">
          Admin API gerekli
        </p>
        <p className="text-sm text-amber-700 mt-1">
          Missing endpoint: <code className="bg-amber-100 px-1 rounded">{endpoint}</code>
        </p>
        {description && (
          <p className="text-sm text-amber-600 mt-1">{description}</p>
        )}
      </div>
    </div>
  );
}
