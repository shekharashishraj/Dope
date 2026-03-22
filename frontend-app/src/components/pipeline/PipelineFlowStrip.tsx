import { ChevronRight } from "lucide-react";
import { cn } from "../../lib/utils";
import { STEP_ORDER } from "../../lib/types";
import { STAGE_META, STAGE_SHORT_LABELS } from "../../lib/pipelineStages";
import type { RunState } from "../../lib/types";

interface PipelineFlowStripProps {
  steps: RunState["steps"];
}

function getCurrentStepId(steps: RunState["steps"]): string | null {
  const running = steps.find((s) => s.status === "running");
  if (running) return running.id;
  const lastDone = [...steps].reverse().find((s) => s.status === "done");
  return lastDone?.id ?? null;
}

export function PipelineFlowStrip({ steps }: PipelineFlowStripProps) {
  const currentStepId = getCurrentStepId(steps);

  return (
    <div
      className="flex flex-wrap items-center gap-1 py-3 px-4 rounded-lg bg-[var(--bg-2)] border border-[var(--card-border)]"
      aria-label="Pipeline progress"
    >
      {STEP_ORDER.map((id, index) => {
        const step = steps.find((s) => s.id === id);
        const meta = STAGE_META[id];
        const status = step?.status ?? "queued";
        const isCurrent = currentStepId === id;
        const isDone = status === "done";
        const isRunning = status === "running";
        const isFailed = status === "failed";

        return (
          <div key={id} className="flex items-center gap-1">
            {index > 0 && (
              <ChevronRight
                className="h-4 w-4 text-[var(--muted)] shrink-0"
                aria-hidden
              />
            )}
            <div
              className={cn(
                "flex items-center gap-2 rounded-md px-2 py-1.5 text-sm",
                isDone && "text-[var(--success)]",
                isRunning && "text-[var(--accent-2)]",
                isFailed && "text-[var(--danger)]",
                status === "queued" && "text-[var(--muted)]",
                isCurrent && isRunning && "ring-1 ring-[var(--accent-2)]/50"
              )}
            >
              <meta.Icon className="h-4 w-4 shrink-0" aria-hidden />
              <span>{STAGE_SHORT_LABELS[id]}</span>
              {isRunning && (
                <span
                  className="h-1.5 w-1.5 rounded-full bg-current animate-pulse"
                  aria-hidden
                />
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
