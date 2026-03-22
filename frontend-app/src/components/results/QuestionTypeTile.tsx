const RATE_KEYS = ["detection_rate", "refusal_rate"];

function formatLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatValue(key: string, value: number | string): string {
  if (RATE_KEYS.includes(key) && typeof value === "number") {
    return `${Number(value).toFixed(2)}%`;
  }
  return String(value);
}

interface QuestionTypeTileProps {
  questionType: string;
  metrics: Record<string, number | string>;
}

export function QuestionTypeTile({
  questionType,
  metrics,
}: QuestionTypeTileProps) {
  const entries = Object.entries(metrics);

  return (
    <div className="rounded-lg border border-[var(--card-border)] bg-[var(--card)]/50 px-4 py-3 min-w-[200px]">
      <div className="font-medium mb-1.5 text-base">{questionType}</div>
      <div className="space-y-1 text-sm">
        {entries.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-2 text-[var(--muted)]">
            <span>{formatLabel(k)}</span>
            <span className="tabular-nums text-[var(--text)]">
              {formatValue(k, v)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
