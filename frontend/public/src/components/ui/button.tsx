import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  // Base styles with premium transitions
  [
    "inline-flex items-center justify-center gap-2 whitespace-nowrap",
    "rounded-sm text-sm font-semibold",
    // Premium transition with cubic-bezier for smooth feel
    "transition-all duration-200 ease-in-out",
    // Focus styles
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
    // Disabled styles
    "disabled:pointer-events-none disabled:opacity-50",
    // Icon sizing
    "[&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  ].join(" "),
  {
    variants: {
      variant: {
        // Primary: Gradient background with glow on hover
        default: [
          "bg-primary text-primary-foreground",
          "shadow-md shadow-primary/20",
          "hover:shadow-lg hover:shadow-primary/30",
          "hover:bg-primary/90",
          "active:scale-[0.98] active:shadow-sm",
        ].join(" "),
        
        // Premium: Gradient with stronger glow
        premium: [
          "gradient-primary text-primary-foreground",
          "shadow-lg shadow-primary/25",
          "hover:shadow-xl hover:shadow-primary/35",
          "hover:gradient-primary-hover",
          "active:scale-[0.98]",
        ].join(" "),
        
        // Destructive
        destructive: [
          "bg-destructive text-destructive-foreground",
          "shadow-sm shadow-destructive/20",
          "hover:bg-destructive/90 hover:shadow-md",
          "active:scale-[0.98]",
        ].join(" "),
        
        // Outline: Border with subtle hover lift
        outline: [
          "border-2 border-input bg-background",
          "shadow-sm",
          "hover:border-primary/50 hover:bg-primary/5",
          "hover:shadow-md hover:text-primary",
          "active:scale-[0.98]",
        ].join(" "),
        
        // Secondary
        secondary: [
          "bg-secondary text-secondary-foreground",
          "shadow-sm",
          "hover:bg-secondary/80 hover:shadow-md",
          "active:scale-[0.98]",
        ].join(" "),
        
        // Ghost: Minimal with subtle background on hover
        ghost: [
          "hover:bg-accent hover:text-accent-foreground",
          "active:bg-accent/80",
        ].join(" "),
        
        // Link style
        link: [
          "text-primary underline-offset-4",
          "hover:underline",
        ].join(" "),
        
        // Glass: For use on images/dark backgrounds
        glass: [
          "bg-white/80 backdrop-blur-sm border border-white/20 text-foreground shadow-sm",
          "hover:bg-white/90",
          "active:scale-[0.98]",
        ].join(" "),
      },
      size: {
        default: "h-10 px-5 py-2",
        sm: "h-9 rounded-sm px-4 text-xs",
        lg: "h-11 rounded-sm px-8",
        xl: "h-12 rounded-sm px-10 text-base",
        icon: "h-10 w-10 rounded-sm",
        "icon-sm": "h-8 w-8 rounded-sm",
        "icon-lg": "h-12 w-12 rounded-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  isLoading?: boolean;
  loadingText?: string;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    className, 
    variant, 
    size, 
    asChild = false, 
    isLoading = false,
    loadingText,
    children,
    disabled,
    ...props 
  }, ref) => {
    const Comp = asChild ? Slot : "button";
    
    // If loading, render button content with spinner
    if (isLoading && !asChild) {
      return (
        <button
          className={cn(buttonVariants({ variant, size, className }))}
          ref={ref}
          disabled={true}
          {...props}
        >
          <Loader2 className="h-4 w-4 animate-spin" />
          {loadingText || children}
        </button>
      );
    }
    
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {children}
      </Comp>
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
