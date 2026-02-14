"use client";

import { Badge } from "@/components/ui/badge";
import type { ProductStatus } from "@/types/api";

const statusConfig: Record<ProductStatus, { label: string; variant: "success" | "secondary" | "outline" }> = {
  active: { label: "Aktif", variant: "success" },
  draft: { label: "Taslak", variant: "secondary" },
  archived: { label: "Arşiv", variant: "outline" },
};

interface BadgeStatusProps {
  status: ProductStatus;
  className?: string;
}

export function BadgeStatus({ status, className }: BadgeStatusProps) {
  const config = statusConfig[status] || { label: status, variant: "outline" as const };
  return (
    <Badge variant={config.variant} className={className}>
      {config.label}
    </Badge>
  );
}
