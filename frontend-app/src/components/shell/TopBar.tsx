import { Bug, Play } from "lucide-react";
import { Button } from "../ui/button";
import { Switch } from "../ui/switch";
import { useRunState } from "../../context/RunStateContext";
import { useTab } from "../../context/TabContext";
import { cn } from "../../lib/utils";

const statusVariant = {
  idle: "bg-[var(--bg-2)] text-[var(--muted)]",
  running: "bg-blue-500/20 text-blue-300",
  done: "bg-[var(--success)]/20 text-[var(--success)]",
  failed: "bg-[var(--danger)]/20 text-[var(--danger)]",
};

export function TopBar({
  onOpenDeveloper,
}: {
  onOpenDeveloper: () => void;
}) {
  const { state, setDevMode } = useRunState();
  const { activeTab, setActiveTab } = useTab();

  const tabClass = cn(
    "px-3 py-1.5 rounded-md text-sm font-medium uppercase transition-colors"
  );
  const activeClass = "bg-[var(--accent)]/20 text-[var(--accent)]";
  const inactiveClass = "text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--card)]/50";

  return (
    <header className="sticky top-0 z-50 flex items-center justify-between px-6 py-4 border-b border-[var(--card-border)] bg-[var(--bg-2)]">
      <div className="flex flex-1 items-center gap-4 justify-start min-w-0">
        <div className="flex shrink-0">
          <img src="/IGShield_Logo.png" alt="IntegrityShield" className="h-14 w-14 sm:h-16 sm:w-16 object-contain" />
        </div>
        <div>
          <div className="font-semibold text-2xl sm:text-3xl tracking-tight">IntegrityShield</div>
        </div>
      </div>

      <nav className="flex flex-1 items-center justify-center gap-20" aria-label="Main navigation">
        <button
          type="button"
          onClick={() => setActiveTab("main")}
          className={cn(tabClass, activeTab === "main" ? activeClass : inactiveClass)}
        >
          Main
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("pipeline")}
          className={cn(tabClass, activeTab === "pipeline" ? activeClass : inactiveClass)}
        >
          Pipeline Run
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("results")}
          className={cn(tabClass, activeTab === "results" ? activeClass : inactiveClass)}
        >
          Results
        </button>
      </nav>

      <div className="flex flex-1 items-center justify-end gap-4 min-w-0">
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium",
            statusVariant[state.status]
          )}
        >
          {state.status === "running" && <Play className="h-3 w-3 animate-pulse" />}
          {state.status === "done"
            ? "Completed"
            : state.status === "failed"
              ? "Error"
              : state.status.charAt(0).toUpperCase() + state.status.slice(1)}
        </span>

        <div className="flex items-center gap-2">
          <span className="text-xs text-[var(--muted)]">Developer Mode</span>
          <Switch
            checked={state.devMode}
            onCheckedChange={setDevMode}
            aria-label="Toggle developer mode"
          />
        </div>

        {state.devMode && (
          <Button variant="secondary" size="sm" onClick={onOpenDeveloper}>
            <Bug className="h-4 w-4" />
            Developer
          </Button>
        )}
      </div>
    </header>
  );
}
