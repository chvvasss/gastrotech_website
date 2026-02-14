import { InboxIcon } from "lucide-react";

interface EmptyStateProps {
  message?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export function EmptyState({
  message = "Veri bulunamadı",
  description,
  icon,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex min-h-[300px] flex-col items-center justify-center gap-4 p-8 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-stone-100">
        {icon || <InboxIcon className="h-8 w-8 text-stone-400" />}
      </div>
      <div className="space-y-1">
        <p className="text-lg font-medium text-stone-900">{message}</p>
        {description && (
          <p className="text-sm text-stone-500">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
}
