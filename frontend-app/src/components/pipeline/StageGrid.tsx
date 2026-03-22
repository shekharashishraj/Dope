import { STEP_ORDER } from "../../lib/types";
import { STAGE_META } from "../../lib/pipelineStages";
import type { RunState } from "../../lib/types";
import type { StepId } from "../../lib/types";
import { PipelineStageCard } from "./PipelineStageCard";

interface StageGridProps {
  steps: RunState["steps"];
  selectedStepId: StepId | null;
  onSelectStep: (id: StepId | null) => void;
}

export function StageGrid({
  steps,
  selectedStepId,
  onSelectStep,
}: StageGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {STEP_ORDER.map((id) => {
        const step = steps.find((s) => s.id === id);
        const meta = STAGE_META[id];
        if (!step || !meta) return null;
        return (
          <PipelineStageCard
            key={step.id}
            step={step}
            stageMeta={meta}
            isSelected={selectedStepId === step.id}
            onClick={() =>
              onSelectStep(selectedStepId === step.id ? null : step.id)
            }
          />
        );
      })}
    </div>
  );
}
