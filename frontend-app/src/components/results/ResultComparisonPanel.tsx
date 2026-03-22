import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { FileText, ExternalLink, Download, Maximize2 } from "lucide-react";
import { useRunState } from "../../context/RunStateContext";
import { getArtifactUrl } from "../../lib/api";

const PREVIEW_HEIGHT = "320px";

function downloadBlobUrl(url: string, filename: string) {
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.rel = "noopener";
  a.click();
}

export function ResultComparisonPanel() {
  const { state, files } = useRunState();
  const [originalUrl, setOriginalUrl] = useState<string | null>(null);
  const [expandOriginal, setExpandOriginal] = useState(false);
  const [expandShielded, setExpandShielded] = useState(false);

  const pdfArtifacts = state.artifacts.filter((a) => a.type === "pdf");
  const firstPdf = pdfArtifacts[0];
  const shieldedUrl =
    state.runId && firstPdf ? getArtifactUrl(state.runId, firstPdf.name) : null;

  useEffect(() => {
    if (!files.pdf) {
      if (originalUrl) {
        URL.revokeObjectURL(originalUrl);
        setOriginalUrl(null);
      }
      return;
    }
    const url = URL.createObjectURL(files.pdf);
    setOriginalUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [files.pdf]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <CardTitle className="text-base">Original Assessment</CardTitle>
            <Badge variant="outline" className="text-xs font-normal">
              Original
            </Badge>
          </div>
          {files.pdf && (
            <p className="text-sm text-[var(--muted)] truncate mt-0.5">
              {files.pdf.name}
            </p>
          )}
        </CardHeader>
        <CardContent className="space-y-3">
          {files.pdf && originalUrl ? (
            <>
              <div className="rounded-lg border border-[var(--card-border)] overflow-hidden bg-[var(--bg-2)]">
                <iframe
                  src={originalUrl}
                  title="Original assessment preview"
                  className="w-full"
                  style={{ height: PREVIEW_HEIGHT }}
                />
              </div>
              <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-[var(--card-border)]">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 text-xs"
                  onClick={() => window.open(originalUrl, "_blank")}
                >
                  <ExternalLink className="h-3.5 w-3.5 mr-1.5" />
                  Open
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 text-xs"
                  onClick={() =>
                    downloadBlobUrl(originalUrl, files.pdf?.name ?? "original.pdf")
                  }
                >
                  <Download className="h-3.5 w-3.5 mr-1.5" />
                  Download
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 text-xs"
                  onClick={() => setExpandOriginal(true)}
                >
                  <Maximize2 className="h-3.5 w-3.5 mr-1.5" />
                  Expand
                </Button>
              </div>
              {expandOriginal && (
                <div
                  className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
                  role="dialog"
                  aria-modal="true"
                  aria-label="Expand original preview"
                  onClick={() => setExpandOriginal(false)}
                >
                  <div
                    className="bg-[var(--card)] rounded-lg border border-[var(--card-border)] overflow-hidden max-w-4xl w-full max-h-[90vh] flex flex-col"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="flex justify-end p-2 border-b border-[var(--card-border)]">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setExpandOriginal(false)}
                      >
                        Close
                      </Button>
                    </div>
                    <iframe
                      src={originalUrl}
                      title="Original assessment (expanded)"
                      className="w-full flex-1 min-h-[70vh]"
                    />
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-[var(--muted)] py-8 text-center">
              No original assessment in this run.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <CardTitle className="text-base">Shielded Assessment</CardTitle>
            <Badge variant="outline" className="text-xs font-normal">
              Shielded
            </Badge>
          </div>
          <p className="text-sm text-[var(--muted)] truncate mt-0.5">
            {firstPdf ? firstPdf.name : "Generated shielded variants."}
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          {pdfArtifacts.length === 0 ? (
            <p className="text-sm text-[var(--muted)] py-8 text-center">
              Run the pipeline to generate shielded PDFs.
            </p>
          ) : (
            <>
              {shieldedUrl && (
                <>
                  <div className="rounded-lg border border-[var(--card-border)] overflow-hidden bg-[var(--bg-2)]">
                    <iframe
                      src={shieldedUrl}
                      title="Shielded assessment preview"
                      className="w-full"
                      style={{ height: PREVIEW_HEIGHT }}
                    />
                  </div>
                  <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-[var(--card-border)]">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 text-xs"
                      onClick={() => window.open(shieldedUrl, "_blank")}
                    >
                      <ExternalLink className="h-3.5 w-3.5 mr-1.5" />
                      Open
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 text-xs"
                      onClick={() => {
                        const a = document.createElement("a");
                        a.href = shieldedUrl;
                        a.download = firstPdf?.name ?? "shielded.pdf";
                        a.rel = "noopener";
                        a.click();
                      }}
                    >
                      <Download className="h-3.5 w-3.5 mr-1.5" />
                      Download
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 text-xs"
                      onClick={() => setExpandShielded(true)}
                    >
                      <Maximize2 className="h-3.5 w-3.5 mr-1.5" />
                      Expand
                    </Button>
                  </div>
                  {expandShielded && (
                    <div
                      className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
                      role="dialog"
                      aria-modal="true"
                      aria-label="Expand shielded preview"
                      onClick={() => setExpandShielded(false)}
                    >
                      <div
                        className="bg-[var(--card)] rounded-lg border border-[var(--card-border)] overflow-hidden max-w-4xl w-full max-h-[90vh] flex flex-col"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div className="flex justify-end p-2 border-b border-[var(--card-border)]">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setExpandShielded(false)}
                          >
                            Close
                          </Button>
                        </div>
                        <iframe
                          src={shieldedUrl}
                          title="Shielded assessment (expanded)"
                          className="w-full flex-1 min-h-[70vh]"
                        />
                      </div>
                    </div>
                  )}
                </>
              )}
              {pdfArtifacts.length > 1 && (
                <ul className="space-y-2 pt-2 border-t border-[var(--card-border)]">
                  {pdfArtifacts.map((a, i) => (
                    <li
                      key={`${a.stageId}-${a.name}-${i}`}
                      className="flex items-center gap-2 py-2 px-3 rounded-lg border border-[var(--card-border)] bg-[var(--bg-2)]/50"
                    >
                      <FileText className="h-4 w-4 shrink-0 text-[var(--muted)]" />
                      <span className="flex-1 truncate text-sm">{a.name}</span>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
