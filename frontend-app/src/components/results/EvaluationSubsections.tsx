import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { useRunState } from "../../context/RunStateContext";
import { ParsingMethodCard } from "./ParsingMethodCard";
import { QuestionTypeTile } from "./QuestionTypeTile";

export function EvaluationSubsections() {
  const { state } = useRunState();
  const byParsing = state.evaluationData?.metrics?.by_parsing_method;
  const byQuestionType = state.evaluationData?.metrics?.by_question_type;

  const hasParsing =
    byParsing && typeof byParsing === "object" && Object.keys(byParsing).length > 0;
  const hasQuestionType =
    byQuestionType &&
    typeof byQuestionType === "object" &&
    Object.keys(byQuestionType).length > 0;

  if (!hasParsing && !hasQuestionType) return null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {hasParsing && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold uppercase tracking-wider text-[var(--muted)]">
              By Parsing Method
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(byParsing).map(([method, metrics]) =>
                typeof metrics === "object" && metrics !== null ? (
                  <ParsingMethodCard
                    key={method}
                    method={method}
                    metrics={metrics as Record<string, number | string>}
                  />
                ) : null
              )}
            </div>
          </CardContent>
        </Card>
      )}
      {hasQuestionType && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold uppercase tracking-wider text-[var(--muted)]">
              By Question Type
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(byQuestionType).map(([qType, metrics]) =>
                typeof metrics === "object" && metrics !== null ? (
                  <QuestionTypeTile
                    key={qType}
                    questionType={qType}
                    metrics={metrics as Record<string, number | string>}
                  />
                ) : null
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
