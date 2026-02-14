import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
  sticky?: boolean;
}

export function PageHeader({
  title,
  description,
  actions,
  className,
  sticky = false,
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-1 pb-6 sm:flex-row sm:items-center sm:justify-between",
        sticky && "sticky top-14 z-10 bg-stone-50 -mx-6 px-6 py-4 border-b border-stone-200 mb-6",
        className
      )}
    >
      <div className="min-w-0">
        <h1 className="text-h1 text-stone-900 truncate">{title}</h1>
        {description && (
          <p className="text-body text-stone-500 mt-1">{description}</p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2 mt-3 sm:mt-0 shrink-0">
          {actions}
        </div>
      )}
    </div>
  );
}
