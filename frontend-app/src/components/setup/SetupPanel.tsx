import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { UploadCard } from "./UploadCard";
import { AttackMethodPicker } from "./AttackMethodPicker";
import { Button } from "../ui/button";
import { useRunState } from "../../context/RunStateContext";
import { usePipelineRunner } from "../../hooks/usePipelineRunner";

export function SetupPanel() {
  const { state, files, setPdfFile, setAnswerFile, reset } = useRunState();
  const { runPipeline } = usePipelineRunner();
  const hasPdf = !!files.pdf;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Setup</CardTitle>
          <CardDescription>Upload documents and choose shielding methods.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <UploadCard
            label="PDF Document"
            required
            accept="application/pdf"
            file={files.pdf}
            onFileChange={setPdfFile}
          />
          <UploadCard
            label="Answer Key (Optional)"
            required={false}
            accept=".pdf,.txt,.csv"
            file={files.answer}
            onFileChange={setAnswerFile}
            helperText="Improves evaluation scoring"
          />

          <AttackMethodPicker />

          <div className="flex flex-col gap-2 pt-2">
            {!hasPdf && (
              <p className="text-sm text-[var(--muted)]">Upload a PDF to continue.</p>
            )}
            <div className="flex gap-2">
              <Button
                disabled={!hasPdf || state.config.attacks.length === 0 || state.status === "running"}
                onClick={() => runPipeline()}
              >
                Run Shielding Pipeline
              </Button>
              <Button variant="ghost" onClick={reset}>
                Reset
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
