interface DetectionDonutChartProps {
  detected: number;
  notDetected: number;
  refused: number;
  size?: number;
}

const DEFAULT_SIZE = 120;
const STROKE = 12;
const RADIUS = (DEFAULT_SIZE - STROKE) / 2;

export function DetectionDonutChart({
  detected,
  notDetected,
  refused,
  size = DEFAULT_SIZE,
}: DetectionDonutChartProps) {
  const total = detected + notDetected + refused;
  if (total === 0) return null;

  const scale = size / DEFAULT_SIZE;
  const r = RADIUS * scale;
  const circumference = 2 * Math.PI * r;
  const stroke = STROKE * scale;
  const cx = (size / 2);
  const cy = (size / 2);

  const toOffset = (ratio: number) => Math.max(0, Math.min(1, ratio)) * circumference;
  const detRatio = detected / total;
  const notDetRatio = notDetected / total;
  const refRatio = refused / total;

  const detLen = toOffset(detRatio);
  const notDetLen = toOffset(notDetRatio);
  const refLen = toOffset(refRatio);

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={size} height={size} className="shrink-0" aria-hidden>
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="var(--card-border)"
          strokeWidth={stroke}
        />
        {/* Detected - green */}
        {detLen > 0 && (
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke="var(--success)"
            strokeWidth={stroke}
            strokeDasharray={`${detLen} ${circumference - detLen}`}
            strokeDashoffset={0}
            transform={`rotate(-90 ${cx} ${cy})`}
          />
        )}
        {/* Not detected - muted */}
        {notDetLen > 0 && (
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke="var(--muted)"
            strokeWidth={stroke}
            strokeDasharray={`${notDetLen} ${circumference - notDetLen}`}
            strokeDashoffset={-detLen}
            transform={`rotate(-90 ${cx} ${cy})`}
          />
        )}
        {/* Refused - warning */}
        {refLen > 0 && (
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke="var(--warning)"
            strokeWidth={stroke}
            strokeDasharray={`${refLen} ${circumference - refLen}`}
            strokeDashoffset={-(detLen + notDetLen)}
            transform={`rotate(-90 ${cx} ${cy})`}
          />
        )}
      </svg>
      <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 text-xs max-w-[200px]">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-[var(--success)]" aria-hidden />
          Detected {detected}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-[var(--muted)]" aria-hidden />
          Not detected {notDetected}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-[var(--warning)]" aria-hidden />
          Refused {refused}
        </span>
      </div>
    </div>
  );
}
