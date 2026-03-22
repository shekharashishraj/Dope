import { useRef, useState } from "react";
import { Card, CardContent } from "../ui/card";
import { Upload } from "lucide-react";
import { cn } from "../../lib/utils";

interface UploadCardProps {
  label: string;
  required: boolean;
  accept: string;
  file: File | null;
  onFileChange: (file: File | null) => void;
  helperText?: string;
}

export function UploadCard({
  label,
  required,
  accept,
  file,
  onFileChange,
  helperText,
}: UploadCardProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) onFileChange(f);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  return (
    <Card
      className={cn(
        "cursor-pointer transition-colors hover:border-[var(--accent)]/50 border-dashed",
        file && "border-[var(--accent)]/30",
        dragOver && "border-[var(--accent)] bg-[var(--accent)]/5"
      )}
      onClick={() => inputRef.current?.click()}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      <CardContent className="pt-4">
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            onFileChange(f ?? null);
          }}
        />
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--bg-2)]">
            <Upload className="h-5 w-5 text-[var(--muted)]" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-medium">
              {label} {required && <span className="text-[var(--danger)]">*</span>}
            </div>
            <div className="text-sm text-[var(--muted)] truncate">
              {file ? `${file.name} (${Math.round(file.size / 1024)} KB)` : "No file selected"}
            </div>
            {helperText && (
              <div className="text-xs text-[var(--muted)] mt-0.5">{helperText}</div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
