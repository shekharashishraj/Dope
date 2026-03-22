import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { ScrollArea } from "../ui/scroll-area";
import { useRunState } from "../../context/RunStateContext";
import { Check, X, AlertCircle } from "lucide-react";

function formatLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function EvaluationHighlightsCard() {
  const { state } = useRunState();
  const metrics = state.evaluationMetrics;
  const data = state.evaluationData;

  const summary = data?.metrics?.summary ?? metrics;
  const byParsing = data?.metrics?.by_parsing_method;
  const byQuestionType = data?.metrics?.by_question_type;
  const sampleResults = data?.sample_results ?? [];

  const hasAny = Boolean(
    (summary && Object.keys(summary).length > 0) ||
    (byParsing && Object.keys(byParsing).length > 0) ||
    (byQuestionType && Object.keys(byQuestionType).length > 0) ||
    sampleResults.length > 0
  );

  if (!hasAny) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Protection Evaluation</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-[var(--muted)]">No evaluation yet.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Protection Evaluation</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {summary && Object.keys(summary).length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider mb-2">
              Summary
            </h4>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
              {Object.entries(summary)
                .filter(([k]) => !["timestamp"].includes(k))
                .map(([key, value]) => (
                  <div key={key} className="flex justify-between gap-2">
                    <span className="text-[var(--muted)]">{formatLabel(key)}</span>
                    <span className="tabular-nums">{String(value)}</span>
                  </div>
                ))}
            </div>
          </div>
        )}

        {byParsing && Object.keys(byParsing).length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider mb-2">
              By parsing method
            </h4>
            <div className="space-y-2">
              {Object.entries(byParsing).map(([method, methodMetrics]) => (
                <div
                  key={method}
                  className="rounded-lg border border-[var(--card-border)] bg-[var(--bg-2)]/50 p-2 text-sm"
                >
                  <div className="font-medium capitalize mb-1">{method.replace(/_/g, " ")}</div>
                  <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 text-[var(--muted)]">
                    {typeof methodMetrics === "object" &&
                      methodMetrics !== null &&
                      Object.entries(methodMetrics as Record<string, number | string>).map(
                        ([k, v]) => (
                          <div key={k} className="flex justify-between">
                            <span>{formatLabel(k)}</span>
                            <span className="tabular-nums text-[var(--text)]">{String(v)}</span>
                          </div>
                        )
                      )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {byQuestionType && Object.keys(byQuestionType).length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider mb-2">
              By question type
            </h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(byQuestionType).map(([qType, typeMetrics]) => (
                <div
                  key={qType}
                  className="rounded-lg border border-[var(--card-border)] bg-[var(--bg-2)]/50 px-3 py-2 text-sm min-w-[140px]"
                >
                  <div className="font-medium mb-1">{qType}</div>
                  {typeof typeMetrics === "object" &&
                    typeMetrics !== null &&
                    Object.entries(typeMetrics as Record<string, number | string>).map(
                      ([k, v]) => (
                        <div key={k} className="flex justify-between text-xs text-[var(--muted)]">
                          <span>{formatLabel(k)}</span>
                          <span className="tabular-nums text-[var(--text)]">{String(v)}</span>
                        </div>
                      )
                    )}
                </div>
              ))}
            </div>
          </div>
        )}

        {sampleResults.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider mb-2">
              Sample detection results
            </h4>
            <ScrollArea className="h-[220px] rounded-md border border-[var(--card-border)]">
              <ul className="p-2 space-y-1.5 text-sm">
                {sampleResults.map((r, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 py-1.5 px-2 rounded hover:bg-[var(--card)]/50"
                  >
                    <span className="shrink-0 mt-0.5">
                      {r.refused ? (
                        <AlertCircle className="h-4 w-4 text-[var(--warning)]" />
                      ) : r.detected ? (
                        <Check className="h-4 w-4 text-[var(--success)]" />
                      ) : (
                        <X className="h-4 w-4 text-[var(--muted)]" />
                      )}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium">
                          Question {r.question_number ?? i + 1}
                        </span>
                        {r.question_type && (
                          <Badge variant="outline" className="text-xs">
                            {r.question_type}
                          </Badge>
                        )}
                        {r.match_confidence != null && (
                          <span className="text-xs text-[var(--muted)]">
                            Confidence: {Number(r.match_confidence).toFixed(2)}
                          </span>
                        )}
                      </div>
                      {r.reason && (
                        <p className="text-xs text-[var(--muted)] mt-0.5 line-clamp-2">
                          {r.reason}
                        </p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </ScrollArea>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
