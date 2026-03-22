import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { ShieldCheck } from "lucide-react";
import { useRunState } from "../../context/RunStateContext";

export function ProtectionOverviewCard() {
  const { state } = useRunState();

  const extractStep = state.steps.find((s) => s.id === "extract");
  const evalStep = state.steps.find((s) => s.id === "eval");
  const questionsValue =
    extractStep?.outputs?.find((o) => o.label === "Questions")?.value ?? "";
  const questionCount = questionsValue !== "--" ? questionsValue : "0";
  const method = state.config.attacks.length > 0 ? state.config.attacks.join(", ") : "none";
  const hasShieldedPdf = state.artifacts.some((a) => a.type === "pdf");
  const evaluationComplete =
    evalStep?.status === "done" && state.evaluationData != null;

  const parts: string[] = [];
  parts.push(
    method !== "none"
      ? `${method} shielding was applied`
      : "No shielding method was applied"
  );
  if (questionCount) {
    parts.push(`to ${questionCount} extracted question${questionCount === "1" ? "" : "s"}`);
  }
  parts.push(".");
  if (hasShieldedPdf) {
    parts.push(" The protected PDF was generated.");
  } else if (state.status === "done" || state.status === "failed") {
    parts.push(" The protected PDF was not generated.");
  }
  if (evaluationComplete) {
    parts.push(" Evaluation completed successfully.");
  } else if (evalStep?.status === "failed") {
    parts.push(" Evaluation did not complete.");
  }

  const summary = parts.join(" ");

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-[var(--muted)]" />
          <CardTitle className="text-base">Protection Overview</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-[var(--muted)] leading-relaxed">{summary}</p>
      </CardContent>
    </Card>
  );
}
