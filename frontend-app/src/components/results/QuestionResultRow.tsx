import { Badge } from "../ui/badge";
import { Check, X, AlertCircle } from "lucide-react";

interface SampleResult {
  question_number?: number;
  question_type?: string;
  detected?: boolean;
  refused?: boolean;
  match_confidence?: number;
  reason?: string;
}

interface QuestionResultRowProps {
  result: SampleResult;
  index: number;
}

export function QuestionResultRow({ result, index }: QuestionResultRowProps) {
  const statusIcon = result.refused ? (
    <AlertCircle className="h-4 w-4 text-[var(--warning)] shrink-0 mt-0.5" />
  ) : result.detected ? (
    <Check className="h-4 w-4 text-[var(--success)] shrink-0 mt-0.5" />
  ) : (
    <X className="h-4 w-4 text-[var(--muted)] shrink-0 mt-0.5" />
  );

  return (
    <li className="flex items-start gap-2 py-2 px-3 rounded-lg border border-[var(--card-border)] bg-[var(--card)]/30 hover:bg-[var(--card)]/50 text-sm">
      <span>{statusIcon}</span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium">
            Question {result.question_number ?? index + 1}
          </span>
          {result.question_type && (
            <Badge variant="outline" className="text-xs">
              {result.question_type}
            </Badge>
          )}
          {result.match_confidence != null && (
            <span className="text-xs text-[var(--muted)]">
              Confidence: {Number(result.match_confidence).toFixed(2)}
            </span>
          )}
        </div>
        {result.reason && (
          <p className="text-xs text-[var(--muted)] mt-0.5 line-clamp-1">
            {result.reason}
          </p>
        )}
      </div>
    </li>
  );
}
