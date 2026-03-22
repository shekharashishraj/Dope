import { forwardRef } from "react";
import { cn } from "../../lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "destructive" | "warning" | "outline";
}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => (
    <span
      ref={ref}
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        variant === "default" && "bg-[var(--bg-2)] text-[var(--muted)]",
        variant === "success" && "bg-[var(--success)]/20 text-[var(--success)]",
        variant === "destructive" && "bg-[var(--danger)]/20 text-[var(--danger)]",
        variant === "warning" && "bg-[var(--warning)]/20 text-[var(--warning)]",
        variant === "outline" && "border border-[var(--card-border)]",
        className
      )}
      {...props}
    />
  )
);
Badge.displayName = "Badge";

export { Badge };
