import { useState } from "react";
import { TopBar } from "./TopBar";
import { DeveloperDrawer } from "../dev/DeveloperDrawer";
import { TabProvider, useTab } from "../../context/TabContext";

interface AppShellProps {
  mainContent: React.ReactNode;
  pipelineContent: React.ReactNode;
  resultsContent: React.ReactNode;
}

function AppShellContent({ mainContent, pipelineContent, resultsContent }: AppShellProps) {
  const [developerOpen, setDeveloperOpen] = useState(false);
  const { activeTab } = useTab();

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg)]">
      <TopBar onOpenDeveloper={() => setDeveloperOpen(true)} />

      <main className="flex-1 p-4 w-full mx-auto">
        {activeTab === "main" && <div className="flex flex-col gap-6 max-w-[1200px] mx-auto w-full">{mainContent}</div>}
        {activeTab === "pipeline" && <div className="flex flex-col gap-4 max-w-6xl mx-auto w-full">{pipelineContent}</div>}
        {activeTab === "results" && <div className="max-w-4xl mx-auto w-full">{resultsContent}</div>}
      </main>

      <DeveloperDrawer open={developerOpen} onOpenChange={setDeveloperOpen} />
    </div>
  );
}

export function AppShell(props: AppShellProps) {
  return (
    <TabProvider>
      <AppShellContent {...props} />
    </TabProvider>
  );
}
