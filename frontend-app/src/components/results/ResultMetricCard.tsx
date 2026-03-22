interface ResultMetricCardProps {
  label: string;
  value: string | number;
}

export function ResultMetricCard({ label, value }: ResultMetricCardProps) {
  return (
    <div className="rounded-lg border border-[var(--card-border)] bg-[var(--card)]/50 px-4 py-3 min-w-0">
      <p className="text-xs font-medium text-[var(--muted)] uppercase tracking-wider truncate">
        {label}
      </p>
      <p className="text-lg font-semibold tabular-nums mt-0.5 truncate" title={String(value)}>
        {value}
      </p>
    </div>
  );
}
