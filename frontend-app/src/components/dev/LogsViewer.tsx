import { useState, useMemo } from "react";
import { ScrollArea } from "../ui/scroll-area";
import { Button } from "../ui/button";
import type { RunState } from "../../lib/types";

interface LogsViewerProps {
  logs: RunState["logs"];
  onCopy: () => void;
}

const LEVELS = ["info", "warn", "error"] as const;

export function LogsViewer({ logs, onCopy }: LogsViewerProps) {
  const [levelFilter, setLevelFilter] = useState<string>("all");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    return logs.filter((entry) => {
      if (levelFilter !== "all" && entry.level !== levelFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        const match =
          entry.msg.toLowerCase().includes(q) ||
          (entry.meta != null && JSON.stringify(entry.meta).toLowerCase().includes(q));
        if (!match) return false;
      }
      return true;
    });
  }, [logs, levelFilter, search]);

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
          className="rounded border border-[var(--card-border)] bg-[var(--bg-2)] px-2 py-1 text-sm text-[var(--text)]"
          aria-label="Filter by level"
        >
          <option value="all">All levels</option>
          {LEVELS.map((l) => (
            <option key={l} value={l}>
              {l.toUpperCase()}
            </option>
          ))}
        </select>
        <input
          type="search"
          placeholder="Search logs..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 min-w-[120px] rounded border border-[var(--card-border)] bg-[var(--bg-2)] px-2 py-1 text-sm text-[var(--text)] placeholder:text-[var(--muted)]"
          aria-label="Search logs"
        />
        <Button variant="outline" size="sm" onClick={onCopy}>
          Copy logs
        </Button>
      </div>
      <ScrollArea className="h-[50vh] rounded-md border border-[var(--card-border)] p-2 font-mono text-xs">
        {filtered.length === 0 ? (
          <p className="text-[var(--muted)]">No matching logs.</p>
        ) : (
          filtered.map((entry, i) => (
            <div
              key={i}
              className={`py-0.5 ${
                entry.level === "error"
                  ? "text-[var(--danger)]"
                  : entry.level === "warn"
                  ? "text-[var(--warning)]"
                  : "text-[var(--muted)]"
              }`}
            >
              [{entry.ts}] {entry.level.toUpperCase()} {entry.msg}
              {entry.meta != null && (
                <pre className="mt-0.5 overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(entry.meta, null, 2)}
                </pre>
              )}
            </div>
          ))
        )}
      </ScrollArea>
    </div>
  );
}
