import { ChevronDown } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { cn } from "../../lib/utils";
import { StatusBadge } from "./StatusBadge";
import type { RunState } from "../../lib/types";
import type { StageMeta } from "../../lib/pipelineStages";

interface PipelineStageCardProps {
  step: RunState["steps"][number];
  stageMeta: StageMeta;
  isSelected: boolean;
  onClick: () => void;
}

export function PipelineStageCard({
  step,
  stageMeta,
  isSelected,
  onClick,
}: PipelineStageCardProps) {
  const { Icon, description } = stageMeta;

  return (
    <Card
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
      className={cn(
        "cursor-pointer transition-all hover:shadow-md hover:border-[var(--accent)]/30",
        isSelected && "ring-2 ring-[var(--accent)]/50 border-[var(--accent)]/30"
      )}
      aria-pressed={isSelected}
      aria-label={`${step.title}, ${step.status}. Click to view details.`}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex gap-3 min-w-0 flex-1">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--bg-2)] text-[var(--muted)]">
              <Icon className="h-5 w-5" aria-hidden />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-medium text-sm truncate">{step.title}</h3>
                <StatusBadge status={step.status} />
              </div>
              <p className="text-xs text-[var(--muted)] mt-1 line-clamp-2">
                {description}
              </p>
            </div>
          </div>
          <ChevronDown
            className={cn(
              "h-4 w-4 shrink-0 text-[var(--muted)] transition-transform",
              isSelected && "rotate-180"
            )}
            aria-hidden
          />
        </div>
        {(step.progress != null || step.durationSec != null) && (
          <div className="flex gap-3 mt-2 text-xs text-[var(--muted)]">
            {step.progress != null && (
              <span>
                {step.progress.current}/{step.progress.total}
              </span>
            )}
            {step.durationSec != null && (
              <span>{step.durationSec.toFixed(1)}s</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
