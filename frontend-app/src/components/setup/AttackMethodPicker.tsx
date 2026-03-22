import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../ui/tooltip";
import { Info } from "lucide-react";
import { useRunState } from "../../context/RunStateContext";
import { cn } from "../../lib/utils";

const METHODS: Array<{
  id: string;
  title: string;
  description: string;
  tooltip: string;
  recommended?: boolean;
}> = [
  {
    id: "icw",
    title: "ICW",
    description: "In-context watermark perturbation.",
    tooltip: "Applies in-context watermarking style changes to question text.",
    recommended: false,
  },
  {
    id: "dual_layer",
    title: "Dual Layer",
    description: "Overlay and hidden-layer protection.",
    tooltip: "Recommended. Combines overlay and LaTeX layer for robust protection.",
    recommended: true,
  },
  {
    id: "font_attack",
    title: "Font Attack",
    description: "Glyph and font-level perturbation.",
    tooltip: "Modifies fonts and glyphs for document protection.",
    recommended: false,
  },
  {
    id: "icw_dual_layer",
    title: "ICW + Dual Layer",
    description: "Combined contextual and layered shielding.",
    tooltip: "Combines ICW with dual-layer for stronger shielding.",
    recommended: false,
  },
  {
    id: "icw_font_attack",
    title: "ICW + Font",
    description: "Combined contextual and font-based shielding.",
    tooltip: "ICW with font-level perturbations.",
    recommended: false,
  },
];

export function AttackMethodPicker() {
  const { state, setConfig } = useRunState();
  const selected = new Set(state.config.attacks);

  const toggle = (id: string) => {
    const next = selected.has(id)
      ? state.config.attacks.filter((a) => a !== id)
      : [...state.config.attacks, id];
    if (next.length === 0) return;
    setConfig({ attacks: next });
  };

  return (
    <TooltipProvider>
      <div className="grid gap-2">
          {METHODS.map((m) => (
            <Card
              key={m.id}
              className={cn(
                "cursor-pointer transition-colors hover:border-[var(--accent)]/50",
                selected.has(m.id) && "border-[var(--accent)] bg-[var(--accent)]/10 ring-1 ring-[var(--accent)]/30"
              )}
              onClick={() => toggle(m.id)}
            >
              <CardContent className="p-3 flex items-start gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{m.title}</span>
                    {m.recommended && (
                      <Badge variant="outline" className="text-xs">
                        Recommended
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-[var(--muted)] mt-0.5">{m.description}</p>
                </div>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      className="shrink-0 p-1 rounded hover:bg-[var(--card)] text-[var(--muted)]"
                      onClick={(e) => e.stopPropagation()}
                      aria-label="Learn more"
                    >
                      <Info className="h-4 w-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>{m.tooltip}</TooltipContent>
                </Tooltip>
              </CardContent>
            </Card>
          ))}
      </div>
    </TooltipProvider>
  );
}
