import { Slot } from "@radix-ui/react-slot";
import { forwardRef } from "react";
import { cn } from "../../lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "ghost" | "outline";
  size?: "default" | "sm";
  asChild?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] disabled:pointer-events-none disabled:opacity-50",
          size === "default" && "px-4 py-2",
          size === "sm" && "h-8 px-3",
          variant === "default" &&
            "bg-[var(--accent)] text-[#0d0f1a] hover:opacity-90",
          variant === "secondary" &&
            "bg-[var(--bg-2)] text-[var(--text)] hover:bg-[var(--card)]",
          variant === "outline" &&
            "border border-[var(--card-border)] bg-transparent hover:bg-[var(--card)]",
          variant === "ghost" && "hover:bg-[var(--card)]",
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
