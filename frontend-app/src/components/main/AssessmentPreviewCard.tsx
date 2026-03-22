import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { useRunState } from "../../context/RunStateContext";

export function AssessmentPreviewCard() {
  const { files } = useRunState();
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!files.pdf) {
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
        setObjectUrl(null);
      }
      return;
    }
    const url = URL.createObjectURL(files.pdf);
    setObjectUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [files.pdf]);

  if (!files.pdf) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Assessment Preview</CardTitle>
        <p className="text-sm text-[var(--muted)] truncate">{files.pdf.name}</p>
      </CardHeader>
      <CardContent>
        <div className="rounded-lg border border-[var(--card-border)] overflow-hidden bg-[var(--bg-2)]">
          <iframe
            src={objectUrl ?? undefined}
            title="Assessment PDF preview"
            className="w-full h-[360px]"
          />
        </div>
      </CardContent>
    </Card>
  );
}
