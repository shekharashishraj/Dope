import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import type { RunState } from "../../lib/types";

interface RunSummaryCardProps {
  state: RunState;
  assessmentFileName?: string | null;
}

function formatRunStatus(status: RunState["status"]): string {
  switch (status) {
    case "idle":
      return "Queued";
    case "running":
      return "Running";
    case "done":
      return "Completed";
    case "failed":
      return "Failed";
    default:
      return status;
  }
}

function getCurrentStageTitle(steps: RunState["steps"]): string | null {
  const running = steps.find((s) => s.status === "running");
  if (running) return running.title;
  const lastDone = [...steps].reverse().find((s) => s.status === "done");
  return lastDone?.title ?? null;
}

function formatStartedAt(ts?: number): string {
  if (ts == null) return "—";
  const d = new Date(ts);
  return d.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function RunSummaryCard({ state, assessmentFileName }: RunSummaryCardProps) {
  const currentStage = getCurrentStageTitle(state.steps);
  const methodLabel =
    state.config.attacks.length > 0
      ? state.config.attacks.join(", ")
      : "—";

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Run Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-[var(--muted)]">Status</dt>
            <dd className="font-medium">{formatRunStatus(state.status)}</dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Method</dt>
            <dd className="font-medium truncate" title={methodLabel}>
              {methodLabel}
            </dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Current stage</dt>
            <dd className="font-medium truncate" title={currentStage ?? undefined}>
              {currentStage ?? "—"}
            </dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Assessment</dt>
            <dd className="font-medium truncate" title={assessmentFileName ?? undefined}>
              {assessmentFileName ?? "—"}
            </dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Started</dt>
            <dd className="font-medium">{formatStartedAt(state.runStartedAt)}</dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}
