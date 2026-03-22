import { ScrollArea } from "../ui/scroll-area";
import { StatusBadge } from "./StatusBadge";
import type { RunState } from "../../lib/types";
import type { StageMeta } from "../../lib/pipelineStages";

interface StageInspectorPanelProps {
  selectedStep: RunState["steps"][number] | null;
  stageMeta: StageMeta | null;
  developerMode: boolean;
}

export function StageInspectorPanel({
  selectedStep,
  stageMeta,
  developerMode,
}: StageInspectorPanelProps) {
  if (!selectedStep || !stageMeta) {
    return (
      <div className="h-full min-h-[200px] flex items-center justify-center rounded-lg border border-[var(--card-border)] bg-[var(--bg-2)] p-6">
        <p className="text-sm text-[var(--muted)] text-center">
          Select a stage to view details.
        </p>
      </div>
    );
  }

  const { overview, inputs, outputs, Icon } = stageMeta;

  return (
    <ScrollArea className="h-full min-h-0 rounded-lg border border-[var(--card-border)] bg-[var(--card)]">
      <div className="p-4 space-y-4">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--bg-2)] text-[var(--muted)]">
            <Icon className="h-5 w-5" aria-hidden />
          </div>
          <div>
            <h3 className="font-medium text-sm">{selectedStep.title}</h3>
            <StatusBadge status={selectedStep.status} className="mt-0.5" />
          </div>
        </div>

        <div>
          <h4 className="text-xs font-medium text-[var(--muted)] mb-1">
            Overview
          </h4>
          <p className="text-sm">{overview}</p>
        </div>

        {inputs.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-[var(--muted)] mb-1">
              Inputs
            </h4>
            <ul className="text-sm list-disc pl-4 space-y-0.5">
              {inputs.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        )}

        {outputs.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-[var(--muted)] mb-1">
              Outputs
            </h4>
            <ul className="text-sm list-disc pl-4 space-y-0.5">
              {outputs.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        )}

        {selectedStep.summary && (
          <div>
            <h4 className="text-xs font-medium text-[var(--muted)] mb-1">
              Summary
            </h4>
            <p className="text-sm">{selectedStep.summary}</p>
          </div>
        )}

        {selectedStep.outputs && selectedStep.outputs.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-[var(--muted)] mb-1">
              Stage outputs
            </h4>
            <ul className="text-sm space-y-1">
              {selectedStep.outputs.map((o, i) => (
                <li key={i}>
                  <span className="text-[var(--muted)]">{o.label}:</span>{" "}
                  <span className="truncate block" title={o.value}>
                    {o.value}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {selectedStep.durationSec != null && (
          <div>
            <h4 className="text-xs font-medium text-[var(--muted)] mb-1">
              Duration
            </h4>
            <p className="text-sm">{selectedStep.durationSec.toFixed(1)}s</p>
          </div>
        )}

        {selectedStep.warnings && selectedStep.warnings.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-[var(--warning)] mb-1">
              Warnings
            </h4>
            <ul className="text-sm list-disc pl-4 space-y-0.5">
              {selectedStep.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        )}

        {developerMode && selectedStep.raw != null && (
          <div>
            <h4 className="text-xs font-medium text-[var(--muted)] mb-1">
              Raw JSON
            </h4>
            <ScrollArea className="h-48 rounded border border-[var(--card-border)] p-2 font-mono text-xs bg-[var(--bg-2)]">
              <pre className="whitespace-pre-wrap text-[var(--muted)]">
                {JSON.stringify(selectedStep.raw, null, 2)}
              </pre>
            </ScrollArea>
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
