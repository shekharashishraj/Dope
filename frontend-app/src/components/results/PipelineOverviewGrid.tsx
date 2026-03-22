import { LayoutDashboard } from "lucide-react";
import { useRunState } from "../../context/RunStateContext";
import { ResultMetricCard } from "./ResultMetricCard";

export function PipelineOverviewGrid() {
  const { state } = useRunState();

  const extractStep = state.steps.find((s) => s.id === "extract");
  const planStep = state.steps.find((s) => s.id === "plan");

  const questionsValue =
    extractStep?.outputs?.find((o) => o.label === "Questions")?.value ?? "--";

  const rawPlan = planStep?.raw as { stats?: { perturbations?: number } } | undefined;
  let perturbationsValue: string;
  if (
    rawPlan?.stats?.perturbations != null &&
    typeof rawPlan.stats.perturbations === "number"
  ) {
    perturbationsValue = String(rawPlan.stats.perturbations);
  } else {
    const summary = planStep?.summary ?? "";
    const match = summary.match(/(\d+)\s*perturbation/i);
    perturbationsValue = match ? match[1] : "--";
  }
  const shieldingMethod =
    state.config.attacks.length > 0
      ? state.config.attacks.join(", ")
      : "--";
  const pdfCompilation = state.config.compile ? "Enabled" : "Disabled";
  const runtime =
    state.runStartedAt != null && state.status === "done"
      ? `${((Date.now() - state.runStartedAt) / 1000).toFixed(1)}s`
      : null;
  const pdfArtifacts = state.artifacts.filter((a) => a.type === "pdf");
  const generatedVariants = pdfArtifacts.length;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <LayoutDashboard className="h-4 w-4 text-[var(--muted)]" />
        <h2 className="text-sm font-semibold">Pipeline Overview</h2>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <ResultMetricCard label="Questions Extracted" value={questionsValue} />
        <ResultMetricCard label="Perturbations" value={perturbationsValue} />
        <ResultMetricCard label="Shielding Method" value={shieldingMethod} />
        <ResultMetricCard label="PDF Compilation" value={pdfCompilation} />
        {runtime != null && (
          <ResultMetricCard label="Runtime" value={runtime} />
        )}
        <ResultMetricCard label="Generated Variants" value={generatedVariants} />
      </div>
    </div>
  );
}
