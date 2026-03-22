import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Copy, FileText } from "lucide-react";
import { useRunState } from "../../context/RunStateContext";
import { useTab } from "../../context/TabContext";

export function PreviewPanel() {
  const { state, files } = useRunState();
  const { setActiveTab } = useTab();
  const [originalObjectUrl, setOriginalObjectUrl] = useState<string | null>(null);

  const pdfArtifacts = state.artifacts.filter((a) => a.type === "pdf");

  useEffect(() => {
    if (!files.pdf) {
      if (originalObjectUrl) {
        URL.revokeObjectURL(originalObjectUrl);
        setOriginalObjectUrl(null);
      }
      return;
    }
    const url = URL.createObjectURL(files.pdf);
    setOriginalObjectUrl(url);
    return () => {
      URL.revokeObjectURL(url);
    };
  }, [files.pdf]);

  const copyPath = (path: string) => {
    navigator.clipboard.writeText(path);
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Original Assessment</CardTitle>
        </CardHeader>
        <CardContent>
          {files.pdf ? (
            <div className="rounded-lg border border-[var(--card-border)] overflow-hidden bg-[var(--bg-2)]">
              <iframe
                src={originalObjectUrl ?? undefined}
                title="Original PDF preview"
                className="w-full h-[360px]"
              />
              <div className="px-3 py-2 text-xs text-[var(--muted)] truncate border-t border-[var(--card-border)]">
                {files.pdf.name}
              </div>
            </div>
          ) : (
            <p className="text-sm text-[var(--muted)] py-6 text-center">
              Upload a PDF and run the pipeline to see the original and shielded variants here.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Generated Shielded Variants</CardTitle>
          <p className="text-xs text-[var(--muted)]">Generated PDFs from the pipeline.</p>
        </CardHeader>
        <CardContent>
          {pdfArtifacts.length === 0 ? (
            <p className="text-sm text-[var(--muted)] py-6 text-center">
              Run the pipeline to see shielded variant PDFs here.
            </p>
          ) : (
            <ul className="space-y-2">
              {pdfArtifacts.map((artifact, i) => (
                <li
                  key={`${artifact.stageId}-${artifact.name}-${i}`}
                  className="flex items-center gap-2 py-2 px-3 rounded-lg border border-[var(--card-border)] bg-[var(--bg-2)]/50"
                >
                  <FileText className="h-4 w-4 shrink-0 text-[var(--muted)]" />
                  <span className="flex-1 truncate text-sm">{artifact.name}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="shrink-0"
                    onClick={() => copyPath(artifact.url ?? artifact.name)}
                    title="Copy path"
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </li>
              ))}
            </ul>
          )}
          {pdfArtifacts.length > 0 && (
            <div className="mt-3 pt-3 border-t border-[var(--card-border)]">
              <button
                type="button"
                onClick={() => setActiveTab("results")}
                className="text-sm text-[var(--accent)] hover:underline"
              >
                {state.artifacts.length} artifacts — View in Results
              </button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
