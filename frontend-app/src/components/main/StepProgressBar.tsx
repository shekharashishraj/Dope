import { useTab } from "../../context/TabContext";
import { cn } from "../../lib/utils";

const STEPS = [
  { id: "upload" as const, label: "Upload", tab: "main" as const },
  { id: "configure" as const, label: "Configure", tab: "main" as const },
  { id: "run" as const, label: "Run", tab: "pipeline" as const },
  { id: "results" as const, label: "Results", tab: "results" as const },
] as const;

export function StepProgressBar() {
  const { activeTab, setActiveTab } = useTab();

  const activeStepIndex =
    activeTab === "main" ? 1 : activeTab === "pipeline" ? 2 : 3;

  return (
    <nav aria-label="Workflow steps" className="w-full">
      <ol className="flex items-center justify-between gap-2">
        {STEPS.map((step, index) => {
          const isActive = activeStepIndex === index;
          const tabForStep = step.tab;
          return (
            <li key={step.id} className="flex flex-1 items-center">
              <button
                type="button"
                onClick={() => setActiveTab(tabForStep)}
                className={cn(
                  "flex flex-1 flex-col items-center gap-1 rounded-lg px-2 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-[var(--accent)]/15 text-[var(--accent)]"
                    : "text-[var(--muted)] hover:bg-[var(--card)]/50 hover:text-[var(--text)]"
                )}
              >
                <span
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs",
                    isActive
                      ? "bg-[var(--accent)]/25 text-[var(--accent)]"
                      : "bg-[var(--bg-2)] text-[var(--muted)]"
                  )}
                >
                  {index + 1}
                </span>
                {step.label}
              </button>
              {index < STEPS.length - 1 && (
                <div
                  className={cn(
                    "h-0.5 flex-1 max-w-[24px] rounded",
                    activeStepIndex > index ? "bg-[var(--accent)]/40" : "bg-[var(--card-border)]"
                  )}
                  aria-hidden
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
