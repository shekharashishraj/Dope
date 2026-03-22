import { AppShell } from "../components/shell/AppShell";
import { MainTabContent } from "../components/main/MainTabContent";
import { PipelineRunPage } from "../components/pipeline/PipelineRunPage";
import { ResultsPanel } from "../components/results/ResultsPanel";

export function Dashboard() {
  return (
    <AppShell
      mainContent={<MainTabContent />}
      pipelineContent={<PipelineRunPage />}
      resultsContent={<ResultsPanel />}
    />
  );
}
