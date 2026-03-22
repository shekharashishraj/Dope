import { FileText, Copy, Download, ExternalLink } from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { getArtifactUrl } from "../../lib/api";
import type { RunState } from "../../lib/types";

interface ArtifactRowProps {
  artifact: RunState["artifacts"][number];
  runId: string | undefined;
}

export function ArtifactRow({ artifact, runId }: ArtifactRowProps) {
  const copyPath = () => {
    const path = artifact.url ?? artifact.name;
    navigator.clipboard.writeText(path);
  };

  const downloadUrl =
    runId != null ? getArtifactUrl(runId, artifact.name) : null;

  return (
    <li className="flex items-center gap-2 py-2 px-3 rounded-lg border border-[var(--card-border)]/50 hover:bg-[var(--card)]/50 group">
      <FileText className="h-4 w-4 shrink-0 text-[var(--muted)]" />
      <span className="flex-1 truncate text-sm min-w-0">{artifact.name}</span>
      <Badge variant="outline" className="text-xs uppercase shrink-0">
        {artifact.type}
      </Badge>
      <div className="flex items-center gap-1 shrink-0">
        {artifact.type === "pdf" && downloadUrl && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs"
            title="Open in new tab"
            onClick={() => window.open(downloadUrl, "_blank")}
          >
            <ExternalLink className="h-3.5 w-3.5 mr-1" />
            Open
          </Button>
        )}
        {downloadUrl && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs"
            title="Download"
            asChild
          >
            <a href={downloadUrl} download={artifact.name} rel="noopener">
              <Download className="h-3.5 w-3.5 mr-1" />
              Download
            </a>
          </Button>
        )}
        <Button
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
          title="Copy path"
          onClick={copyPath}
        >
          <Copy className="h-3.5 w-3.5" />
        </Button>
      </div>
    </li>
  );
}
