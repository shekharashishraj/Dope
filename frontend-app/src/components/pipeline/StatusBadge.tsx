import { Check, AlertCircle } from "lucide-react";
import { cn } from "../../lib/utils";
import type { StepStatus } from "../../lib/types";

interface StatusBadgeProps {
  status: StepStatus;
  className?: string;
}

const label: Record<StepStatus, string> = {
  queued: "Queued",
  running: "Running",
  done: "Completed",
  failed: "Failed",
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        status === "queued" && "bg-[var(--bg-2)] text-[var(--muted)]",
        status === "running" &&
          "bg-[var(--accent-2)]/20 text-[var(--accent-2)] border border-[var(--accent-2)]/40",
        status === "done" && "bg-[var(--success)]/20 text-[var(--success)]",
        status === "failed" && "bg-[var(--danger)]/20 text-[var(--danger)]",
        className
      )}
      aria-label={`Status: ${label[status]}`}
    >
      {status === "running" && (
        <span
          className="h-1.5 w-1.5 rounded-full bg-current animate-pulse"
          aria-hidden
        />
      )}
      {status === "done" && <Check className="h-3 w-3 shrink-0" aria-hidden />}
      {status === "failed" && (
        <AlertCircle className="h-3 w-3 shrink-0" aria-hidden />
      )}
      {label[status]}
    </span>
  );
}
