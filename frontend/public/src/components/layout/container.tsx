import { cn } from "@/lib/utils";

interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function Container({ children, className, ...props }: ContainerProps) {
  return (
    <div
      className={cn(
        "mx-auto w-full max-w-7xl",
        // Responsive padding: 16px on tiny screens, scaling up
        "px-4 sm:px-6 lg:px-8",
        // Safer max-width constraint
        "2xl:max-w-screen-2xl",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
