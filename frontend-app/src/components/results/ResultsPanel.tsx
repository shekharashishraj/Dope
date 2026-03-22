import { ResultComparisonPanel } from "./ResultComparisonPanel";
import { PipelineOverviewGrid } from "./PipelineOverviewGrid";
import { EvaluationSummaryCard } from "./EvaluationSummaryCard";
import { EvaluationSubsections } from "./EvaluationSubsections";
import { QuestionResultList } from "./QuestionResultList";
import { ArtifactsList } from "./ArtifactsList";

export function ResultsPanel() {
  return (
    <div className="space-y-6">
      <ResultComparisonPanel />
      <PipelineOverviewGrid />
      <EvaluationSummaryCard />
      <EvaluationSubsections />
      <QuestionResultList />
      <ArtifactsList />
    </div>
  );
}
