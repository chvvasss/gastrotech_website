import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  trend?: "up" | "down" | {
    value: number;
    positive: boolean;
  };
  loading?: boolean;
  className?: string;
  href?: string;
  onClick?: () => void;
}

export function StatCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  loading,
  className,
  onClick,
}: StatCardProps) {
  if (loading) {
    return (
      <Card className={cn("border-stone-200", className)}>
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-9 w-9 rounded-lg" />
          </div>
          <Skeleton className="mt-3 h-7 w-20" />
          <Skeleton className="mt-2 h-3 w-32" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card 
      className={cn(
        "border-stone-200 bg-white card-premium",
        onClick && "cursor-pointer hover:border-stone-300",
        className
      )}
      onClick={onClick}
    >
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <p className="text-label text-stone-500">{title}</p>
          {Icon && (
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Icon className="h-[1.125rem] w-[1.125rem]" />
            </div>
          )}
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <p className="text-h2 text-stone-900">{value}</p>
          {trend && (
            typeof trend === "string" ? (
              <span className={cn(
                "text-tiny font-medium px-1.5 py-0.5 rounded",
                trend === "up" ? "text-green-700 bg-green-50" : "text-red-700 bg-red-50"
              )}>
                {trend === "up" ? "↑" : "↓"}
              </span>
            ) : (
              <span
                className={cn(
                  "text-tiny font-medium px-1.5 py-0.5 rounded",
                  trend.positive ? "text-green-700 bg-green-50" : "text-red-700 bg-red-50"
                )}
              >
                {trend.positive ? "+" : "-"}
                {Math.abs(trend.value)}%
              </span>
            )
          )}
        </div>
        {description && (
          <p className="mt-1.5 text-small text-stone-500">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}
