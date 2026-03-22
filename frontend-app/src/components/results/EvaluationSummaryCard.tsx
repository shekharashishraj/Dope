import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { BarChart3 } from "lucide-react";
import { useRunState } from "../../context/RunStateContext";
import { DetectionDonutChart } from "./DetectionDonutChart";

const RATE_KEYS = [
  "detection_rate",
  "refusal_rate",
  "false_negative_rate",
];

function formatLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatSummaryValue(key: string, value: number | string): string {
  const n = typeof value === "number" ? value : Number(value);
  if (RATE_KEYS.includes(key) && !Number.isNaN(n)) {
    return `${Number(n).toFixed(2)}%`;
  }
  if (key === "average_confidence" && !Number.isNaN(n)) {
    return Number(n).toFixed(3);
  }
  return String(value);
}

export function EvaluationSummaryCard() {
  const { state } = useRunState();
  const data = state.evaluationData;
  const summary = data?.metrics?.summary;

  const hasSummary = summary && Object.keys(summary).length > 0;
  const skipKeys = ["timestamp"];
  const summaryEntries = hasSummary
    ? Object.entries(summary).filter(([k]) => !skipKeys.includes(k))
    : [];

  const detected = hasSummary ? Number(summary.detected ?? 0) : 0;
  const notDetected = hasSummary ? Number(summary.not_detected ?? 0) : 0;
  const refused = hasSummary ? Number(summary.refused ?? 0) : 0;
  const hasDonutData = detected + notDetected + refused > 0;

  if (!hasSummary && !hasDonutData) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-[var(--muted)]" />
            <CardTitle className="text-base">Evaluation Overview</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-[var(--muted)]">No evaluation yet.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-[var(--muted)]" />
          <CardTitle className="text-base">Evaluation Overview</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-[1.4fr,auto] gap-8 items-start">
          <div className="flex flex-col gap-y-4 text-sm min-w-0">
            {summaryEntries.map(([key, value]) => (
              <div
                key={key}
                className="flex justify-between items-center gap-4 min-w-0"
              >
                <span className="text-[var(--muted)] truncate min-w-0">
                  {formatLabel(key)}
                </span>
                <span className="tabular-nums shrink-0">
                  {formatSummaryValue(key, value)}
                </span>
              </div>
            ))}
          </div>
          {hasDonutData && (
            <div className="flex justify-end shrink-0">
              <DetectionDonutChart
                detected={detected}
                notDetected={notDetected}
                refused={refused}
              />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
