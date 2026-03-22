import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { useRunState } from "../../context/RunStateContext";
import { STAGE_META } from "../../lib/pipelineStages";
import type { StepId } from "../../lib/types";
import { PipelineFlowStrip } from "./PipelineFlowStrip";
import { RunSummaryCard } from "./RunSummaryCard";
import { EmptyRunState } from "./EmptyRunState";
import { StageGrid } from "./StageGrid";
import { StageInspectorPanel } from "./StageInspectorPanel";

export function PipelineRunPage() {
  const { state, files } = useRunState();
  const [selectedStepId, setSelectedStepId] = useState<StepId | null>(null);

  const isIdle = state.status === "idle";
  const selectedStep = selectedStepId
    ? state.steps.find((s) => s.id === selectedStepId) ?? null
    : null;
  const selectedMeta = selectedStepId ? STAGE_META[selectedStepId] : null;

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Run</CardTitle>
          <p className="text-sm text-[var(--muted)]">
            Track each stage from ingestion to evaluation.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <PipelineFlowStrip steps={state.steps} />

          {isIdle ? (
            <EmptyRunState />
          ) : (
            <>
              <RunSummaryCard
                state={state}
                assessmentFileName={files.pdf?.name ?? undefined}
              />
              <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6 min-h-0">
                <div className="min-w-0">
                  <StageGrid
                    steps={state.steps}
                    selectedStepId={selectedStepId}
                    onSelectStep={setSelectedStepId}
                  />
                </div>
                <div className="min-w-0 flex flex-col lg:min-h-[400px]">
                  <StageInspectorPanel
                    selectedStep={selectedStep}
                    stageMeta={selectedMeta}
                    developerMode={state.devMode}
                  />
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
