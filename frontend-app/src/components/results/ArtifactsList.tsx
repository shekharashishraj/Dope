import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Files } from "lucide-react";
import { useRunState } from "../../context/RunStateContext";
import { STEP_TITLES, type StepId } from "../../lib/types";
import { ArtifactRow } from "./ArtifactRow";

export function ArtifactsList() {
  const { state } = useRunState();

  const byStage = state.artifacts.reduce<Record<StepId, typeof state.artifacts>>(
    (acc, a) => {
      if (!acc[a.stageId]) acc[a.stageId] = [];
      acc[a.stageId].push(a);
      return acc;
    },
    {} as Record<StepId, typeof state.artifacts>
  );

  const stages = (["extract", "plan", "inject", "compile", "eval"] as StepId[]).filter(
    (id) => (byStage[id]?.length ?? 0) > 0
  );

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Files className="h-4 w-4 text-[var(--muted)]" />
          <CardTitle className="text-base">Generated Artifacts</CardTitle>
        </div>
        <p className="text-sm text-[var(--muted)] mt-0.5">
          Generated files by stage.
        </p>
      </CardHeader>
      <CardContent>
        {state.status === "running" && stages.length === 0 ? (
          <div className="space-y-2 animate-pulse">
            <div className="h-4 w-3/4 rounded bg-[var(--card-border)]" />
            <div className="h-4 w-1/2 rounded bg-[var(--card-border)]" />
            <div className="h-4 w-2/3 rounded bg-[var(--card-border)]" />
          </div>
        ) : stages.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">No artifacts yet.</p>
        ) : (
          <div className="space-y-4">
            {stages.map((stageId) => (
              <div key={stageId}>
                <div className="text-xs font-medium text-[var(--muted)] uppercase tracking-wider mb-2">
                  {STEP_TITLES[stageId]}
                </div>
                <ul className="space-y-1.5">
                  {(byStage[stageId] ?? []).map((a, i) => (
                    <ArtifactRow
                      key={`${a.stageId}-${a.name}-${i}`}
                      artifact={a}
                      runId={state.runId}
                    />
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
