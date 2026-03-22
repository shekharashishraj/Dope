import { Card, CardContent } from "../ui/card";

const RATE_KEYS = ["detection_rate", "refusal_rate", "false_negative_rate"];

function formatLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatValue(key: string, value: number | string): string {
  if (RATE_KEYS.includes(key) && typeof value === "number") {
    return `${Number(value).toFixed(2)}%`;
  }
  if (key === "average_confidence") {
    return Number(value).toFixed(3);
  }
  return String(value);
}

interface ParsingMethodCardProps {
  method: string;
  metrics: Record<string, number | string>;
}

export function ParsingMethodCard({ method, metrics }: ParsingMethodCardProps) {
  const entries = Object.entries(metrics).filter(
    ([k]) => k !== "timestamp"
  );

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        <div className="font-medium capitalize mb-2 text-base">
          {method.replace(/_/g, " ")}
        </div>
        <div className="grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
          {entries.map(([k, v]) => (
            <div key={k} className="flex justify-between gap-2">
              <span className="text-[var(--muted)] truncate">
                {formatLabel(k)}
              </span>
              <span className="tabular-nums shrink-0">
                {formatValue(k, v)}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
