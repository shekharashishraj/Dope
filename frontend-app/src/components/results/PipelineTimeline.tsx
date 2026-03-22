import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Check, X, Circle, Loader2, Clock3 } from "lucide-react";
import { useRunState } from "../../context/RunStateContext";
import { STEP_ORDER, type StepStatus } from "../../lib/types";

function StatusIcon({ status }: { status: StepStatus }) {
  if (status === "done")
    return <Check className="h-4 w-4 text-[var(--success)] shrink-0" />;
  if (status === "failed")
    return <X className="h-4 w-4 text-[var(--danger)] shrink-0" />;
  if (status === "running")
    return (
      <Loader2 className="h-4 w-4 text-[var(--muted)] shrink-0 animate-spin" />
    );
  return <Circle className="h-4 w-4 text-[var(--muted)] shrink-0 opacity-50" />;
}

function stepLabel(step: { id: string; title: string; status: StepStatus }) {
  if (step.status === "done") return `${step.title} complete`;
  if (step.status === "failed") return `${step.title} failed`;
  return step.title;
}

export function PipelineTimeline() {
  const { state } = useRunState();
  const steps = STEP_ORDER.map(
    (id) => state.steps.find((s) => s.id === id)!
  ).filter(Boolean);

  if (steps.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Clock3 className="h-4 w-4 text-[var(--muted)]" />
          <CardTitle className="text-base">Pipeline Timeline</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {steps.map((step) => (
            <li
              key={step.id}
              className="flex items-center gap-3 text-sm"
            >
              <StatusIcon status={step.status} />
              <span
                className={
                  step.status === "done"
                    ? "text-[var(--text)]"
                    : step.status === "failed"
                      ? "text-[var(--danger)]"
                      : "text-[var(--muted)]"
                }
              >
                {stepLabel(step)}
              </span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
