import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../ui/tooltip";
import { UploadCard } from "../setup/UploadCard";
import { AttackMethodPicker } from "../setup/AttackMethodPicker";
import { useRunState } from "../../context/RunStateContext";
import { usePipelineRunner } from "../../hooks/usePipelineRunner";
import { AssessmentPreviewCard } from "./AssessmentPreviewCard";

function ActionButtons({
  canRun,
  hasPdf,
  hasMethod,
  onRun,
  onReset,
}: {
  canRun: boolean;
  hasPdf: boolean;
  hasMethod: boolean;
  onRun: () => void;
  onReset: () => void;
}) {
  return (
    <div className="flex justify-center items-center gap-3 mt-4">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              disabled={!canRun}
              onClick={onRun}
              className="rounded-lg"
            >
              Begin Shielding
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            {!hasPdf
              ? "Upload an assessment to continue."
              : !hasMethod
                ? "Choose at least one shielding method to continue."
                : "Run the pipeline."}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
      <Button variant="ghost" onClick={onReset} className="rounded-lg">
        Reset
      </Button>
    </div>
  );
}

export function MainTabContent() {
  const { files, setPdfFile, setAnswerFile, state, reset } = useRunState();
  const { runPipeline } = usePipelineRunner();

  const hasPdf = !!files.pdf;
  const hasMethod = state.config.attacks.length >= 1;
  const canRun = hasPdf && hasMethod && state.status !== "running";

  const actionButtons = (
    <ActionButtons
      canRun={canRun}
      hasPdf={hasPdf}
      hasMethod={hasMethod}
      onRun={runPipeline}
      onReset={reset}
    />
  );

  return (
    <div className="flex flex-col gap-6">
      <section>
        <h2 className="sr-only">Upload</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <UploadCard
            label="Upload Assessment"
            required
            accept="application/pdf"
            file={files.pdf}
            onFileChange={setPdfFile}
          />
          <UploadCard
            label="Upload Answer Key (Optional)"
            required={false}
            accept=".pdf,.txt,.csv"
            file={files.answer}
            onFileChange={setAnswerFile}
            helperText="Improves evaluation quality / scoring"
          />
        </div>
        {!hasPdf && actionButtons}
      </section>

      <AssessmentPreviewCard />

      {files.pdf && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Choose Shielding Method</CardTitle>
            </CardHeader>
            <CardContent>
              <AttackMethodPicker />
            </CardContent>
          </Card>

          {actionButtons}
        </>
      )}

      {!files.pdf && (
        <p className="text-sm text-[var(--muted)]">
          Upload an assessment PDF to begin shielding and evaluation.
        </p>
      )}
    </div>
  );
}
