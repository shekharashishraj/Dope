import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { useRunState } from "../../context/RunStateContext";

export function RunSummaryCard() {
  const { state } = useRunState();

  const runtime =
    state.runStartedAt != null && state.status === "done"
      ? ((Date.now() - state.runStartedAt) / 1000).toFixed(1)
      : null;

  const extractStep = state.steps.find((s) => s.id === "extract");
  const planStep = state.steps.find((s) => s.id === "plan");

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pipeline Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-[var(--muted)]">Questions extracted</span>
          <span>{extractStep?.outputs?.find((o) => o.label === "Questions")?.value ?? "--"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--muted)]">Perturbations</span>
          <span>{planStep?.summary ?? "--"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--muted)]">Shielding method(s) used</span>
          <span>{state.config.attacks.length ? state.config.attacks.join(", ") : "--"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--muted)]">PDF compilation</span>
          <span>Enabled</span>
        </div>
        {runtime != null && (
          <div className="flex justify-between">
            <span className="text-[var(--muted)]">Total runtime</span>
            <span>{runtime}s</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
