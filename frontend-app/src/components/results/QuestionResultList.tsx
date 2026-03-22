import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { ListChecks } from "lucide-react";
import { useRunState } from "../../context/RunStateContext";
import { QuestionResultRow } from "./QuestionResultRow";

const DEFAULT_VISIBLE = 5;
const DEV_VISIBLE = 10;

type FilterOption = "all" | "detected" | "not_detected" | "refused";

export function QuestionResultList() {
  const { state } = useRunState();
  const [showAll, setShowAll] = useState(false);
  const [filter, setFilter] = useState<FilterOption>("all");

  const sampleResults = state.evaluationData?.sample_results ?? [];
  const devMode = state.devMode;
  const visibleDefault = devMode ? DEV_VISIBLE : DEFAULT_VISIBLE;

  const filtered = useMemo(() => {
    if (filter === "all") return sampleResults;
    return sampleResults.filter((r) => {
      if (filter === "detected") return r.detected === true;
      if (filter === "refused") return r.refused === true;
      if (filter === "not_detected")
        return r.detected !== true && r.refused !== true;
      return true;
    });
  }, [sampleResults, filter]);

  const visibleCount = showAll ? filtered.length : visibleDefault;
  const visible = filtered.slice(0, visibleCount);
  const hasMore = filtered.length > visibleDefault && !showAll;

  if (sampleResults.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <ListChecks className="h-4 w-4 text-[var(--muted)]" />
          <CardTitle className="text-base">Question-Level Results</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-[var(--muted)]">Filter:</span>
          {(
            [
              ["all", "All"],
              ["detected", "Detected"],
              ["not_detected", "Not detected"],
              ["refused", "Refused"],
            ] as const
          ).map(([value, label]) => (
            <Button
              key={value}
              variant={filter === value ? "secondary" : "ghost"}
              size="sm"
              className="h-7 text-xs"
              onClick={() => setFilter(value)}
            >
              {label}
            </Button>
          ))}
        </div>
        <ul className="space-y-1.5">
          {visible.map((r, i) => (
            <QuestionResultRow key={i} result={r} index={i} />
          ))}
        </ul>
        {hasMore && (
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-sm"
            onClick={() => setShowAll(true)}
          >
            Show all results ({filtered.length})
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
